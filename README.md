# Análisis de Datos Meteorológicos

> Proyecto final — Big Data · Grado en Matemáticas · UNIE Universidad

[![CI](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/ci.yml/badge.svg)](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/ci.yml)
[![Docs](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/docs.yml/badge.svg)](https://sergio-repogit.github.io/climate-trends-spain/)
[![Coverage](https://codecov.io/gh/Sergio-repogit/climate-trends-spain/graph/badge.svg)](https://codecov.io/gh/Sergio-repogit/climate-trends-spain)
[![Version](https://img.shields.io/github/v/release/Sergio-repogit/climate-trends-spain)](https://github.com/Sergio-repogit/climate-trends-spain/releases)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)


---

## Description

Este proyecto tiene como objetivo analizar tendencias climáticas en España a partir de datos meteorológicos históricos.  

Se estudian variables como temperatura, evolución temporal y posibles anomalías climáticas.  

El proyecto está diseñado siguiendo buenas prácticas de ingeniería de datos: código modular, tests automatizados, integración continua (CI) y documentación reproducible.


## Documentation

Full documentation at **[sergio-repogit.github.io/climate-trends-spain/](https://sergio-repogit.github.io/climate-trends-spain/)**

## Installation

  ```bash
    git clone https://github.com/Sergio-repogit/climate-trends-spain.git
    cd climate-trends-spain
    pip install uv
    uv sync --group dev
  ```

## Data Download

Data is not included in the repository. To download:

  ```bash
  python scripts/download_data.py
  ```

## Usage

  ```bash
  uv run pytest                          # run tests
  uv run pytest --cov=src -v     # tests with coverage
  uv run ruff check .                    # lint
  uv run ruff format .                   # format
  uv run mkdocs serve                    # preview docs at localhost:8000
  ```

## Project Structure

  ```
  climate-trends-spain/
    ├── .github/workflows/
    ├── data/
    ├── docs/
    ├── notebooks/
    ├── scripts/
    ├── src/
    ├── tests/
    ├── mkdocs.yml
    ├── pyproject.toml
    └── README.md
  ```

## Author

**Sergio Mínguez Cruces** · [github.com/Sergio-repogit](https://github.com/Sergio-repogit)

## Professor
**Álvaro Diez** · [github.com/alvarodiez20](https://github.com/alvarodiez20)

---

*Big Data · 4º Grado en Matemáticas · UNIE Universidad · 2025–2026*