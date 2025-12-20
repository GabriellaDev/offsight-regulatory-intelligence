# OffSight™ – AI-Powered Regulatory Intelligence for Offshore Wind

OffSight™ is a proof-of-concept system that monitors regulatory changes in the UK offshore wind market and translates them into actionable insights for product design and certification, for the people responsible for requirement monitoring.

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

## Prerequisites

Before running OffSight, ensure you have the following installed and running:

### Required Software

1. **Python 3.11+** - The application is written in Python
2. **PostgreSQL** - Database server (version 12+ recommended)
3. **Ollama** - Local LLM runtime (for AI analysis)
4. **Git** - Version control (for cloning the repository)

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 8GB (16GB recommended for Ollama)
- **Disk Space**: ~5GB for dependencies and models
- **Network**: Internet connection for scraping regulatory sources

## Getting Started

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/GabriellaDev/offsight-regulatory-intelligence.git
cd offsight-regulatory-intelligence

# Create a virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file in the project root with the following variables:

```env
# Database connection (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/offsight

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Demo source URL (GitHub Pages)
DEMO_SOURCE_URL=https://gabrielladev.github.io/offsight-demo-regulation-source/
```

**Note**: Replace `username`, `password`, and database name with your PostgreSQL credentials.

### Step 3: Setup PostgreSQL Database

```bash
# Create the database (using psql or pgAdmin)
createdb offsight

# Or using SQL:
# CREATE DATABASE offsight;
```

### Step 4: Initialize Database Schema

```bash
# Set PYTHONPATH and initialize tables
# Windows PowerShell:
$env:PYTHONPATH="src"
python src/offsight/core/init_db.py

# Linux/macOS:
export PYTHONPATH=src
python src/offsight/core/init_db.py
```

### Step 5: Setup Ollama

```bash
# Install Ollama from https://ollama.com/download
# After installation, pull the required model:
ollama pull llama3.1

# Verify Ollama is running:
ollama list
```

### Step 6: Run the Application

```bash
# With virtual environment activated and PYTHONPATH set:
uvicorn src.offsight.main:app --reload

# The application will be available at:
# - UI: http://localhost:8000/ui
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

## Running the Demo Pipeline

### Option 1: Web UI (Recommended)

1. Navigate to `http://localhost:8000/ui/run`
2. Configure pipeline options (defaults are fine for first run)
3. Click "Run Monitoring Pipeline"
4. View results and click "View Changes →" when changes are detected

### Option 2: Command Line

```bash
# Full pipeline: reset DB, seed sources, scrape, detect changes, run AI analysis
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --reset --yes --seed --scrape --detect --ai

# Or run individual steps:
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --seed --scrape --detect
```

See `src/offsight/core/run_demo_pipeline.py` for all available options.

## Testing

```bash
# Run all tests
PYTHONPATH=src pytest

# Run specific test file
PYTHONPATH=src pytest tests/test_health.py
```

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL installed and running
- [ ] Database `offsight` created
- [ ] `.env` file configured with database URL
- [ ] Database schema initialized (`init_db.py`)
- [ ] Ollama installed and running
- [ ] Ollama model `llama3.1` pulled
- [ ] Application started (`uvicorn src.offsight.main:app --reload`)
- [ ] UI accessible at `http://localhost:8000/ui`

## Documentation

- **Setup Guide**: See [docs/setup.md](docs/setup.md) for detailed installation instructions
- **Architecture**: See [docs/architecture.md](docs/architecture.md) for system design
- **Requirements**: See [docs/requirements.md](docs/requirements.md) for functional requirements
- **Code Documentation**: See [docs/code-documentation.md](docs/code-documentation.md) for docstring standards

## API Documentation

When the application is running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

All API endpoints include docstrings that are automatically rendered in these interfaces.