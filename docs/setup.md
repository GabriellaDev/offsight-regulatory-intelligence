# Setup Guide

This document provides detailed setup instructions for running OffSight™ on a local development machine.

## System Requirements

### Software Prerequisites

1. **Python 3.11 or higher**
   - Check version: `python --version`
   - Download: https://www.python.org/downloads/

2. **PostgreSQL 12 or higher**
   - Download: https://www.postgresql.org/download/
   - Ensure PostgreSQL service is running

3. **Ollama** (for AI analysis)
   - Download: https://ollama.com/download
   - Required model: `llama3.1`

4. **Git** (for version control)
   - Download: https://git-scm.com/downloads

### Hardware Requirements

- **RAM**: Minimum 8GB, 16GB recommended (Ollama requires significant memory)
- **Disk Space**: ~5GB for dependencies, models, and database
- **Network**: Internet connection for scraping regulatory sources

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd offsight-regulatory-intelligence
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Why use a virtual environment?**
- Isolates project dependencies from system Python
- Prevents conflicts with other Python projects
- Ensures reproducible builds

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM for database
- `psycopg2-binary` - PostgreSQL adapter
- `httpx` - HTTP client
- `beautifulsoup4` - HTML parsing
- `pydantic` - Data validation
- `jinja2` - Template engine
- `pytest` - Testing framework

### 4. Configure PostgreSQL Database

**Create database:**
```sql
CREATE DATABASE offsight;
```

**Or using command line:**
```bash
createdb offsight
```

**Verify connection:**
```bash
psql -U your_username -d offsight -c "SELECT version();"
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database connection string
# Format: postgresql+psycopg2://username:password@host:port/database
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/offsight

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Demo source URL (GitHub Pages)
DEMO_SOURCE_URL=https://gabrielladev.github.io/offsight-demo-regulation/
```

**Security Note:** Never commit `.env` files to version control. They are already in `.gitignore`.

### 6. Initialize Database Schema

```bash
# Windows PowerShell:
$env:PYTHONPATH="src"
python src/offsight/core/init_db.py

# Linux/macOS:
export PYTHONPATH=src
python src/offsight/core/init_db.py
```

This creates all necessary database tables based on SQLAlchemy models.

### 7. Setup Ollama

**Install Ollama:**
- Download from https://ollama.com/download
- Follow installation instructions for your OS
- Ollama should start automatically after installation

**Pull required model:**
```bash
ollama pull llama3.1
```

**Verify installation:**
```bash
ollama list
# Should show llama3.1 in the list

ollama run llama3.1 "Hello"
# Should return a response from the model
```

**Note:** The first time you pull a model, it may take several minutes depending on your internet connection.

## Running the Application

### Start the Server

```bash
# Ensure virtual environment is activated
# Set PYTHONPATH (if not already set)
# Windows PowerShell:
$env:PYTHONPATH="src"
uvicorn src.offsight.main:app --reload

# Linux/macOS:
export PYTHONPATH=src
uvicorn src.offsight.main:app --reload
```

**Server will start at:** `http://localhost:8000`

### Access Points

- **Web UI Home**: http://localhost:8000/ui
- **Changes List**: http://localhost:8000/ui/changes
- **Sources Management**: http://localhost:8000/ui/sources
- **Run Pipeline**: http://localhost:8000/ui/run
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Running the Demo Pipeline

### Via Web UI (Recommended)

1. Navigate to http://localhost:8000/ui/run
2. Configure options (defaults work for first run)
3. Click "Run Monitoring Pipeline"
4. View results and click "View Changes →" when changes are detected

### Via Command Line

```bash
# Full pipeline with reset
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --reset --yes --seed --scrape --detect --ai

# Individual steps
PYTHONPATH=src python src/offsight/core/run_demo_pipeline.py --seed --scrape --detect --ai
```

## Verification Checklist

Before running the application, verify:

- [ ] Python 3.11+ installed and accessible
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows required packages)
- [ ] PostgreSQL installed and service running
- [ ] Database `offsight` created
- [ ] `.env` file exists with correct database URL
- [ ] Database schema initialized (tables exist)
- [ ] Ollama installed and running
- [ ] Model `llama3.1` pulled (`ollama list`)
- [ ] `PYTHONPATH=src` set (or use full module paths)

## Troubleshooting

### Database Connection Errors

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
- Verify PostgreSQL service is running
- Check database credentials in `.env`
- Ensure database `offsight` exists
- Verify firewall allows connections on port 5432

### Ollama Connection Errors

**Error:** `Failed to call Ollama API`

**Solutions:**
- Verify Ollama is running: `ollama list`
- Check `OLLAMA_BASE_URL` in `.env` (default: `http://localhost:11434`)
- Ensure model is pulled: `ollama pull llama3.1`
- Test manually: `curl http://localhost:11434/api/tags`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'offsight'`

**Solutions:**
- Set `PYTHONPATH=src` before running commands
- Ensure you're in the project root directory
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Already in Use

**Error:** `Address already in use`

**Solutions:**
- Change port: `uvicorn src.offsight.main:app --reload --port 8001`
- Kill existing process using port 8000
- Check if another instance is already running

## Development Workflow

1. **Start PostgreSQL** (if not running as service)
2. **Activate virtual environment**
3. **Set PYTHONPATH**: `export PYTHONPATH=src` (Linux/macOS) or `$env:PYTHONPATH="src"` (Windows)
4. **Start Ollama** (usually runs automatically)
5. **Run server**: `uvicorn src.offsight.main:app --reload`
6. **Access UI**: Open http://localhost:8000/ui in browser

## Next Steps

After successful setup:

1. Run the pipeline via UI: http://localhost:8000/ui/run
2. View detected changes: http://localhost:8000/ui/changes
3. Review and validate changes: Click "View" on any change
4. Manage sources: http://localhost:8000/ui/sources

