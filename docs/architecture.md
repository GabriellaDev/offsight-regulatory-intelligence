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
The AI Service communicates with the local Ollama LLM to generate human-readable summaries and classify regulatory changes into predefined requirement classes. It handles prompt construction, API calls to Ollama, response parsing, and category normalization to ensure consistency with the fixed taxonomy.

**Main Inputs:**
- RegulationChange entities with diff content
- Fixed requirement class taxonomy (7 predefined categories)

**Main Outputs:**
- AI-generated summaries (text)
- Requirement class classifications (mapped to predefined categories)
- Updated RegulationChange entities with AI-generated content

**Interactions:**
- Reads RegulationChange entities from the Database (those with status='pending' and ai_summary=NULL)
- Updates RegulationChange entities with AI summaries and categories, setting status to 'ai_suggested'
- Communicates with Ollama API via HTTP (configured through Configuration service)
- Handles errors gracefully and logs failures without crashing the pipeline (per-change error handling)
- Normalizes AI responses to match exact predefined category names

### Pipeline Service (Orchestrator)

**Main Responsibility:**
The Pipeline Service orchestrates the complete monitoring pipeline workflow, coordinating all pipeline steps in a sequential, fault-tolerant manner. It handles conditional step execution, result collection, and error handling to ensure partial failures do not crash the entire pipeline.

**Main Inputs:**
- Pipeline configuration flags (seed_sources, scrape, detect, run_ai, etc.)
- Database session for all operations

**Main Outputs:**
- PipelineResult object containing step results, aggregated totals, and warnings
- Structured execution logs for UI display

**Interactions:**
- Orchestrates ScraperService, ChangeDetectionService, and AiService
- Manages database initialization and reset operations (with confirmation)
- Seeds requirement categories and demo sources
- Tests Ollama connectivity before AI analysis
- Collects results from all steps and aggregates metrics
- Implements per-source and per-change error handling to ensure fault tolerance

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
- Renders HTML pages using Jinja2 templates (server-side rendering)
- Displays RegulationChange lists with filtering by status and source ID
- Allows users to view change details including diff content, AI suggestions, and validation history
- Provides validation forms for approving, correcting, or rejecting AI suggestions
- Provides a web-based pipeline execution interface (`/ui/run`) that calls PipelineService
- Implements PRG (Post-Redirect-Get) pattern to prevent duplicate pipeline executions
- Enables source management (add, update, enable/disable) through a web interface (`/ui/sources`)
- Serves static files (images, CSS) from `/static` directory

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

### Validation Service

**Main Responsibility:**
The Validation Service provides shared logic for processing human validation decisions (approve, correct, reject) and creating ValidationRecord entities. It handles user resolution, category normalization, and status updates for RegulationChange entities.

**Main Inputs:**
- RegulationChange entity to validate
- Validation decision (approved, corrected, rejected)
- Optional corrections (final summary, final category, notes)

**Main Outputs:**
- ValidationRecord entity with validator identity, timestamp, and decision
- Updated RegulationChange status (validated, corrected, rejected)

**Interactions:**
- Reads and updates RegulationChange entities in the Database
- Creates ValidationRecord entities for audit trail
- Resolves user identity (uses demo user if not provided)
- Normalizes category names to match database format
- Used by both API and UI validation endpoints

### Configuration / Settings

**Main Responsibility:**
The Configuration component manages application settings, environment variables, and connection parameters. It provides a centralized way to access database URLs, Ollama endpoints, and other configuration values using Pydantic Settings.

**Main Inputs:**
- Environment variables (highest priority)
- `.env` file (if present)
- Default values (lowest priority)

**Main Outputs:**
- Settings objects accessible throughout the application
- Validated configuration values with type safety

**Interactions:**
- Used by all components that need configuration (Database connections, Ollama client, Scraper timeouts, etc.)
- Loads settings at application startup and caches them using `@lru_cache` for performance
- Provides type-safe access to configuration through Pydantic models

## Data Flow

The main operational flow of OffSight follows these steps:

1. **Source Configuration**: A user configures one or more regulatory Sources through the UI (`/ui/sources`), specifying URLs, descriptions, and enabled/disabled status. These Sources are stored in the Database with timestamps for traceability.

2. **Pipeline Execution**: A user triggers the monitoring pipeline through the web UI (`/ui/run`) or command line. The PipelineService orchestrates all steps in sequence, with conditional execution based on user-selected options.

3. **Content Retrieval**: The ScraperService retrieves content from all enabled Sources. For each source, it:
   - Fetches current content via HTTP GET
   - Parses HTML using BeautifulSoup to extract text
   - Computes SHA256 hash of the content
   - Compares hash with the latest stored document
   - Stores a new RegulationDocument only if the hash differs (idempotent operation)
   - Preserves source URL and retrieval timestamp for traceability

4. **Change Detection**: The ChangeDetectionService processes all enabled sources:
   - Retrieves all RegulationDocument entities for each source in chronological order
   - Compares consecutive document pairs
   - Computes unified diff using Python's `difflib` library
   - Creates a RegulationChange entity only if the diff is non-empty (filters whitespace-only changes)
   - Links changes to both previous and new document versions via foreign keys
   - Sets initial status to "pending"

5. **AI Processing**: The AiService processes pending changes:
   - Queries for RegulationChange entities with status='pending' and ai_summary=NULL
   - For each change, sends the diff content to Ollama LLM with a constrained prompt
   - The prompt instructs the LLM to return one of 7 predefined requirement classes
   - Parses and normalizes the AI response to match exact category names
   - Updates the RegulationChange with ai_summary, category_id, and sets status to "ai_suggested"
   - Implements per-change error handling to continue processing even if some analyses fail

6. **Storage and Traceability**: All entities (Sources, RegulationDocuments, RegulationChanges, Categories, ValidationRecords) are persisted in PostgreSQL with:
   - Foreign key relationships ensuring referential integrity
   - Timestamps (created_at, retrieved_at, detected_at, validated_at) for audit trail
   - Content hashes for duplicate detection
   - Status fields tracking workflow progression

7. **User Access and Validation**: Users access the UI to:
   - View a list of detected changes, filtered by status or source ID
   - View detailed change information including diff content and AI suggestions
   - Create ValidationRecords to approve, correct, or reject AI suggestions
   - The ValidationService processes validation decisions, updates RegulationChange status, and creates audit trail records

8. **Pipeline Results**: After pipeline execution, the UI displays:
   - Step-by-step execution results with status indicators (success, warning, error)
   - Aggregated totals (sources scraped, new documents, new changes, AI processed)
   - Warnings for non-critical failures (e.g., individual source scrape failures)
   - A success banner with a link to view detected changes if new changes were found

## Use in Documentation and Diagrams

This architecture description will be used to create component diagrams and sequence diagrams in Astah, illustrating how the different services interact and how data flows through the system. These diagrams will form the backbone for the technical architecture chapters in the bachelor project report, providing visual representations of the system design and supporting the narrative explanation of how OffSight operates.
