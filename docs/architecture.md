# Architecture

OffSight follows a modular, service-oriented architecture designed to separate concerns and enable independent development and testing of each component. The system is built on Python with FastAPI as the web framework, PostgreSQL for persistent storage, and a local LLM (via Ollama) for AI-powered analysis. The architecture supports local deployment on a developer machine while maintaining scalability and maintainability through clear component boundaries and well-defined interfaces.

## Components

### Scraper / Data Retrieval Service

**Main Responsibility:**
The Scraper service is responsible for periodically retrieving regulatory documents from configured sources. It handles HTTP requests, HTML parsing, content extraction, and storing raw document content in the database.

**Main Inputs:**
- Source configuration (URLs, retrieval intervals)
- Scheduling triggers (time-based or manual)

**Main Outputs:**
- Raw document content stored as RegulationDocument entities
- Retrieval metadata (timestamps, HTTP status, content hashes)

**Interactions:**
- Reads Source configurations from the Database
- Writes RegulationDocument entities to the Database
- Uses the Configuration service to access settings (e.g., retry policies, timeouts)
- May trigger the Change Detection Service when new documents are retrieved

### Change Detection Service

**Main Responsibility:**
The Change Detection Service compares new document versions with previous versions to identify changes. It computes differences between document versions and creates RegulationChange records when changes are detected.

**Main Inputs:**
- New RegulationDocument entities
- Previous RegulationDocument entities from the same Source

**Main Outputs:**
- RegulationChange entities with computed diff content
- Change detection metadata (detection timestamps, change severity indicators)

**Interactions:**
- Reads RegulationDocument entities from the Database
- Writes RegulationChange entities to the Database
- Triggers the AI Service when a new change is detected
- Uses content hashing and diff algorithms to efficiently detect changes

### AI Service (Ollama client)

**Main Responsibility:**
The AI Service communicates with the local Ollama LLM to generate human-readable summaries and classify regulatory changes into predefined categories. It handles prompt construction, API calls to Ollama, and response parsing.

**Main Inputs:**
- RegulationChange entities with diff content
- Category definitions for classification

**Main Outputs:**
- AI-generated summaries (text)
- Category classifications
- Updated RegulationChange entities with AI-generated content

**Interactions:**
- Reads RegulationChange entities from the Database (those pending AI processing)
- Updates RegulationChange entities with AI summaries and categories
- Communicates with Ollama API via HTTP (configured through Configuration service)
- Handles errors gracefully and logs failures without crashing the pipeline

### API Layer (FastAPI)

**Main Responsibility:**
The API Layer provides RESTful endpoints for accessing and managing regulatory changes, sources, and validations. It handles HTTP requests, request validation, authentication (if implemented), and response formatting.

**Main Inputs:**
- HTTP requests (GET, POST, PUT, DELETE)
- Request parameters and JSON payloads

**Main Outputs:**
- HTTP responses with JSON data
- Status codes and error messages

**Interactions:**
- Reads from and writes to the Database through service layer abstractions
- Exposes endpoints for the UI Layer to consume
- Validates user input using Pydantic models
- May call various services (Change Detection, AI Service) through API endpoints

### UI Layer (web frontend or templates)

**Main Responsibility:**
The UI Layer provides a user interface for viewing regulatory changes, filtering results, performing validations, managing sources, and executing the monitoring pipeline. It is implemented using FastAPI templates (Jinja2) with a server-rendered approach.

**Main Inputs:**
- User interactions (clicks, form submissions, filter selections)
- Data from the API Layer

**Main Outputs:**
- Rendered HTML pages
- User interface elements (tables, forms, filters, pipeline execution interface)

**Interactions:**
- Consumes data from the API Layer via HTTP requests
- Sends user validation actions back to the API Layer
- Displays RegulationChange lists with filtering and sorting capabilities
- Allows users to view, validate, and correct AI-generated summaries and categories
- Provides a web-based pipeline execution interface (`/ui/run`) that orchestrates all pipeline steps
- Enables source management (add, update, enable/disable) through a web interface (`/ui/sources`)

### Database (PostgreSQL)

**Main Responsibility:**
The Database provides persistent storage for all entities (Sources, RegulationDocuments, RegulationChanges, Categories, Users, ValidationRecords). It ensures data integrity through foreign key constraints and supports efficient querying.

**Main Inputs:**
- SQL queries and transactions from all services
- Entity creation, updates, and deletions

**Main Outputs:**
- Query results and transaction confirmations
- Stored entity data

**Interactions:**
- Accessed by all services through SQLAlchemy ORM
- Stores all domain entities and their relationships
- Provides transaction support for data consistency

### Configuration / Settings

**Main Responsibility:**
The Configuration component manages application settings, environment variables, and connection parameters. It provides a centralized way to access database URLs, Ollama endpoints, and other configuration values.

**Main Inputs:**
- Environment variables
- `.env` file (if present)
- Default values

**Main Outputs:**
- Settings objects accessible throughout the application
- Validated configuration values

**Interactions:**
- Used by all components that need configuration (Database connections, Ollama client, Scraper timeouts, etc.)
- Loads settings at application startup and caches them for performance

## Data Flow

The main operational flow of OffSight follows these steps:

1. **Source Configuration**: A user or administrator configures one or more regulatory Sources through the UI/API, specifying URLs and monitoring parameters. These Sources are stored in the Database.

2. **Periodic Retrieval**: The Scraper service periodically (or on-demand) retrieves content from all enabled Sources. It fetches the current version of each regulatory document, extracts the content, and stores it as a new RegulationDocument entity in the Database.

3. **Change Detection**: When a new RegulationDocument is stored, the Change Detection Service compares it with the previous version from the same Source. If the content hash differs, it computes the differences and creates a RegulationChange entity with the diff content.

4. **AI Processing**: For each newly detected RegulationChange, the AI Service sends the diff content to the Ollama LLM with appropriate prompts. The LLM generates a human-readable summary and classifies the change into one of the predefined Categories. The AI Service updates the RegulationChange entity with the summary and category.

5. **Storage**: All entities (Sources, RegulationDocuments, RegulationChanges, Categories) are persisted in PostgreSQL, ensuring traceability and historical tracking.

6. **User Access and Validation**: Users access the UI to view a list of detected changes, filtered by source, date, category, or validation status. Users can review the AI-generated summaries and categories, and create ValidationRecords to approve, correct, or reject the AI's interpretation. These validations are stored in the Database and can be used to improve future AI accuracy or for reporting purposes.

7. **Pipeline Execution**: Users can execute the full monitoring pipeline through the web UI (`/ui/run`), which provides a unified interface for running all pipeline steps (seed sources, scrape, detect changes, AI analysis) without requiring command-line access. The pipeline execution is idempotent and safe to run multiple times.

## Use in Documentation and Diagrams

This architecture description will be used to create component diagrams and sequence diagrams in Astah, illustrating how the different services interact and how data flows through the system. These diagrams will form the backbone for the technical architecture chapters in the bachelor project report, providing visual representations of the system design and supporting the narrative explanation of how OffSight operates.
