# OffSight™ – AI-Powered Regulatory Intelligence for Offshore Wind

OffSight™ is a proof-of-concept system that monitors regulatory changes in the UK offshore wind market and translates them into actionable insights for product design and certification.

This project is developed as part of a bachelor thesis at VIA University College (Global Business Engineering).

## Goals

- Continuously monitor selected UK regulatory sources (e.g. legislation.gov.uk).
- Detect changes between document versions.
- Use a local LLM (via Ollama) to summarise and classify changes.
- Provide a simple UI/API to review, validate, and trace regulatory updates.

## Tech Stack

- **Language**: Python
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **AI**: Local LLM via Ollama
- **Frontend/UI**: Simple web UI (FastAPI templates or minimal React)
- **Version Control**: Git + GitHub

## Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure environment**: Copy `.env.example` to `.env` and configure your database and Ollama URLs
3. **Initialize database**: `PYTHONPATH=src python src/offsight/core/init_db.py`
4. **Run the application**: `PYTHONPATH=src uvicorn src.offsight.main:app --reload`
5. **Access the UI**: Open `http://localhost:8000/ui` in your browser
6. **Run tests**: `PYTHONPATH=src pytest`

## Demo Pipeline

For a complete demo workflow, use the demo pipeline script:

```bash
# Full pipeline: reset DB, seed sources, scrape, detect changes, run AI analysis
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --reset --yes --seed --scrape --detect --ai

# Or run individual steps:
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --seed --scrape --detect
```

See `src/offsight/core/run_demo_pipeline.py` for all available options.