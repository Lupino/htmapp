import numpy as np
from htm.bindings.sdr import SDR
from htm.encoders.rdse import RDSE, RDSE_Parameters
from htm.encoders.date import DateEncoder
from htm.bindings.algorithms import SpatialPooler
from htm.bindings.algorithms import TemporalMemory

from htm.bindings.algorithms import Predictor

from ..base_model import BaseModel


class Model(BaseModel):
    def __init__(self, parameters, *args, **kwargs):
        BaseModel.__init__(self, *args, **kwargs)

        self.parameters = parameters

    def create(self):
        parameters = self.parameters

        # Make the Encoders.
        # These will convert input data into binary representations.
        dateEncoder = DateEncoder(
            timeOfDay=parameters["enc"]["time"]["timeOfDay"],
            weekend=parameters["enc"]["time"]["weekend"])

        scalarEncoderParams = RDSE_Parameters()
        scalarEncoderParams.size = parameters["enc"]["value"]["size"]
        scalarEncoderParams.sparsity = parameters["enc"]["value"]["sparsity"]
        scalarEncoderParams.resolution = parameters["enc"]["value"][
            "resolution"]
        scalarEncoder = RDSE(scalarEncoderParams)
        encodingWidth = (dateEncoder.size + scalarEncoder.size)

        # Make the HTM.  SpatialPooler & TemporalMemory & associated tools.
        spParams = parameters["sp"]
        sp = SpatialPooler(inputDimensions=(encodingWidth, ),
                           columnDimensions=(spParams["columnCount"], ),
                           potentialPct=spParams["potentialPct"],
                           potentialRadius=encodingWidth,
                           globalInhibition=True,
                           localAreaDensity=spParams["localAreaDensity"],
                           synPermInactiveDec=spParams["synPermInactiveDec"],
                           synPermActiveInc=spParams["synPermActiveInc"],
                           synPermConnected=spParams["synPermConnected"],
                           boostStrength=spParams["boostStrength"],
                           wrapAround=True)

        tmParams = parameters["tm"]
        tm = TemporalMemory(
            columnDimensions=(spParams["columnCount"], ),
            cellsPerColumn=tmParams["cellsPerColumn"],
            activationThreshold=tmParams["activationThreshold"],
            initialPermanence=tmParams["initialPerm"],
            connectedPermanence=spParams["synPermConnected"],
            minThreshold=tmParams["minThreshold"],
            maxNewSynapseCount=tmParams["newSynapseCount"],
            permanenceIncrement=tmParams["permanenceInc"],
            permanenceDecrement=tmParams["permanenceDec"],
            predictedSegmentDecrement=0.0,
            maxSegmentsPerCell=tmParams["maxSegmentsPerCell"],
            maxSynapsesPerSegment=tmParams["maxSynapsesPerSegment"])

        # setup likelihood, these settings are used in NAB
        predictor = Predictor(steps=[1, 5],
                              alpha=parameters["predictor"]['sdrc_alpha'])
        predictor_resolution = 1

        self.dateEncoder = dateEncoder
        self.scalarEncoder = scalarEncoder
        self.encodingWidth = encodingWidth
        self.sp = sp
        self.tm = tm
        self.predictor = predictor
        self.predictor_resolution = predictor_resolution
        self.count = 0

        self.more_save_keys([
            'dateEncoder',
            'scalarEncoder',
            'encodingWidth',
            'sp',
            'tm',
            'predictor',
            'predictor_resolution',
            'count',
        ])

    def run(self, dateString, consumption):
        dateEncoder = self.dateEncoder
        scalarEncoder = self.scalarEncoder
        encodingWidth = self.encodingWidth
        sp = self.sp
        tm = self.tm
        predictor = self.predictor
        predictor_resolution = self.predictor_resolution

        # Call the encoders to create bit representations for each value.
        # These are SDR objects.
        dateBits = dateEncoder.encode(dateString)
        consumptionBits = scalarEncoder.encode(consumption)

        # Concatenate all these encodings into one large encoding for
        # Spatial Pooling.
        encoding = SDR(encodingWidth).concatenate([consumptionBits, dateBits])

        # Create an SDR to represent active columns, This will be populated by
        # the compute method below. It must have the same dimensions as the
        # Spatial Pooler.
        activeColumns = SDR(sp.getColumnDimensions())

        # Execute Spatial Pooling algorithm over input space.
        sp.compute(encoding, True, activeColumns)

        # Execute Temporal Memory algorithm over active mini-columns.
        tm.compute(activeColumns, learn=True)

        # Predict what will happen, and then train the predictor based on
        # what just happened.
        pdf = predictor.infer(tm.getActiveCells())
        predictions = {1: None, 5: None}

        for n in (1, 5):
            if pdf[n]:
                index = np.argmax(pdf[n])
                predictions[n] = (index * predictor_resolution, pdf[n][index])
            else:
                predictions[n] = (float('nan'), 0)

        predictor.learn(self.count, tm.getActiveCells(),
                        int(consumption / predictor_resolution))

        self.count = self.count + 1

        return {
            'predictions': predictions,
            'anomaly': self.tm.anomaly,
        }
