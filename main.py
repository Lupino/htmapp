from hotgym import worker
import sys
specid = '1'
if len(sys.argv) > 1:
    specid = sys.argv[1]
worker.start(specid)
