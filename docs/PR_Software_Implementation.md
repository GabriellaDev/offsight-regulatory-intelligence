# Implementation

## Implementation Overview

The OffSight system is implemented as a Python-based web application following a modular, service-oriented architecture. The implementation prioritizes local-first execution, enabling developers to run the entire system—including database, web server, and AI analysis—on a single development machine without external cloud dependencies. The system is built using FastAPI as the web framework, which provides both REST API endpoints and server-rendered UI templates through Jinja2, creating a unified application that serves both programmatic and human interfaces.

The implementation follows a clear separation of concerns, with distinct service layers for scraping, change detection, AI analysis, and validation. All components interact through well-defined interfaces, primarily via the database (PostgreSQL) and direct service method calls. The system uses SQLAlchemy as an Object-Relational Mapping (ORM) layer, which abstracts database operations and enables type-safe model definitions. Configuration is managed through Pydantic Settings, supporting environment variables and `.env` files for flexible deployment across different environments. The local LLM integration via Ollama ensures that all AI processing occurs on-device, maintaining data privacy and eliminating external API dependencies. The UI supports running the complete monitoring pipeline through a web interface and allows users to validate AI-generated summaries and classifications, creating a complete workflow from source monitoring to human validation.

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

**Local Execution**: The application runs locally using `uvicorn src.offsight.main:app --reload` with a Python virtual environment. PostgreSQL runs as a local service, and Ollama operates on `http://localhost:11434`. Detailed setup instructions are provided in the README.md file.

## Project Structure (Repository Overview)

The project follows a standard Python package structure with clear separation between API, services, models, and UI components:

```
offsight-regulatory-intelligence/
├── src/offsight/
│   ├── api/              # REST API endpoints (changes, sources, validation, pipeline)
│   ├── core/             # Core utilities (config, db, init scripts, seeding)
│   ├── models/           # SQLAlchemy ORM models (Source, RegulationDocument, etc.)
│   ├── services/         # Business logic services (scraper, change detection, AI, validation)
│   ├── ui/               # UI routes and Jinja2 templates
│   └── main.py           # FastAPI application entry point
├── tests/                # Test files (pytest)
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

**Key Locations**:
- **UI Routes**: `src/offsight/ui/routes.py` - Handles all web UI endpoints including pipeline execution
- **Services**: `src/offsight/services/` - Contains `pipeline_service.py`, `scraper_service.py`, `change_detection_service.py`, `ai_service.py`, `validation_service.py`
- **Models**: `src/offsight/models/` - SQLAlchemy models defining database schema and relationships
- **Core Scripts**: `src/offsight/core/` - Database initialization (`init_db.py`), seeding scripts, and configuration

## Pipeline Orchestration

The monitoring pipeline is orchestrated by the `run_pipeline()` function in `src/offsight/services/pipeline_service.py`. This function coordinates all pipeline steps in a sequential, fault-tolerant manner, executing the end-to-end workflow: seeding data sources, scraping regulatory content, detecting changes between document versions, and performing AI analysis on detected changes.

### Conditional Step Execution

Each pipeline step is controlled by a boolean flag passed to `run_pipeline()`, allowing steps to be conditionally enabled or disabled. The function executes eight distinct steps in a fixed order: (1) database initialization, (2) database reset (with confirmation token), (3) seeding requirement categories, (4) seeding demo sources, (5) Ollama connectivity testing, (6) scraping enabled sources, (7) change detection, and (8) AI analysis.

**Code Snippet: Pipeline Orchestration Core Logic**

*Snippet shortened for clarity. Shows conditional step execution, error handling, and result aggregation.*

```python
# File: src/offsight/services/pipeline_service.py

def run_pipeline(
    *,
    init_db_flag: bool = False,
    reset_db_flag: bool = False,
    reset_confirm_token: str = "",
    seed_sources: bool = True,
    scrape: bool = True,
    detect: bool = True,
    run_ai: bool = True,
    ai_limit: int = 5,
    test_ollama: bool = True,
) -> PipelineResult:
    """
    Execute the complete monitoring pipeline with configurable steps.
    """
    result = PipelineResult()  # Initialize result container
    
    # Validate reset confirmation (safety check)
    if reset_db_flag and reset_confirm_token != "CONFIRM":
        result.steps.append(
            PipelineStepResult(name="Reset DB", status="error", 
                              message="Reset requires confirmation token 'CONFIRM'")
        )
        return result  # Early return if validation fails
    
    db = SessionLocal()  # Create database session
    try:
        # Step 6: Scrape enabled sources (conditional)
        if scrape:
            try:
                scraper = ScraperService()
                sources = db.query(Source).filter(Source.enabled.is_(True)).all()
                
                if not sources:
                    result.steps.append(
                        PipelineStepResult(name="Scrape", status="warning",
                                          message="No enabled sources found")
                    )
                else:
                    new_docs_count = 0
                    # Per-source error handling (NFR2: fault tolerance)
                    for source in sources:
                        try:
                            new_doc = scraper.fetch_and_store_if_changed(source.id, db)
                            if new_doc:
                                new_docs_count += 1
                        except Exception as e:
                            # Log warning, continue with next source
                            result.warnings.append(f"Error scraping source {source.id}: {str(e)}")
                            continue  # Continue pipeline despite individual failure
                    
                    result.steps.append(
                        PipelineStepResult(
                            name="Scrape",
                            status="success",
                            message=f"Scraped {len(sources)} source(s), {new_docs_count} new document(s)",
                            counts={"sources_scraped": len(sources), "new_documents": new_docs_count}
                        )
                    )
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(name="Scrape", status="error", message=f"Failed: {str(e)}")
                )
                return result  # Stop pipeline on critical failure
        
        # Step 8: AI analysis (conditional)
        if run_ai:
            try:
                settings = get_settings()
                ai_service = AiService(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    timeout=300,
                )
                
                # Count pending changes before processing
                pending_before = (
                    db.query(RegulationChange)
                    .filter(
                        RegulationChange.status == "pending",
                        RegulationChange.ai_summary.is_(None),
                    )
                    .count()
                )
                
                if pending_before == 0:
                    result.steps.append(
                        PipelineStepResult(
                            name="AI Analysis",
                            status="warning",
                            message="No pending changes to analyze",
                            counts={"changes_processed": 0},
                        )
                    )
                else:
                    try:
                        # Process up to ai_limit changes
                        updated_changes = ai_service.analyse_pending_changes(db, limit=ai_limit)
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="success",
                                message=f"AI analysis complete. {len(updated_changes)} change(s) processed",
                                counts={"changes_processed": len(updated_changes)}
                            )
                        )
                    except AiServiceError as e:
                        # AI-specific error handling (NFR2: log and continue)
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="error",
                                message=f"AI service error: {str(e)}",
                            )
                        )
                        result.warnings.append("AI analysis failed. Is Ollama running?")
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(
                        name="AI Analysis",
                        status="error",
                        message=f"AI analysis failed: {str(e)}",
                    )
                )
        
        # Aggregate totals across all steps
        result.totals = {
            "sources_seeded": sum(
                step.counts.get("created", 0) + step.counts.get("updated", 0)
                for step in result.steps
                if step.name == "Seed Sources"
            ),
            "sources_scraped": sum(
                step.counts.get("sources_scraped", 0) for step in result.steps if step.name == "Scrape"
            ),
            "new_documents": sum(
                step.counts.get("new_documents", 0) for step in result.steps if step.name == "Scrape"
            ),
            "new_changes": sum(
                step.counts.get("new_changes", 0) for step in result.steps if step.name == "Detect Changes"
            ),
            "changes_ai_processed": sum(
                step.counts.get("changes_processed", 0) for step in result.steps if step.name == "AI Analysis"
            ),
        }
    except Exception as e:
        result.steps.append(
            PipelineStepResult(name="Pipeline", status="error", message=f"Unexpected error: {str(e)}")
        )
    finally:
        db.close()  # Always close database session
    
    return result  # Return complete result with all step outcomes
```

**Explanation**: The function uses boolean flags to conditionally execute steps. Each step is wrapped in try-except blocks that capture exceptions and convert them into `PipelineStepResult` objects. Critical steps (database operations) return early on failure, while non-critical steps (scraping, AI analysis) log warnings and continue execution. Per-source error handling in the scraping step ensures that one source failure does not stop the entire pipeline (NFR2). Results are collected in a `PipelineResult` object containing step outcomes, aggregated totals, and warnings.

## UI Pipeline Execution and PRG Pattern

The UI layer provides a web-based interface for executing the monitoring pipeline through `GET /ui/run` and `POST /ui/run` handlers in `src/offsight/ui/routes.py`. The implementation follows the Post-Redirect-Get (PRG) pattern to prevent duplicate pipeline executions when users refresh the results page.

**Code Snippet: PRG Pattern Implementation**

```python
# File: src/offsight/ui/routes.py

@router.post("/run", tags=["ui"])
def run_pipeline_ui_post(
    request: Request,
    seed_sources: str | None = Form(None),
    scrape: str | None = Form(None),
    detect: str | None = Form(None),
    run_ai: str | None = Form(None),
    ai_limit: int = Form(5),
    # ... other form fields
):
    """
    Handle pipeline run form submission (PRG pattern).
    """
    try:
        # Convert checkbox strings to booleans (HTML checkboxes send "true" or nothing)
        seed_sources_bool = seed_sources == "true" if seed_sources else True
        scrape_bool = scrape == "true" if scrape else True
        detect_bool = detect == "true" if detect else True
        run_ai_bool = run_ai == "true" if run_ai else True
        
        # Execute pipeline with converted boolean flags
        result = run_pipeline(
            seed_sources=seed_sources_bool,
            scrape=scrape_bool,
            detect=detect_bool,
            run_ai=run_ai_bool,
            ai_limit=ai_limit,
        )
        
        # PRG Pattern: Encode result in redirect URL (base64 JSON)
        import json
        import base64
        result_json = json.dumps(result.to_dict())  # Serialize to JSON
        result_encoded = base64.b64encode(result_json.encode()).decode()  # Base64 encode
        
        # Redirect to GET endpoint with encoded result (prevents duplicate submissions)
        return RedirectResponse(
            url=f"/ui/run?result={result_encoded}",
            status_code=status.HTTP_303_SEE_OTHER,  # 303 See Other (PRG standard)
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/ui/run?error={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

@router.get("/run", response_class=HTMLResponse, tags=["ui"])
def run_pipeline_ui(request: Request, result: str | None = Query(None)):
    """
    Render the pipeline runner page with optional result or error.
    """
    pipeline_result = None
    if result:
        try:
            import json
            import base64
            result_json = base64.b64decode(result.encode()).decode()  # Decode base64
            pipeline_result = json.loads(result_json)  # Deserialize JSON
        except Exception:
            pipeline_result = None
    
    return templates.TemplateResponse("run_pipeline.html", {
        "request": request,
        "pipeline_result": pipeline_result,
    })
```

**Explanation**: The POST handler converts HTML form checkbox values to boolean flags, executes the pipeline, serializes the result to JSON, base64-encodes it, and redirects to the GET endpoint with the encoded result in the query parameter. The GET handler decodes and deserializes the result for display. This pattern ensures that refreshing the results page does not re-execute the pipeline, and execution results are preserved across page loads. This matches the SSD behavior shown in Figure X (System Sequence Diagram).

## Scraping and Document Versioning

The scraping service (`ScraperService` in `src/offsight/services/scraper_service.py`) retrieves content from regulatory sources, extracts text from HTML, and stores new document versions only when content changes. The service uses SHA256 content hashing to detect changes and prevent duplicate storage, ensuring idempotency and supporting traceability.

**Code Snippet: Content Hashing and Versioning Logic**

*Snippet shortened for clarity. Shows hash computation, duplicate detection, and version increment logic.*

```python
# File: src/offsight/services/scraper_service.py

def fetch_and_store_if_changed(self, source_id: int, db: Session) -> RegulationDocument | None:
    """
    Fetch content from a source and store a new document version if content changed.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    # Fetch raw content from URL
    content = self.fetch_raw_content(source)  # HTTP GET + BeautifulSoup parsing
    if content is None:
        return None  # Return None on fetch failure
    
    # Compute content hash (SHA256)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    # Get the latest document for this source
    latest_doc = (
        db.query(RegulationDocument)
        .filter(RegulationDocument.source_id == source_id)
        .order_by(desc(RegulationDocument.retrieved_at))
        .first()
    )
    
    # Check if content has changed - prevent duplicate storage
    if latest_doc and latest_doc.content_hash == content_hash:
        # Content unchanged - DO NOT store a new document
        print("No changes detected; skipping storage.")
        return None  # Idempotent: same content = no new version
    
    # Determine next version number (increment from highest numeric version)
    all_docs = db.query(RegulationDocument).filter(
        RegulationDocument.source_id == source_id
    ).all()
    
    if all_docs:
        # Find the highest numeric version
        max_version_num = 0
        for doc in all_docs:
            try:
                version_num = int(doc.version)
                if version_num > max_version_num:
                    max_version_num = version_num
            except ValueError:
                # Skip non-numeric versions for max calculation
                pass
        
        if max_version_num > 0:
            next_version = str(max_version_num + 1)
        else:
            # No numeric versions found, use latest doc's version + suffix
            if latest_doc:
                next_version = f"{latest_doc.version}.1"
            else:
                next_version = "1"
    else:
        next_version = "1"  # First document for this source
    
    # Create new document version
    new_doc = RegulationDocument(
        source_id=source_id,
        version=next_version,
        content=content,
        content_hash=content_hash,  # Store hash for future comparisons
        retrieved_at=datetime.now(UTC),
        url=source.url,  # Preserve source URL for traceability
    )
    
    db.add(new_doc)
    db.commit()
    return new_doc
```

**Explanation**: The method fetches content from the source URL using HTTP GET, parses HTML with BeautifulSoup to extract text, and computes a SHA256 hash of the content. It compares this hash with the latest stored document's hash. If hashes match, the method returns `None` without storing a new version, ensuring idempotency. If hashes differ, it determines the next version number (incrementing from the highest numeric version) and stores a new `RegulationDocument` with the content, hash, retrieval timestamp, and source URL. This hashing approach supports traceability (requirement 8) by ensuring each unique content version is stored exactly once, and enables efficient change detection without storing duplicate content.

## Change Detection and Diff Generation

The change detection service (`ChangeDetectionService` in `src/offsight/services/change_detection_service.py`) compares consecutive document versions for each source, computes textual diffs using Python's `difflib` library, and creates `RegulationChange` records when non-empty differences are detected.

**Code Snippet: Change Detection and Diff Computation**

```python
# File: src/offsight/services/change_detection_service.py

def detect_changes_for_source(self, source_id: int, db: Session) -> list[RegulationChange]:
    """
    Detect changes between consecutive document versions for a source.
    """
    documents = self.get_ordered_documents(source_id, db)  # Get chronologically ordered docs
    
    if len(documents) < 2:
        return []  # Need at least 2 documents to detect changes
    
    created_changes: list[RegulationChange] = []
    
    # Iterate through consecutive pairs
    for i in range(len(documents) - 1):
        previous_doc = documents[i]
        current_doc = documents[i + 1]
        
        # Check if a RegulationChange already exists for this pair (prevent duplicates)
        existing_change = db.query(RegulationChange).filter(
            and_(
                RegulationChange.previous_document_id == previous_doc.id,
                RegulationChange.new_document_id == current_doc.id,
            )
        ).first()
        
        if existing_change:
            continue  # Skip if change already detected
        
        # Compute textual diff using difflib
        previous_lines = previous_doc.content.splitlines(keepends=True)
        current_lines = current_doc.content.splitlines(keepends=True)
        
        diff_lines = difflib.unified_diff(
            previous_lines,
            current_lines,
            fromfile=f"version_{previous_doc.version}",
            tofile=f"version_{current_doc.version}",
            lineterm="",
        )
        
        diff_content = "".join(diff_lines)
        
        # Skip if diff is empty or only whitespace (requirement 11)
        if not diff_content or diff_content.strip() == "":
            continue  # No real change detected
        
        # Create new RegulationChange
        new_change = RegulationChange(
            previous_document_id=previous_doc.id,  # Link to previous version
            new_document_id=current_doc.id,         # Link to new version
            diff_content=diff_content,               # Store computed diff
            detected_at=datetime.now(UTC),          # Detection timestamp
            status="pending",                       # Initial status
        )
        
        db.add(new_change)
        created_changes.append(new_change)
    
    if created_changes:
        db.commit()  # Commit all changes at once
    
    return created_changes
```

**Explanation**: The method retrieves all documents for a source in chronological order, iterates through consecutive document pairs, and checks if a change record already exists (preventing duplicates). For each pair, it computes a unified diff using `difflib.unified_diff()`, which produces a line-by-line comparison showing additions and deletions. If the diff is empty or contains only whitespace, no change record is created (requirement 11). Otherwise, a new `RegulationChange` is created with foreign key references to both document versions (`previous_document_id`, `new_document_id`), the computed diff content, and a detection timestamp. This ensures traceability (requirement 9, 10) by linking changes to specific document versions and preserving the exact differences detected.

## AI-Assisted Analysis (Ollama Integration)

The AI service (`AiService` in `src/offsight/services/ai_service.py`) communicates with the local Ollama LLM via HTTP API to generate summaries and classify regulatory changes into predefined requirement classes. The service handles prompt construction, API calls, response parsing, and category normalization to ensure consistency with the fixed taxonomy.

**Code Snippet: Ollama API Integration and Error Handling**

*Snippet shortened for clarity. Shows API call structure, response parsing, and per-change error handling.*

```python
# File: src/offsight/services/ai_service.py

def analyse_change_text(self, change_text: str) -> dict:
    """
    Analyze change text using Ollama LLM and return structured results.
    """
    # Build the prompt with change text and requirement class constraints
    prompt = self._build_prompt(change_text)
    
    # Call Ollama API
    try:
        response = self._call_ollama(prompt)  # HTTP POST to Ollama API
    except httpx.HTTPError as e:
        raise AiServiceError(f"Failed to call Ollama API: {e}") from e
    
    # Parse JSON response
    try:
        result = self._parse_response(response)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise AiServiceError(f"Failed to parse AI response: {e}") from e
    
    # Validate and normalize requirement class
    result["requirement_class"] = self._normalize_category(
        result.get("requirement_class", "Other / unclear")
    )
    
    return result  # Returns: {"summary": str, "requirement_class": str, "confidence": float}

def _call_ollama(self, prompt: str) -> str:
    """
    Call Ollama API to generate response.
    """
    url = f"{self.base_url}/api/generate"
    payload = {
        "model": self.model,
        "prompt": prompt,
        "stream": False,
        "format": "json",  # Request JSON response
    }
    
    with httpx.Client(timeout=self.timeout) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Ollama /api/generate returns {"response": "..."} or just the text
        if "response" in result:
            return result["response"]
        elif isinstance(result, str):
            return result
        else:
            # Fallback: try to extract text from response
            return json.dumps(result)

def analyse_pending_changes(self, db: Session, limit: int = 10) -> list[RegulationChange]:
    """
    Analyze pending changes using Ollama.
    """
    # Get pending changes (status='pending' AND ai_summary is NULL)
    pending_changes = (
        db.query(RegulationChange)
        .filter(
            RegulationChange.status == "pending",
            RegulationChange.ai_summary.is_(None),
        )
        .limit(limit)
        .all()
    )
    
    updated_changes = []
    for change in pending_changes:
        try:
            # Analyze and update change (calls analyse_and_update_change internally)
            updated_change = self.analyse_and_update_change(change, db)
            updated_changes.append(updated_change)
        except AiServiceError as e:
            # Log error but continue with next change (NFR2: fault tolerance)
            print(f"[WARN] Failed to analyze change ID {change.id}: {e}")
            continue  # Continue processing other changes
    
    return updated_changes
```

**Explanation**: The service constructs a prompt that includes the change diff text and constrains the AI to return one of seven predefined requirement classes. It sends an HTTP POST request to Ollama's `/api/generate` endpoint with JSON format requested. The response is parsed, validated, and the requirement class is normalized to match exact category names. If Ollama is unreachable or returns invalid responses, `AiServiceError` exceptions are raised. In `analyse_pending_changes()`, per-change error handling ensures that one change's AI analysis failure does not stop processing of other changes (NFR2). The service updates each change with `ai_summary`, `category_id`, and sets status to `"ai_suggested"` (requirement 14), supporting the workflow from pending to AI-suggested status.

## Human Validation and Audit Trail

The validation service (`validation_service.py`) and API endpoint (`api/validation.py`) handle human validation of AI-generated summaries and classifications. When a user validates a change, a `ValidationRecord` is created with the validator identity, timestamp, final summary, final category, and validation decision. The `RegulationChange` status is updated to reflect the validation outcome (validated, corrected, or rejected).

**Code Snippet: Validation Processing and Audit Trail**

```python
# File: src/offsight/services/validation_service.py

def process_validation(
    change: RegulationChange,
    decision: str,  # "approved", "corrected", or "rejected"
    user_id: int | None,
    final_summary: str | None,
    final_category: str | None,
    notes: str | None,
    db: Session,
) -> tuple[ValidationRecord, str, str | None]:
    """
    Process a validation decision and create ValidationRecord.
    """
    # Determine user (use demo user if not provided)
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = get_or_create_demo_user(db)
    else:
        user = get_or_create_demo_user(db)
    
    # Determine final summary and category based on decision
    if decision == "approved":
        # Accept AI suggestion as-is
        final_summary = change.ai_summary
        final_category_name = change.category.name if change.category else None
        final_category_id = change.category_id
    
    elif decision == "corrected":
        # Human provided corrections (requirement 15)
        if not final_summary or not final_category:
            raise ValueError("final_summary and final_category required for 'corrected'")
        
        category = get_or_create_category(final_category, db)
        final_category_name = category.name
        final_category_id = category.id
    
    elif decision == "rejected":
        # AI suggestion rejected
        final_summary = final_summary or "Rejected"
        category = get_or_create_category(final_category or "other", db)
        final_category_name = category.name
        final_category_id = category.id
    
    # Create ValidationRecord (requirement 16: audit trail)
    validation_record = ValidationRecord(
        change_id=change.id,                    # Link to change
        user_id=user.id,                         # Validator identity
        validated_summary=final_summary,         # Final summary
        validated_category_id=final_category_id, # Final category
        validation_status=decision,              # "approved", "corrected", or "rejected"
        notes=notes,                             # Optional notes
        validated_at=datetime.now(UTC),         # Timestamp (requirement 16)
    )
    
    db.add(validation_record)
    
    # Update RegulationChange status (requirement 17)
    if decision == "approved":
        change.status = "validated"
    elif decision == "corrected":
        change.status = "corrected"
    elif decision == "rejected":
        change.status = "rejected"
    
    # Update change with final values if corrected/rejected
    if decision in ["corrected", "rejected"]:
        change.ai_summary = final_summary
        change.category_id = final_category_id
    
    return validation_record, final_summary, final_category_name
```

**Explanation**: The function processes three validation decisions: "approved" (accepts AI suggestion), "corrected" (human provides new summary/category), and "rejected" (AI suggestion is rejected). For each decision, it creates a `ValidationRecord` containing the validator identity (`user_id`), timestamp (`validated_at`), final summary, final category, validation status, and optional notes (requirement 16). The `RegulationChange` status is updated to "validated", "corrected", or "rejected" (requirement 17). The separate `ValidationRecord` table ensures that validation history is preserved independently of the change record, supporting auditability and allowing multiple validations per change if needed. Foreign key relationships (`change_id`, `user_id`, `validated_category_id`) maintain traceability between changes, validators, and categories.

## Persistence Model Notes

The system uses SQLAlchemy ORM models to define the database schema and relationships. Key models include `Source`, `RegulationDocument`, `RegulationChange`, `Category`, `User`, and `ValidationRecord`. Foreign key relationships ensure referential integrity and support traceability requirements.

**Code Snippet: RegulationChange Model with Relationships**

```python
# File: src/offsight/models/regulation_change.py

class RegulationChange(Base):
    """
    RegulationChange model for detected changes between document versions.
    """
    __tablename__ = "regulation_changes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    previous_document_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_documents.id"), nullable=False
    )
    new_document_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_documents.id"), nullable=False
    )
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    # Relationships (SQLAlchemy)
    previous_document: Mapped["RegulationDocument"] = relationship(
        "RegulationDocument",
        foreign_keys=[previous_document_id],
        back_populates="previous_changes",
    )
    new_document: Mapped["RegulationDocument"] = relationship(
        "RegulationDocument",
        foreign_keys=[new_document_id],
        back_populates="new_changes",
    )
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="regulation_changes"
    )
    validation_records: Mapped[list["ValidationRecord"]] = relationship(
        "ValidationRecord", back_populates="regulation_change"
    )
```

**Explanation**: The `RegulationChange` model includes foreign keys to `RegulationDocument` (both previous and new versions), `Category`, and has a one-to-many relationship with `ValidationRecord`. These relationships ensure that changes are traceable to their source documents (via `RegulationDocument.source_id`), categories, and validation history. The `detected_at` timestamp and `status` field support workflow tracking from pending → ai_suggested → validated/corrected/rejected. SQLAlchemy relationships enable efficient querying with automatic joins, supporting requirement 9 (traceability) by maintaining links between sources, documents, changes, and validations.

## Testing and Reliability Notes

The system uses `pytest` for unit and integration testing. Test files are located in the `tests/` directory and include:

- `test_health.py`: Tests the health check endpoint
- `test_sources_api.py`: Tests source management API endpoints
- `test_change_detection_service.py`: Tests change detection logic
- `test_ai_service_mocked.py`: Tests AI service with mocked Ollama responses (avoids real API calls)
- `test_pipeline_api.py`: Tests pipeline API endpoint with mocked services

**Testing Approach**: External dependencies (Ollama API, HTTP requests to regulatory sources) are mocked using `unittest.mock.patch` to ensure tests run without network dependencies and to avoid rate limiting. The AI service tests use mocked Ollama responses to validate prompt construction, response parsing, and category normalization without requiring a running Ollama instance. Database operations in tests use the same SQLAlchemy session factory, but tests should use test databases or transaction rollbacks to avoid polluting development data.

**Running Tests**: Tests are executed using `PYTHONPATH=src pytest` from the project root. The test suite validates core functionality including change detection logic, AI response parsing, and API endpoint behavior, ensuring that the system meets reliability requirements (NFR2) through fault-tolerant error handling.

## Summary of Implementation Mapped to Requirements

The following table maps implemented features to functional and non-functional requirements:

| Feature | Requirements Covered |
|---------|---------------------|
| Source registry and management UI | FR1, FR2, FR3 |
| Content retrieval and versioning with hashing | FR4, FR5, FR6, FR7, FR8 |
| Change detection with diff computation | FR9, FR10, FR11 (Note: FR11 refers to empty diff filtering) |
| AI summarisation and classification | FR12, FR13, FR14 |
| Human validation and audit trail | FR15, FR16, FR17 |
| Pipeline execution UI | FR20, FR22 |
| Database initialization and reset (with confirmation) | FR21 |
| Change list and detail views | FR18, FR19 |
| Local-first execution (FastAPI + PostgreSQL + Ollama) | NFR1 |
| Fault tolerance (per-source/per-change error handling) | NFR2 |
| Traceability (foreign keys, timestamps, relationships) | NFR3 |
| Modular architecture (separate services) | NFR4 |
| Web UI for non-technical users | NFR5 |
| Public sources only (no confidential data) | NFR6 |
| Scraping limitations awareness | NFR7 |

**Key Implementation Highlights**:
- **Pipeline Orchestration**: Conditional step execution with fault-tolerant error handling ensures partial failures do not crash the entire pipeline (NFR2).
- **Content Hashing**: SHA256 hashing prevents duplicate storage and enables efficient change detection, supporting idempotency and traceability (FR6, FR7, FR8).
- **Diff Computation**: `difflib.unified_diff()` generates textual diffs, with empty/whitespace-only diffs filtered out (FR10, FR11).
- **AI Integration**: Ollama HTTP API integration with per-change error handling ensures pipeline continues even if some AI analyses fail (FR12, FR13, FR14, NFR2).
- **Validation Audit Trail**: Separate `ValidationRecord` table preserves validation history with timestamps and validator identity (FR15, FR16, FR17, NFR3).
- **PRG Pattern**: Post-Redirect-Get implementation prevents duplicate pipeline executions and preserves results across page refreshes (FR20, FR22).

