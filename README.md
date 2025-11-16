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
