model_root='models'
periodic='tcp://127.0.0.1:5000'
max_process=4

parameters = {
 'enc': {'resolution': 0.9551003024002529,
         'size': 692,
         'sparsity': 0.02349173387867304},
 'sp': {'boostStrength': 2.331600954004477,
        'columnCount': 1905,
        'numActiveColumnsPerInhArea': 34,
        'potentialPct': 0.9616584936945282,
        'synPermActiveInc': 0.034755234293843695,
        'synPermConnected': 0.0709642810371415,
        'synPermInactiveDec': 0.007365910271986643},
 'time': {'timeOfDay': (30, 2), 'weekend': 29},
 'tm': {'activationThreshold': 17,
        'cellsPerColumn': 27,
        'initialPerm': 0.20991245171830633,
        'maxSegmentsPerCell': 152,
        'maxSynapsesPerSegment': 25,
        'minThreshold': 7,
        'newSynapseCount': 20,
        'permanenceDec': 0.09335662142342668,
        'permanenceInc': 0.08673586267418514}}
