# Pipeline Orchestration Code Snippet

## File Paths

- **Main Orchestrator**: `src/offsight/services/pipeline_service.py` (function: `run_pipeline`, lines 134-559)
- **UI Route Handler**: `src/offsight/ui/routes.py` (function: `run_pipeline_ui_post`, lines 489-543)
- **Result Classes**: `src/offsight/services/pipeline_service.py` (classes: `PipelineStepResult`, `PipelineResult`, lines 30-99)

## Annotated Code Snippet

### Core Orchestration Function

```python
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
    result = PipelineResult()  # Initialize result container for all steps
    
    # Validate reset confirmation (safety check)
    if reset_db_flag and reset_confirm_token != "CONFIRM":
        result.steps.append(
            PipelineStepResult(
                name="Reset DB",
                status="error",
                message="Reset requires confirmation token 'CONFIRM'",
            )
        )
        return result  # Early return if validation fails
    
    db = SessionLocal()  # Create database session for all steps
    try:
        # Step 1: Initialize database schema (conditional)
        if init_db_flag:
            try:
                Base.metadata.create_all(bind=engine)  # Create all tables
                result.steps.append(
                    PipelineStepResult(name="Init DB", status="success", message="Database tables created/verified")
                )
            except Exception as e:
                # Error handling: capture error, add to results, return early
                result.steps.append(
                    PipelineStepResult(name="Init DB", status="error", message=f"Failed: {str(e)}")
                )
                return result  # Stop pipeline on critical DB init failure
        
        # Step 2: Reset database (conditional, requires confirmation)
        if reset_db_flag:
            try:
                # Delete all application data (preserves schema)
                counts: dict[str, int] = {}
                for model, label in [
                    (ValidationRecord, "ValidationRecord"),
                    (RegulationChange, "RegulationChange"),
                    (RegulationDocument, "RegulationDocument"),
                    (Category, "Category"),
                    (Source, "Source"),
                    (User, "User"),
                ]:
                    delete_result = db.execute(delete(model))
                    counts[label] = delete_result.rowcount or 0
                
                db.commit()  # Commit transaction
                total_deleted = sum(counts.values())
                result.steps.append(
                    PipelineStepResult(
                        name="Reset DB",
                        status="success",
                        message=f"Database reset complete. {total_deleted} rows deleted.",
                        counts=counts,  # Store metrics for reporting
                    )
                )
            except Exception as e:
                db.rollback()  # Rollback on error
                result.steps.append(
                    PipelineStepResult(name="Reset DB", status="error", message=f"Failed: {str(e)}")
                )
                return result  # Stop pipeline on reset failure
        
        # Step 3: Seed requirement categories (runs if seed_sources=True)
        if seed_sources:
            try:
                seed_requirement_categories(db)  # Upsert predefined categories
                db.commit()
                result.steps.append(
                    PipelineStepResult(name="Seed Categories", status="success", message="Requirement categories seeded")
                )
            except Exception as e:
                db.rollback()
                result.steps.append(
                    PipelineStepResult(name="Seed Categories", status="error", message=f"Failed: {str(e)}")
                )
                return result  # Stop pipeline on category seeding failure
        
        # Step 4: Seed demo sources (runs if seed_sources=True)
        if seed_sources:
            try:
                settings = get_settings()
                sources_created = 0
                sources_updated = 0
                
                # Upsert primary demo source (GitHub Pages)
                existing = db.query(Source).filter(Source.url == settings.demo_source_url).first()
                if existing:
                    # Update existing source
                    existing.name = "OffSight Demo Regulation (GitHub Pages)"
                    existing.enabled = True
                    sources_updated += 1
                else:
                    # Create new source
                    new_source = Source(name="...", url=settings.demo_source_url, enabled=True)
                    db.add(new_source)
                    sources_created += 1
                
                # Upsert additional sources (disabled by default)
                # ... (similar upsert logic for extra sources)
                
                db.commit()
                result.steps.append(
                    PipelineStepResult(
                        name="Seed Sources",
                        status="success",
                        message=f"Sources seeded: {sources_created} created, {sources_updated} updated",
                        counts={"created": sources_created, "updated": sources_updated},  # Store metrics
                    )
                )
            except Exception as e:
                db.rollback()
                result.steps.append(
                    PipelineStepResult(name="Seed Sources", status="error", message=f"Failed: {str(e)}")
                )
                return result
        
        # Step 5: Test Ollama connectivity (conditional, non-blocking)
        if test_ollama:
            is_connected, message = test_ollama_connectivity()  # HTTP GET to Ollama API
            result.steps.append(
                PipelineStepResult(
                    name="Test Ollama",
                    status="success" if is_connected else "warning",  # Warning, not error
                    message=message,
                )
            )
            if not is_connected:
                result.warnings.append("Ollama is not accessible. AI analysis will fail.")  # Log warning
        
        # Step 6: Scrape enabled sources (conditional)
        if scrape:
            try:
                scraper = ScraperService()
                sources = db.query(Source).filter(Source.enabled.is_(True)).all()  # Get enabled sources only
                
                if not sources:
                    result.steps.append(
                        PipelineStepResult(
                            name="Scrape",
                            status="warning",  # Warning, not error (no sources is acceptable)
                            message="No enabled sources found to scrape",
                            counts={"sources_scraped": 0, "new_documents": 0},
                        )
                    )
                else:
                    new_docs_count = 0
                    # Loop through sources with per-source error handling (NFR4: fault tolerance)
                    for source in sources:
                        try:
                            new_doc = scraper.fetch_and_store_if_changed(source.id, db)
                            if new_doc:
                                new_docs_count += 1
                        except Exception as e:
                            # Per-source error handling: log warning, continue with next source
                            result.warnings.append(f"Error scraping source {source.id}: {str(e)}")
                            continue  # Continue pipeline despite individual source failure
                    
                    result.steps.append(
                        PipelineStepResult(
                            name="Scrape",
                            status="success",
                            message=f"Scraped {len(sources)} source(s), {new_docs_count} new document(s) stored",
                            counts={"sources_scraped": len(sources), "new_documents": new_docs_count},
                        )
                    )
            except Exception as e:
                # Only catch unexpected errors (e.g., DB connection failure)
                result.steps.append(
                    PipelineStepResult(name="Scrape", status="error", message=f"Scraping failed: {str(e)}")
                )
                return result  # Stop pipeline on critical scraping failure
        
        # Step 7: Detect changes between document versions (conditional)
        if detect:
            try:
                change_service = ChangeDetectionService()
                sources = db.query(Source).filter(Source.enabled.is_(True)).all()
                
                if not sources:
                    result.steps.append(
                        PipelineStepResult(
                            name="Detect Changes",
                            status="warning",
                            message="No enabled sources found for change detection",
                            counts={"new_changes": 0},
                        )
                    )
                else:
                    total_changes = 0
                    # Process each source's document versions
                    for source in sources:
                        created_changes = change_service.detect_changes_for_source(source.id, db)
                        total_changes += len(created_changes)
                    
                    result.steps.append(
                        PipelineStepResult(
                            name="Detect Changes",
                            status="success",
                            message=f"Change detection complete. {total_changes} new change(s) created",
                            counts={"new_changes": total_changes},  # Store count for reporting
                        )
                    )
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(name="Detect Changes", status="error", message=f"Failed: {str(e)}")
                )
                return result
        
        # Step 8: AI analysis of pending changes (conditional)
        if run_ai:
            try:
                settings = get_settings()
                ai_service = AiService(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    timeout=300,  # 5-minute timeout per change
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
                        # Process up to ai_limit changes (NFR2: performance limit)
                        updated_changes = ai_service.analyse_pending_changes(db, limit=ai_limit)
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="success",
                                message=f"AI analysis complete. {len(updated_changes)} change(s) processed",
                                counts={"changes_processed": len(updated_changes)},
                            )
                        )
                    except AiServiceError as e:
                        # AI-specific error handling (NFR4: log and continue)
                        result.steps.append(
                            PipelineStepResult(
                                name="AI Analysis",
                                status="error",
                                message=f"AI service error: {str(e)}",
                            )
                        )
                        result.warnings.append("AI analysis failed. Is Ollama running?")  # Log warning
            except Exception as e:
                result.steps.append(
                    PipelineStepResult(name="AI Analysis", status="error", message=f"Failed: {str(e)}")
                )
        
        # Aggregate totals across all steps for summary reporting
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
        # Catch-all for unexpected errors
        result.steps.append(
            PipelineStepResult(name="Pipeline", status="error", message=f"Unexpected error: {str(e)}")
        )
    finally:
        db.close()  # Always close database session
    
    return result  # Return complete result with all step outcomes
```

### PRG Pattern Implementation (UI Route)

```python
@router.post("/run", tags=["ui"])
def run_pipeline_ui_post(
    request: Request,
    init_db: str | None = Form(None),
    reset_db: str | None = Form(None),
    reset_confirm_token: str = Form(""),
    seed_sources: str | None = Form(None),
    scrape: str | None = Form(None),
    detect: str | None = Form(None),
    run_ai: str | None = Form(None),
    ai_limit: int = Form(5),
    test_ollama: str | None = Form(None),
):
    """
    Handle pipeline run form submission (PRG pattern).
    """
    try:
        # Convert checkbox strings to booleans (HTML checkboxes send "true" or nothing)
        init_db_bool = init_db == "true" if init_db else False
        reset_db_bool = reset_db == "true" if reset_db else False
        seed_sources_bool = seed_sources == "true" if seed_sources else True  # Default True
        scrape_bool = scrape == "true" if scrape else True  # Default True
        detect_bool = detect == "true" if detect else True  # Default True
        run_ai_bool = run_ai == "true" if run_ai else True  # Default True
        test_ollama_bool = test_ollama == "true" if test_ollama else True  # Default True
        
        # Execute pipeline with converted boolean flags
        result = run_pipeline(
            init_db_flag=init_db_bool,
            reset_db_flag=reset_db_bool,
            reset_confirm_token=reset_confirm_token,
            seed_sources=seed_sources_bool,
            scrape=scrape_bool,
            detect=detect_bool,
            run_ai=run_ai_bool,
            ai_limit=ai_limit,
            test_ollama=test_ollama_bool,
        )
        
        # PRG Pattern: Encode result in redirect URL (base64 JSON)
        import json
        import base64
        result_json = json.dumps(result.to_dict())  # Serialize result to JSON
        result_encoded = base64.b64encode(result_json.encode()).decode()  # Base64 encode for URL
        
        # Redirect to GET endpoint with encoded result (prevents duplicate submissions)
        return RedirectResponse(
            url=f"/ui/run?result={result_encoded}",
            status_code=status.HTTP_303_SEE_OTHER,  # 303 See Other (PRG standard)
        )
    except Exception as e:
        # Error handling: redirect with error message
        return RedirectResponse(
            url=f"/ui/run?error={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
```

