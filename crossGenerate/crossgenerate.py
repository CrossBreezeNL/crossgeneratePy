""" crossgenerate class """
import logging
import os
from pathlib import Path
from types import SimpleNamespace
import yaml as yml
import jinja2 as j2
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException
from munch import Munch
from .crossgenerate_exception import CrossGenerateException


class CrossGenerate:
    ''' Main generator class '''

    def __init__(self) -> None:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    def generate(self, config_file: str):
        ''' Generates code based on the config file '''
        config_path: Path = Path(config_file)
        config: dict = self.__read_config(config_path=config_path)

        # Default all folders to the base path
        base_path: Path = config_path.parent.absolute()

        # Get base path based on config file location
        model_file_location: Path = self.__get_qualified_path(base_path=base_path, config=config, folder='modelFileLocation', create_if_not_exists=False)
        template_file_location: Path = self.__get_qualified_path(base_path=base_path, config=config, folder='templateFileLocation', create_if_not_exists=False)
        output_file_location: Path = self.__get_qualified_path(base_path=base_path, config=config, folder='outputFileLocation', create_if_not_exists=True)

        # initialize logging & yaml processor
        logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)
        log = ConsolePrinter(logging_args)
        yaml = Parsers.get_yaml_editor()

        # Initialize jinja2 template environment
        template_env: j2.Environment = j2.Environment(loader=j2.FileSystemLoader(searchpath=template_file_location))

        # Process all modelTemplateBindings entries from the config
        for mtb in config['modelTemplateBindings']:
            # Read model file
            model_yaml_file = f"{model_file_location}/{mtb['modelFile']}"
            yaml_path = YAMLPath(mtb['modelYAMLPath'])
            (yaml_data, doc_loaded) = Parsers.get_yaml_data(yaml, log, model_yaml_file)
            if not doc_loaded:
                # There was an issue loading the file; an error message has already been
                # printed via ConsolePrinter.
                exit(1)
            # Pass the logging facility and parsed YAML data to the YAMLPath Processor
            processor = Processor(log, yaml_data)

            try:
                logging.debug("executing %s on model %s", yaml_path, model_yaml_file)
                for node_coordinate in processor.get_nodes(yaml_path, mustexist=True):
                    # Convert to objects using Munch
                    results = Munch.fromDict(node_coordinate.node)
                    self.__process_model_template_binding(model_items=results, templates=mtb['templateBindings'], template_env=template_env, output_file_location=output_file_location)

            except YAMLPathException as ex:
                # If merely retrieving data, this exception may be deemed non-critical
                # unless your later code absolutely depends upon a result.
                log.error(ex)

    def __read_config(self, config_path: Path) -> dict:

        if not config_path.is_file():
            logging.error("%s does not exist or is not a file.", config_path)
            raise CrossGenerateException("Error reading config file")

        config: dict = None
        with open(file=config_path, mode='r', encoding='UTF-8') as config_stream:
            try:
                config = yml.safe_load(config_stream)
            except yml.YAMLError as exc:
                logging.error("Error readong config file %s", config_path)
                logging.error(exc)
                raise CrossGenerateException(exc) from exc
        return config

    def __get_qualified_path(self, base_path: Path, config: dict, folder: str, create_if_not_exists: bool) -> Path:
        if config[folder]:
            file_location: Path = Path(f"{base_path}/{config[folder]}")
            if not file_location.is_dir():
                if create_if_not_exists:
                    logging.debug("folder %s does not exist, trying to create it", file_location)
                    try:
                        os.makedirs(file_location)
                    except os.error as exc:
                        logging.error("Error occured when trying to create file location %s", file_location)
                        logging.error(exc)
                        raise CrossGenerateException(exc) from exc
                else:
                    logging.error("%s does not exist", file_location)
                    raise CrossGenerateException()
            return file_location
        return base_path

    def __process_model_template_binding(self, model_items: Munch, templates: dict, template_env: j2.Environment, output_file_location: Path):
        for obj in model_items:
            # process all templatebindings for this selection
            for template_binding in templates:
                template = template_env.get_template(template_binding['templateFile'])
                output = template.render(obj)
                output_file_name: str = f"{output_file_location}/{template_binding['outputFileName'].replace('{{name}}', obj.name)}"
                with open(output_file_name, mode='w', encoding='UTF-8') as output_file:
                    output_file.write(output)
                    output_file.close()
