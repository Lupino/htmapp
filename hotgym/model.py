from htm.algorithms import SpatialPooler
from htm.algorithms import TemporalMemory
from htm.bindings.sdr import SDR, Metrics
from htm.encoders.rdse import RDSE, RDSE_Parameters
from htm.encoders.date import DateEncoder
from htm.algorithms.anomaly_likelihood import AnomalyLikelihood
from htm.bindings.algorithms import Predictor
import numpy as np
import math

class Model:
    def __init__(self, parameters):
        self.parameters = parameters
        self.count = 0

    def createEncoder(self):
        # Make the Encoders.  These will convert input data into binary representations.
        self.dateEncoder = DateEncoder(timeOfDay= self.parameters["enc"]["time"]["timeOfDay"],
                                  weekend  = self.parameters["enc"]["time"]["weekend"])

        scalarEncoderParams            = RDSE_Parameters()
        scalarEncoderParams.size       = self.parameters["enc"]["value"]["size"]
        scalarEncoderParams.sparsity   = self.parameters["enc"]["value"]["sparsity"]
        scalarEncoderParams.resolution = self.parameters["enc"]["value"]["resolution"]
        self.scalarEncoder = RDSE( scalarEncoderParams )
        self.encodingWidth = (self.dateEncoder.size + self.scalarEncoder.size)

    def createOther(self, record_length = 100):
        # setup likelihood, these settings are used in NAB
        anParams = self.parameters["anomaly"]["likelihood"]
        probationaryPeriod = int(math.floor(float(anParams["probationaryPct"])*record_length))
        learningPeriod     = int(math.floor(probationaryPeriod / 2.0))
        self.anomaly_history = AnomalyLikelihood(learningPeriod= learningPeriod,
                                            estimationSamples= probationaryPeriod - learningPeriod,
                                            reestimationPeriod= anParams["reestimationPeriod"])

        self.predictor = Predictor( steps=[1, 5], alpha=self.parameters["predictor"]['sdrc_alpha'] )
        self.predictor_resolution = 1

    def create(self):
        self.createEncoder()

        # Make the HTM.  SpatialPooler & TemporalMemory & associated tools.
        spParams = self.parameters["sp"]
        self.sp = SpatialPooler(
          inputDimensions            = (self.encodingWidth,),
          columnDimensions           = (spParams["columnCount"],),
          potentialPct               = spParams["potentialPct"],
          potentialRadius            = self.encodingWidth,
          globalInhibition           = True,
          localAreaDensity           = spParams["localAreaDensity"],
          synPermInactiveDec         = spParams["synPermInactiveDec"],
          synPermActiveInc           = spParams["synPermActiveInc"],
          synPermConnected           = spParams["synPermConnected"],
          boostStrength              = spParams["boostStrength"],
          wrapAround                 = True
        )

        tmParams = self.parameters["tm"]
        self.tm = TemporalMemory(
          columnDimensions          = (spParams["columnCount"],),
          cellsPerColumn            = tmParams["cellsPerColumn"],
          activationThreshold       = tmParams["activationThreshold"],
          initialPermanence         = tmParams["initialPerm"],
          connectedPermanence       = spParams["synPermConnected"],
          minThreshold              = tmParams["minThreshold"],
          maxNewSynapseCount        = tmParams["newSynapseCount"],
          permanenceIncrement       = tmParams["permanenceInc"],
          permanenceDecrement       = tmParams["permanenceDec"],
          predictedSegmentDecrement = 0.0,
          maxSegmentsPerCell        = tmParams["maxSegmentsPerCell"],
          maxSynapsesPerSegment     = tmParams["maxSynapsesPerSegment"]
        )

        self.createOther()

    def save(self, store):
        store.save('model', {'sp': self.sp, 'tm': self.tm, 'count': self.count})

    def load(self, store):
        self.createEncoder()
        model = store.load('model')
        if not model:
            raise Exception('Load model failed')
        if not isinstance(model.get('sp'), SpatialPooler):
            raise Exception('Load SpatialPooler failed')

        if not isinstance(model.get('tm'), TemporalMemory):
            raise Exception('Load TemporalMemory failed')

        self.sp = model['sp']
        self.tm = model['tm']
        self.count = model.get('count', 0)

        self.createOther()

    def run(self, dateString, consumption):

        # Call the encoders to create bit representations for each value.  These are SDR objects.
        dateBits        = self.dateEncoder.encode(dateString)
        consumptionBits = self.scalarEncoder.encode(consumption)

        # Concatenate all these encodings into one large encoding for Spatial Pooling.
        encoding = SDR( self.encodingWidth ).concatenate([consumptionBits, dateBits])

        # Create an SDR to represent active columns, This will be populated by the
        # compute method below. It must have the same dimensions as the Spatial Pooler.
        activeColumns = SDR( self.sp.getColumnDimensions() )

        # Execute Spatial Pooling algorithm over input space.
        self.sp.compute(encoding, True, activeColumns)

        # Execute Temporal Memory algorithm over active mini-columns.
        self.tm.compute(activeColumns, learn=True)

        # Predict what will happen, and then train the predictor based on what just happened.
        pdf = self.predictor.infer( self.tm.getActiveCells() )
        predictions = []
        for n in (1, 5):
          if pdf[n]:
            predictions.append( np.argmax( pdf[n] ) * self.predictor_resolution )
          else:
            predictions.append(float('nan'))

        anomalyLikelihood = self.anomaly_history.anomalyProbability( consumption, self.tm.anomaly )

        self.predictor.learn(self.count, self.tm.getActiveCells(), int(consumption / self.predictor_resolution))

        self.count = self.count + 1

        return {
            'predictions': predictions,
            'anomaly': self.tm.anomaly,
            'anomalyProb': anomalyLikelihood
        }
