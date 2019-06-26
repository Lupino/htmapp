model_root='models'
periodic='tcp://127.0.0.1:5000'
max_thread=2

parameters = {
 'enc': {'resolution': 0.88, 'size': 700, 'sparsity': 0.02},
 'sdrc_alpha': 0.1,
 'sp': {'boostStrength': 3.0,
        'columnCount': 1638,
        'numActiveColumnsPerInhArea': 72,
        'potentialPct': 0.85,
        'synPermActiveInc': 0.04,
        'synPermConnected': 0.13999999999999999,
        'synPermInactiveDec': 0.006},
 'time': {'timeOfDay': (30, 1), 'weekend': 21},
 'tm': {'activationThreshold': 17,
        'cellsPerColumn': 13,
        'initialPerm': 0.21,
        'maxSegmentsPerCell': 128,
        'maxSynapsesPerSegment': 64,
        'minThreshold': 10,
        'newSynapseCount': 32,
        'permanenceDec': 0.1,
        'permanenceInc': 0.1}}
