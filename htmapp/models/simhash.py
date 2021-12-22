from htm.encoders.simhash_document_encoder import SimHashDocumentEncoder, \
        SimHashDocumentEncoderParameters
from htm.algorithms import SpatialPooler, Classifier
from htm.bindings.sdr import SDR
import re

from ..base_model import BaseModel

re_spec_code = re.compile(r'[ /{}\[\]\(\).,=+-]+')


class Model(BaseModel):
    model_name = 'simhash'

    def __init__(self, *args, **kwargs):
        BaseModel.__init__(self, *args, **kwargs)

        self.more_save_keys(['sdrc', 'sp', 'encoder', 'targets'])

    def create(self):
        parameters = self.checkpoint.get_parameters()
        print(parameters)

        # Make the Encoders.
        encoderParameters = SimHashDocumentEncoderParameters()
        encoderParameters.activeBits = 0
        encoderParameters.caseSensitivity = False
        encoderParameters.encodeOrphans = False
        encoderParameters.excludes = []
        encoderParameters.frequencyCeiling = 0
        encoderParameters.frequencyFloor = 0
        encoderParameters.size = parameters['encoder']['size']
        encoderParameters.sparsity = parameters['encoder']['sparsity']
        encoderParameters.tokenSimilarity = True
        encoderParameters.vocabulary = {}
        encoder = SimHashDocumentEncoder(encoderParameters)
        encodingWidth = encoder.size

        # Make the HTM.  SpatialPooler & associated tools.
        sp = SpatialPooler(
            inputDimensions=(encodingWidth, ),
            columnDimensions=(parameters['sp']['columnDimensions'], ),
            potentialRadius=parameters['sp']['potentialRadius'],
            potentialPct=parameters['sp']['potentialPct'],
            globalInhibition=True,
            localAreaDensity=parameters['sp']['localAreaDensity'],
            stimulusThreshold=int(round(
                parameters['sp']['stimulusThreshold'])),
            synPermInactiveDec=parameters['sp']['synPermInactiveDec'],
            synPermActiveInc=parameters['sp']['synPermActiveInc'],
            synPermConnected=parameters['sp']['synPermConnected'],
            minPctOverlapDutyCycle=parameters['sp']['minPctOverlapDutyCycle'],
            dutyCyclePeriod=int(round(parameters['sp']['dutyCyclePeriod'])),
            boostStrength=parameters['sp']['boostStrength'],
            seed=0,
            # this is important, 0="random" seed
            # which changes on each invocation
            spVerbosity=99,
            wrapAround=True)

        sdrc = Classifier()

        self.encoder = encoder
        self.sp = sp
        self.sdrc = sdrc
        self.targets = []

    def run(self, doc, target=None):
        # Call the encoders to create bit representations for each value.
        # These are SDR objects.
        doc = re_spec_code.sub(' ', doc)
        doc = doc.strip().lower()

        encoding = self.encoder.encode(doc)

        # Create an SDR to represent active columns, This will be populated by
        # the compute method below. It must have the same dimensions as the
        # Spatial Pooler.
        activeColumns = SDR(self.sp.getColumnDimensions())

        # Execute Spatial Pooling algorithm over input space.
        self.sp.compute(encoding, False, activeColumns)

        infer = self.sdrc.infer(activeColumns)
        infers = list(zip(self.targets, infer))
        infers.sort(key=lambda x: x[1], reverse=True)

        if target:
            if target not in self.targets:
                self.targets.append(target)

            self.sp.compute(encoding, True, activeColumns)
            self.sdrc.learn(activeColumns, self.targets.index(target))

        return {'infers': infers[:10]}
