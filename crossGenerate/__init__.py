"""crossgenerate module, contains all classes for the generator"""
import sys
from .crossgenerate import CrossGenerate
from .crossgenerate_exception import CrossGenerateException

if __name__ == "__main__":
    # Entry point of module, process commandline arguments and invoke crossGenerate
    if len(sys.argv) != 2:
        print('usage: python -m crossGenerate <configfile>')
        sys.exit()

    config_file: str = sys.argv[1]
    generator: CrossGenerate = CrossGenerate()
    generator.generate(config_file)
