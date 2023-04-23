import logging
import sys
import os
import yaml as yml
import jinja2 as j2
from pathlib import Path
from collections import OrderedDict
from types import SimpleNamespace
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException
from munch import Munch

def crossGenerate(config_file:str):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    # check if the config file is valid
    p = Path(config_file)
    if not p.is_file():
        print(f"{config_file} does not exist or is not a file.")
        sys.exit()
   
    #Get base path based on config file location
    basePath = p.parent.absolute()
    config = None
    # Default all folders to the base path
    modelFileLocation = basePath
    templateFileLocation = basePath
    outputFileLocation = basePath

    with open(config_file, 'r') as f:
        try:
            config = yml.safe_load(f)
        except yml.YAMLError as exc:
            print(f"error reading config file {config_file}:")
            print(exc)    
            sys.exit()

    # Read model file location from config
    if config['modelFileLocation']:
        modelFileLocation = Path(f"{basePath}/{config['modelFileLocation']}")
        if not modelFileLocation.is_dir():
            print(f"Model file location {modelFileLocation} is not a valid directory")
            sys.exit()

    # Read template file location from config
    if config['templateFileLocation']:
        templateFileLocation = Path(f"{basePath}/{config['templateFileLocation']}")
        if not templateFileLocation.is_dir():
            print(f"Template file location {templateFileLocation} is not a valid directory")
            sys.exit()
    
    # Read the output location from config, if it does not exist, try to create it
    if config['outputFileLocation']:
        outputFileLocation = Path(f"{basePath}/{config['outputFileLocation']}")
        if not outputFileLocation.is_dir():
            logging.debug(f"Output file location {outputFileLocation} does not exist, trying to create it")
            try:
                os.makedirs(outputFileLocation)
            except os.error(exc):
                print(f"Error occured when trying to create output file location {outputFileLocation}:")
                print(exc)
                sys.exit()
   
    #initialize logging & yaml processor
    logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)
    log = ConsolePrinter(logging_args)
    yaml=Parsers.get_yaml_editor()

    #Initialize jinja2 template environment
    templateEnv = j2.Environment(loader=j2.FileSystemLoader(searchpath=templateFileLocation))
    
    #Process all modelTemplateBindings entries from the config
    for mtb in config['modelTemplateBindings']:
        #Read model file
        model_yaml_file = f"{modelFileLocation}/{mtb['modelFile']}"
        yaml_path = YAMLPath(mtb['modelYAMLPath'])
        (yaml_data, doc_loaded) = Parsers.get_yaml_data(yaml, log, model_yaml_file)
        if not doc_loaded:
            # There was an issue loading the file; an error message has already been
            # printed via ConsolePrinter.
            exit(1)
        # Pass the logging facility and parsed YAML data to the YAMLPath Processor
        processor = Processor(log, yaml_data)

        try:
            logging.debug(f"executing {yaml_path} on model {model_yaml_file}")
            for node_coordinate in processor.get_nodes(yaml_path, mustexist=True):
                #Convert to objects using Munch
                results = Munch.fromDict(node_coordinate.node)
                for obj in results:
                    # process all templatebindings for this selection
                    for templateBinding in mtb['templateBindings']:
                        logging.debug(f"Generating {obj.code} with template {templateBinding}")
                        template = templateEnv.get_template(templateBinding['templateFile'])
                        output = template.render(obj)
                        outputFileName = f"{outputFileLocation}/{templateBinding['outputFileName'].replace('{{name}}', obj.name)}"
                        outFile = open(outputFileName, 'w')
                        outFile.write(output)
                        outFile.close()
                        # Do something with each node_coordinate.node (the actual data)                
        except YAMLPathException as ex:
            # If merely retrieving data, this exception may be deemed non-critical
            # unless your later code absolutely depends upon a result.
            log.error(ex)
