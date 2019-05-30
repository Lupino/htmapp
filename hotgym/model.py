from nupic.bindings.algorithms import SpatialPooler
from nupic.bindings.algorithms import TemporalMemory
from nupic.bindings.sdr import SDR, Metrics
from nupic.encoders.rdse import RDSE, RDSE_Parameters
from nupic.encoders.date import DateEncoder
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood

def createEncoder(parameters):
    model = {}
    timeOfDayEncoder = DateEncoder(parameters["time"]["timeOfDay"])
    model['timeOfDayEncoder'] = timeOfDayEncoder
    weekendEncoder   = DateEncoder(parameters["time"]["weekend"])
    model['weekendEncoder'] = weekendEncoder

    rdseParams = RDSE_Parameters()
    rdseParams.size       = parameters["enc"]["size"]
    rdseParams.sparsity   = parameters["enc"]["sparsity"]
    rdseParams.resolution = parameters["enc"]["resolution"]
    scalarEncoder = RDSE( rdseParams )
    model['scalarEncoder'] = scalarEncoder

    encodingWidth = (timeOfDayEncoder.size
                     + weekendEncoder.size
                     + scalarEncoder.size)
    model['encodingWidth'] = encodingWidth
    return model


def createModel(parameters):
    print('createModel')
    model = createEncoder(parameters)

    encodingWidth = model['encodingWidth']

    spParams = parameters["sp"]
    sp = SpatialPooler(
        inputDimensions            = (encodingWidth,),
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
    model['sp'] = sp

    tmParams = parameters["tm"]
    tm = TemporalMemory(
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
    model['tm'] = tm

    anomaly_history = AnomalyLikelihood()
    model['anomaly_history'] = anomaly_history

    return model

def runModel(model, dateString, consumption):
    # Now we call the encoders to create bit representations for each value.
    timeOfDayBits   = model['timeOfDayEncoder'].encode(dateString)
    weekendBits     = model['weekendEncoder'].encode(dateString)
    consumptionBits = model['scalarEncoder'].encode(consumption)

    # Concatenate all these encodings into one large encoding for Spatial
    # Pooling.
    encoding = SDR( model['encodingWidth'] ).concatenate(
                                [consumptionBits, timeOfDayBits, weekendBits])

    # Create an SDR to represent active columns, This will be populated by the
    # compute method below. It must have the same dimensions as the Spatial
    # Pooler.
    activeColumns = SDR( model['sp'].getColumnDimensions() )

    # Execute Spatial Pooling algorithm over input space.
    model['sp'].compute(encoding, True, activeColumns)

    # Execute Temporal Memory algorithm over active mini-columns.
    model['tm'].compute(activeColumns, learn=True)

    # anomalyLikelihood = model['anomaly_history'].anomalyProbability( consumption, model['tm'].anomaly )
    return model['tm'].anomaly
    # return anomalyLikelihood

def saveModel(store, model):
    print('saveModel')
    store.save('model', {'sp': model['sp'], 'tm': model['tm']})

def prepareModel(model, parameters):
    print('prepareModel')
    if not isinstance(model.get('sp'), SpatialPooler):
        return None

    if not isinstance(model.get('tm'), TemporalMemory):
        return None

    model.update(createEncoder(parameters))
    return model
