# Requirements for OffSight™

This document defines the functional and non-functional requirements for OffSight™, an AI-powered regulatory intelligence system that monitors UK offshore wind regulations, detects changes, and provides actionable insights through AI summarisation and classification.

## Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| FR1 | Source registry | Configure one or more UK regulatory sources (e.g. URLs/APIs) to be monitored. |
| FR2 | Periodic retrieval | Periodically retrieve content from all configured sources and store raw content and metadata in the database. |
| FR3 | Version tracking | Detect when a document from a source has changed and store versioned snapshots. |
| FR4 | Change detection | Compute differences between the new and previous version of a document when a change is detected. |
| FR5 | AI summarisation | For each detected change, generate a short human-readable summary using a local LLM. |
| FR6 | Impact classification | For each detected change, classify its impact into one of a predefined set of requirement classes: Spatial constraints, Temporal constraints, Procedural obligations, Technical performance expectations, Operational restrictions, Evidence and reporting requirements, Other/unclear. |
| FR7 | Human validation | Allow a user to validate or correct the AI-generated summary and category, and store the validation result. |
| FR8 | Change overview UI | Present a list of detected changes with source, date, summary, category, and validation status, with basic filtering. |
| FR9 | Traceability | For each change, store references to the original URL/source, document versions, and detection time. |
| FR10 | Pipeline execution UI | Provide a web-based interface to execute the full monitoring pipeline (seed, scrape, detect, AI analysis) without requiring command-line access. |
| FR11 | Source management UI | Allow users to add, update, and enable/disable regulatory sources through a web interface. |

## Non-Functional Requirements

- **NFR1 – Local execution**: The system shall be deployable on a developer laptop using PostgreSQL and a locally hosted LLM via Ollama.
- **NFR2 – Performance**: For a batch of up to 20 changed documents, the system should be able to generate summaries and categories within a reasonable time (e.g. a few minutes), to be evaluated during testing.
- **NFR3 – Security**: Only publicly available regulatory sources are processed; no confidential internal documents are ingested.
- **NFR4 – Reliability**: Failures in scraping or AI summarisation must be logged and must not crash the entire pipeline.
- **NFR5 – Maintainability**: The system shall use a modular architecture where scraping, diffing, AI, and UI are separated into distinct components/modules.
- **NFR6 – Usability**: The UI shall present a clear list of changes and allow non-technical users to understand and filter results.

---

**Note**: This requirements document will be used later for test case design and traceability in the bachelor report.

