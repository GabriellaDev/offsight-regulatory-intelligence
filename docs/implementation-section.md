# Implementation

## Recommended Subsections

1. **Implementation Overview**
2. **Technology Stack**
3. **Local Development Setup**
4. **Database Schema and Initialization**
5. **Service Layer Implementation**
6. **API and UI Layer Implementation**
7. **Configuration Management**

---

## Implementation Overview

The OffSight system is implemented as a Python-based web application following a modular, service-oriented architecture. The implementation prioritizes local-first execution (NFR1), enabling developers to run the entire system—including database, web server, and AI analysis—on a single development machine without external cloud dependencies. The system is built using FastAPI as the web framework, which provides both REST API endpoints and server-rendered UI templates through Jinja2, creating a unified application that serves both programmatic and human interfaces.

The implementation follows a clear separation of concerns, with distinct service layers for scraping, change detection, AI analysis, and validation. All components interact through well-defined interfaces, primarily via the database (PostgreSQL) and direct service method calls. The system uses SQLAlchemy as an Object-Relational Mapping (ORM) layer, which abstracts database operations and enables type-safe model definitions. Configuration is managed through Pydantic Settings, supporting environment variables and `.env` files for flexible deployment across different environments. The local LLM integration via Ollama ensures that all AI processing occurs on-device, maintaining data privacy and eliminating external API dependencies.

## Technology Stack

The following technologies were selected to meet the project's functional and non-functional requirements:

- **Python 3.11+**: The primary programming language, chosen for its extensive ecosystem, readability, and strong support for web development and data processing libraries.

- **FastAPI**: Modern, high-performance web framework for building APIs and web applications. Selected for its automatic OpenAPI documentation, type safety through Pydantic integration, and support for both REST APIs and server-rendered templates.

- **Uvicorn**: ASGI (Asynchronous Server Gateway Interface) server implementation, used to run the FastAPI application. Provides hot-reload capabilities during development and production-ready performance.

- **PostgreSQL**: Relational database management system chosen for its reliability, ACID compliance, and robust support for complex queries and relationships. Essential for storing versioned documents, change records, and maintaining referential integrity.

- **SQLAlchemy**: ORM framework that provides a Pythonic interface to the database. Enables declarative model definitions, automatic relationship management, and database-agnostic query construction.

- **psycopg2-binary**: PostgreSQL database adapter for Python, providing efficient connection pooling and native PostgreSQL protocol support.

- **Pydantic & pydantic-settings**: Data validation library used for request/response models and configuration management. Ensures type safety, automatic validation, and seamless integration with FastAPI's dependency injection system.

- **python-dotenv**: Library for loading environment variables from `.env` files, enabling secure configuration management without hardcoding sensitive values.

- **Jinja2**: Template engine for server-side rendering of HTML pages. Integrated with FastAPI to provide a cohesive web UI without requiring a separate frontend framework.

- **httpx**: Modern HTTP client library for making asynchronous requests to external regulatory sources. Provides better performance and error handling compared to traditional synchronous clients.

- **BeautifulSoup4**: HTML parsing library used to extract and clean content from regulatory web pages, handling malformed HTML and extracting structured text from complex documents.

- **Ollama**: Local LLM runtime that enables on-device AI processing without external API calls. Selected to meet NFR1 (local execution) and ensure data privacy for regulatory content analysis.

- **pytest**: Testing framework used for unit and integration testing, providing fixtures, mocking capabilities, and clear test output for validating system behavior.

## Local-First Execution (NFR1)

The implementation adheres to NFR1 by ensuring the entire system can be deployed and executed on a developer's local machine. This is achieved through several design decisions:

**Database Configuration**: PostgreSQL runs as a local service, with connection parameters configurable via environment variables. The system uses SQLAlchemy's `create_all()` method to initialize the database schema programmatically, eliminating the need for external migration tools or database administration overhead.

**AI Processing**: All AI analysis is performed using Ollama, which runs as a local service on the developer's machine. The system communicates with Ollama via HTTP API calls to `http://localhost:11434`, ensuring no data leaves the local environment. The required LLM model (`llama3.1`) is downloaded and cached locally during setup.

**Development Workflow**: The application is started using a single command (`uvicorn src.offsight.main:app --reload`), with all dependencies managed through a Python virtual environment. The `PYTHONPATH=src` environment variable ensures proper module resolution without requiring package installation. Configuration is externalized through `.env` files, allowing developers to customize database credentials and Ollama settings without modifying code.

**No External Dependencies**: The system does not require Docker, cloud services, or external APIs beyond the regulatory sources being monitored. All components—database, web server, and AI runtime—operate as local processes, making the system fully self-contained and suitable for offline development and demonstration.

## Pipeline Orchestration

The monitoring pipeline is orchestrated by the `PipelineService`, which coordinates all pipeline steps in a sequential, fault-tolerant manner. The orchestrator is responsible for executing the end-to-end workflow: seeding data sources, scraping regulatory content, detecting changes between document versions, and performing AI analysis on detected changes. The implementation ensures that each step can be conditionally enabled or disabled based on user configuration, and that failures in individual steps do not crash the entire pipeline execution.

### Step Execution and Conditional Logic

The pipeline executes eight distinct steps in a fixed order, with each step controlled by a boolean flag passed to the `run_pipeline()` function. The steps are: (1) database initialization, (2) database reset (with confirmation token), (3) seeding requirement categories, (4) seeding demo sources, (5) Ollama connectivity testing, (6) scraping enabled sources, (7) change detection, and (8) AI analysis. Steps 1, 2, and 5 are optional and typically used only during initial setup or troubleshooting. Steps 3-4 are grouped under the `seed_sources` flag, while steps 6-8 represent the core monitoring workflow (scrape, detect, analyze). The UI layer (`run_pipeline_ui_post`) converts HTML form checkbox values to boolean flags, with sensible defaults (most steps enabled by default) to simplify user interaction.

### Result Collection and Logging

Each pipeline step returns a `PipelineStepResult` object containing the step name, execution status (success, warning, error, or skipped), a human-readable message, and optional metrics (counts dictionary). All step results are collected in a `PipelineResult` object, which aggregates totals across steps (e.g., `sources_seeded`, `new_documents`, `new_changes`, `changes_ai_processed`) and maintains a list of warnings encountered during execution. This structured result collection enables the UI to display a comprehensive execution report, showing both individual step outcomes and aggregate metrics. The result is serialized to JSON and base64-encoded for transmission via URL query parameters in the PRG (Post-Redirect-Get) pattern, preventing duplicate form submissions while preserving execution details.

### Fault Tolerance and Error Handling (NFR4)

The pipeline implements multi-level error handling to ensure that failures in scraping or AI summarisation do not crash the entire pipeline (NFR4). At the step level, each step is wrapped in a try-except block that captures exceptions and converts them into `PipelineStepResult` objects with `status="error"`. Critical steps (database initialization, reset, seeding) return early on failure to prevent cascading errors, while non-critical steps (scraping, AI analysis) log warnings and continue execution. At the source level, the scraping step implements per-source error handling: if one source fails to scrape, a warning is logged and the pipeline continues with the next source. Similarly, AI analysis failures are captured as warnings rather than stopping the pipeline, allowing users to review successfully processed changes even if some AI operations fail. This fault-tolerant design ensures that partial results are always available, and users receive clear feedback about which operations succeeded or failed.

### PRG Pattern Implementation

The UI layer implements the Post-Redirect-Get (PRG) pattern to prevent duplicate pipeline executions when users refresh the results page. When the pipeline form is submitted via POST, the `run_pipeline_ui_post` handler executes the pipeline, serializes the result to JSON, base64-encodes it, and redirects to the GET endpoint (`/ui/run`) with the encoded result in the query parameter. The GET handler (`run_pipeline_ui_get`) decodes and deserializes the result for display. This pattern ensures that refreshing the results page does not re-execute the pipeline, and that execution results are preserved across page loads without requiring server-side session storage.

### Requirements Mapping

The pipeline orchestration directly implements several functional and non-functional requirements:

- **FR2 (Periodic retrieval)**: Implemented by the scraping step, which retrieves content from all enabled sources and stores raw content in the database.

- **FR3 (Version tracking)**: Implemented by the scraping step's `fetch_and_store_if_changed()` method, which detects content changes via hash comparison and stores new document versions.

- **FR4 (Change detection)**: Implemented by the change detection step, which computes differences between document versions using Python's `difflib` library and creates `RegulationChange` records.

- **FR5 (AI summarisation)**: Implemented by the AI analysis step, which calls `AiService.analyse_pending_changes()` to generate summaries for pending changes using the local Ollama LLM.

- **FR6 (Impact classification)**: Implemented by the AI analysis step, which classifies each change into one of seven predefined requirement classes (spatial constraints, temporal constraints, procedural obligations, technical performance expectations, operational restrictions, evidence and reporting requirements, other/unclear).

- **FR10 (Pipeline execution UI)**: Implemented by the UI route handlers (`run_pipeline_ui_post`, `run_pipeline_ui_get`), which provide a web-based interface for executing the full pipeline without command-line access.

- **NFR2 (Performance)**: The AI analysis step respects the `ai_limit` parameter (default 5, configurable up to 100), ensuring that batch processing of up to 20 documents completes within a reasonable time frame.

- **NFR4 (Reliability)**: Fault tolerance is implemented through per-step and per-source error handling, ensuring that failures in scraping or AI summarisation are logged as warnings and do not crash the pipeline.

- **NFR5 (Maintainability)**: The pipeline orchestrator delegates actual work to dedicated service classes (`ScraperService`, `ChangeDetectionService`, `AiService`), maintaining clear separation of concerns and enabling independent testing and modification of each component.

