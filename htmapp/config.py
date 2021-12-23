hotgym_parameters = {
    'enc': {
        "value": {
            'resolution': 0.88,
            'size': 700,
            'sparsity': 0.02
        },
        "time": {
            'timeOfDay': (30, 1),
            'weekend': 21
        }
    },
    'sp': {
        'boostStrength': 3.0,
        'columnCount': 1638,
        'localAreaDensity': 0.04395604395604396,
        'potentialPct': 0.85,
        'synPermActiveInc': 0.04,
        'synPermConnected': 0.13999999999999999,
        'synPermInactiveDec': 0.006
    },
    'tm': {
        'activationThreshold': 17,
        'cellsPerColumn': 13,
        'initialPerm': 0.21,
        'maxSegmentsPerCell': 128,
        'maxSynapsesPerSegment': 64,
        'minThreshold': 10,
        'newSynapseCount': 32,
        'permanenceDec': 0.1,
        'permanenceInc': 0.1
    },
}

simhash_parameters = {
    'encoder': {
        'size': 600,
        'sparsity': 0.2
    },
    'sp': {
        'potentialRadius': 16,
        'boostStrength': 0,
        'columnDimensions': 1600,
        'dutyCyclePeriod': 1000,
        'localAreaDensity': 0.02,
        'minPctOverlapDutyCycle': 0.001,
        'potentialPct': 0.5,
        'stimulusThreshold': 0,
        'synPermActiveInc': 0.1,
        'synPermConnected': 0.1,
        'synPermInactiveDec': 0.01
    }
}

parameters = {
    "hotgym": hotgym_parameters,
    "simhash": simhash_parameters,
}
