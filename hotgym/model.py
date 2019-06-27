from htm.algorithms import SpatialPooler
from htm.algorithms import TemporalMemory
from htm.bindings.sdr import SDR, Metrics
from htm.encoders.rdse import RDSE, RDSE_Parameters
from htm.encoders.date import DateEncoder
from htm.algorithms.anomaly_likelihood import AnomalyLikelihood
from htm.bindings.algorithms import Predictor
import numpy as np

class Model:
    def __init__(self, parameters):
        self.parameters = parameters
        self.count = 0

    def createEncoder(self):
        self.timeOfDayEncoder = DateEncoder(self.parameters["time"]["timeOfDay"])
        self.weekendEncoder   = DateEncoder(self.parameters["time"]["weekend"])

        rdseParams = RDSE_Parameters()
        rdseParams.size       = self.parameters["enc"]["size"]
        rdseParams.sparsity   = self.parameters["enc"]["sparsity"]
        rdseParams.resolution = self.parameters["enc"]["resolution"]
        self.scalarEncoder = RDSE( rdseParams )
        self.encodingWidth = (self.timeOfDayEncoder.size
                         + self.weekendEncoder.size
                         + self.scalarEncoder.size)

    def createOther(self):
        self.anomaly_history = AnomalyLikelihood()
        self.predictor = Predictor( steps=[1, 5], alpha=self.parameters['sdrc_alpha'] )
        self.predictor_resolution = 1

    def create(self):
        self.createEncoder()

        spParams = self.parameters["sp"]
        self.sp = SpatialPooler(
            inputDimensions            = (self.encodingWidth,),
            columnDimensions           = (spParams["columnCount"],),
            potentialPct               = spParams["potentialPct"],
            potentialRadius            = encodingWidth,
            globalInhibition           = True,
            localAreaDensity           = -1,
            numActiveColumnsPerInhArea = spParams["numActiveColumnsPerInhArea"],
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
        if not isinstance(model.get('sp'), SpatialPooler):
            raise Exception('Load SpatialPooler failed')

        if not isinstance(model.get('tm'), TemporalMemory):
            raise Exception('Load TemporalMemory failed')

        self.sp = model['sp']
        self.tm = model['tm']
        self.count = model.get('count', 0)

        self.createOther()

    def run(self, dateString, consumption):
        # Now we call the encoders to create bit representations for each value.
        timeOfDayBits   = self.timeOfDayEncoder.encode(dateString)
        weekendBits     = self.weekendEncoder.encode(dateString)
        consumptionBits = self.scalarEncoder.encode(consumption)

        # Concatenate all these encodings into one large encoding for Spatial
        # Pooling.
        encoding = SDR( self.encodingWidth ).concatenate(
                                    [consumptionBits, timeOfDayBits, weekendBits])

        # Create an SDR to represent active columns, This will be populated by the
        # compute method below. It must have the same dimensions as the Spatial
        # Pooler.
        activeColumns = SDR( self.sp.getColumnDimensions() )

        # Execute Spatial Pooling algorithm over input space.
        self.sp.compute(encoding, True, activeColumns)

        # Execute Temporal Memory algorithm over active mini-columns.
        self.tm.compute(activeColumns, learn=True)

        # Predict what will happen, and then train the predictor based on what just happened.
        pdf = self.predictor.infer( self.count, self.tm.getActiveCells() )

        predict_value = 0
        if pdf[1]:
            predict_value = np.argmax(pdf[1]) * self.predictor_resolution

        self.predictor.learn( self.count, self.tm.getActiveCells(),
                                  int(consumption / self.predictor_resolution))

        self.count = self.count + 1


        anomalyLikelihood = self.anomaly_history.anomalyProbability( consumption, self.tm.anomaly )

        return {
            'perdict': predict_value,
            'anomaly': self.tm.anomaly,
            'anomalyProb': anomalyLikelihood
        }
