import sys
from . import crossgenerate

# Entry point of module, process commandline arguments and invoke crossGenerate
if len(sys.argv) != 2:
    print('usage: python -m crossGenerate <configfile>')
    sys.exit()

config_file = sys.argv[1]
crossgenerate.crossGenerate(config_file)
