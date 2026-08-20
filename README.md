# BaseballCommand
## Development
Run the following command in the terminal to install Poetry:
`curl -sSL https://install.python-poetry.org | python3 -`
>There may be an SSL error, if so, run this command in the terminal: 
> 
>`pip install pip-system-certs`

Then, to activate the Poetry virtual environment, run:

`eval $(poetry env activate)`

To install any dependencies, run:

`poetry install`

To install the CLI for testing, in the virtual environment, run

`pip install --editable .`