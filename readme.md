# CrossGenerate Python

Code generator that binds YAML model contents on [Jinja2](https://pypi.org/project/Jinja2/) templates using [YAMLPath](https://pypi.org/project/yamlpath/1.0.0/)

## Running CrossGenerate Python locally

- Pull this repository
- Install required dependencies (creating a virtual env is best) using pip install -r ./requirements.txt
- Invoke crossgenerate with python -m crossgenerate ./examples/config.yml

## Configuring VS Code for development

- Install Python extensions including Pylint
- Enable linting with [pycodestyle](https://code.visualstudio.com/docs/python/linting#_pycodestyle-pep8)
- Edit settings for linting and ignore E500 (pycodestyle line exceeds 80 characters) and C0301 (pylint line too long)

```json
 "python.linting.pycodestyleArgs": [
        "--ignore=E501"
    ],
    "pylint.args": ["-d", "C0301"],    
```
