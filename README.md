# ES Dictionary - Earth and Planetary Science Dictionaries

This is a modern Python tool designed to generate and compile Earth and Planetary Science dictionaries for macOS.

The compiler is fully config-driven (via YAML) and class-based, allowing you to compile custom dictionaries dynamically from configuration files or command-line overrides.

---

## Directory Layout

* **`configs/`**: YAML configuration files defining the metadata, inputs, stylesheet, and plist configurations for each dictionary.
* **`data/`**: Raw CSV/TSV datasets with column headers (e.g., `nws-glossary.csv`, `naer-translation.csv`).
* **`assets/`**: Stylesheets (`.css`) and other files needed for macOS Dictionary.app bundles.
* **`templates/`**: XML and plist templates used during generation.
* **`outputs/`**: Generated intermediate files (XML dictionary source files and `.plist` property lists).

---

## Installation

This project is managed via [uv](https://github.com/astral-sh/uv). To install the package and dependencies:

```bash
uv pip install -e .[dev]
```

---

## Running the Compiler

You compile dictionaries dynamically by specifying their configuration files.

```bash
uv run python -m eaps_dict.cli --config configs/[config].yaml
```

### Useful CLI Flags

* **`--reload-app`**: Automatically close and reopen macOS `Dictionary.app` to load the newly compiled dictionary.

  ```bash
  uv run python -m eaps_dict.cli --config configs/nws-glossary.yaml --reload-app
  ```

* **`--no-compile`**: Generate the XML and plist source files in `outputs/` without running the compilation process (useful on systems without the macOS Dictionary Development Kit).

  ```bash
  uv run python -m eaps_dict.cli --config configs/nws-glossary.yaml --no-compile
  ```

* **Overrides**: You can override any configuration parameter on the fly using equivalent CLI flags. For example:

  ```bash
  uv run python -m eaps_dict.cli --config configs/nws-glossary.yaml --name "Custom Dictionary Name" --input-csvs data/custom-glossary.csv
  ```

---

## Running Tests

Automated tests are written with `pytest`. Run them with:

```bash
PYTHONPATH=. uv run pytest
```
