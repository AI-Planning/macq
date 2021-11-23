# Contributing

## Setup

### Installing

Install macq for development by cloning the repository and running
`pip install -e .[dev]`

We recommend installing in a virtual environment to avoid package version
conflicts.

**Note: `tarski` requires [`clingo`](https://potassco.org/clingo/) be installed to work.**

### Formatting

We use [black](https://black.readthedocs.io/en/stable/) for easy and consistent
code formatting.

You can enable the pre-commit formatting hook with `pre-commit install`


## Development

### Type Checking

Run `mypy -p macq` to locate typing errors or inconsistencies in your code.

### Testing and Test Coverage

Run `pytest` to run the test suite. To run a specific test, provide the relative
path to the test(e.g. `pytest tests/test_readme.py`)

To see the test coverage, run `pytest --cov=macq`. For a more detailed coverage
report, run `pytest --cov=macq --cov-report=html`, and open `htmlcov/index.html`
in a browser. This will provide detailed line by line test coverage information,
so you can identify what specifically still needs testing.

### Generating Docs
To generate the HTML documentation, run `pdoc --html macq --config latex_math=True`.

During development, you can run a local HTTP server to reference/see live
changes to the documentation: `pdoc --http : macq --config latex_math=True`.

*Note: `--config latex_math=True` is required to properly render the latex found
in many extraction techniques' documentation.*

