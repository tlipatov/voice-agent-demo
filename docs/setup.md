# Local Python Setup

## Prerequisites

- Python 3.11+
- `pip`

## Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment configuration

```bash
cp .env.example .env
```

Update `.env` values as needed for your local services.

## Quick verification

```bash
python -c "import fastapi, chromadb, typer; print('dependencies-ok')"
```
