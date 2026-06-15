# ES Dictionary - Earth and Planetary Science Dictionaries

This is a modern Python tool designed to generate and compile Earth and Planetary Science dictionaries for macOS.

## Installation

This project is managed via [uv](https://github.com/astral-sh/uv). To install the package and development dependencies in your local virtual environment:

```bash
uv pip install -e .[dev]
```

## Running the tool

Use the command line interface to generate the dictionary XML files and optionally compile them:

### Compile Both Dictionaries

```bash
uv run python -m eaps_dict.cli --all
```

To automatically open the dictionary app after compilation, add the `--reload-app` flag:

```bash
uv run python -m eaps_dict.cli --reload-app
```

### Compile NWS Glossary Only

```bash
uv run python -m eaps_dict.cli --type nws
```

### Compile NAER English-Traditional Chinese Translations Only

```bash
uv run python -m eaps_dict.cli --type naer
```

## Running Tests

Automated tests are written with `pytest`. Run them via:

```bash
uv run pytest
```
