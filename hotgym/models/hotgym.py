from datetime import datetime
from htm.bindings.sdr import SDR
from htm.encoders.rdse import RDSE, RDSE_Parameters
from htm.encoders.date import DateEncoder
from htm.bindings.algorithms import SpatialPooler
from htm.bindings.algorithms import TemporalMemory

from ..base_model import BaseModel


class Model(BaseModel):
    def __init__(self, parameters, *args, **kwargs):
        BaseModel.__init__(self, *args, **kwargs)

        self.parameters = parameters

        self.more_save_keys(['sp', 'tm'])

    def createEncoder(self):
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

        self.dateEncoder = dateEncoder
        self.scalarEncoder = scalarEncoder
        self.encodingWidth = encodingWidth

    def create(self):
        parameters = self.parameters

        self.createEncoder()

        encodingWidth = self.encodingWidth
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

        self.sp = sp
        self.tm = tm

    def prepare(self, model):
        BaseModel.prepare(self, model)
        self.createEncoder()

    def run(self, timestamp, consumption):
        # Call the encoders to create bit representations for each value.
        # These are SDR objects.
        dateString = datetime.fromtimestamp(timestamp)
        dateBits = self.dateEncoder.encode(dateString)
        consumptionBits = self.scalarEncoder.encode(consumption)

        # Concatenate all these encodings into one large encoding for
        # Spatial Pooling.
        encoding = SDR(self.encodingWidth).concatenate(
            [consumptionBits, dateBits])

        # Create an SDR to represent active columns, This will be populated by
        # the compute method below. It must have the same dimensions as the
        # Spatial Pooler.
        activeColumns = SDR(self.sp.getColumnDimensions())

        # Execute Spatial Pooling algorithm over input space.
        self.sp.compute(encoding, True, activeColumns)

        # Execute Temporal Memory algorithm over active mini-columns.
        self.tm.compute(activeColumns, learn=True)

        return {
            'anomaly': self.tm.anomaly,
        }
