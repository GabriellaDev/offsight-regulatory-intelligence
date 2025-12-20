REQUIREMENTS
The requirements presented below are the result of an iterative refinement process rather than upfront user-story elicitation or prioritisation techniques such as MoSCoW. While such approaches are well suited to commissioned systems with clearly defined stakeholders and negotiated feature scope, OffSight™ was developed as an exploratory pilot without a single system owner or predefined backlog.
Initial requirements were therefore defined at a capability level based on business-layer analysis of regulatory monitoring as organisational work, structured around the core functions of sensing, interpretation, and institutionalisation. These capabilities were derived from empirical observation of monitoring practices during an internship, supported by interviews, document analysis, and process modelling techniques such as Work-as-Imagined vs Work-as-Done (WAI/WAD) and BPMN.
As the pilot workflow and technical feasibility were explored, capability-level requirements were progressively decomposed into concrete functional and non-functional system requirements, expressed in a “system shall” format consistent with IEEE-style requirement specification guidance. This ensured that requirements remain precise, testable, and implementation-oriented, while still reflecting the exploratory and process-driven nature of the project. The resulting requirements therefore represent system capabilities necessary to support the redesigned monitoring workflow within the bounded UK scope, rather than prioritised feature requests from end users.

FUNCTIONAL REQUIREMENTS

Source registry & scope management
FR1. The system shall allow creation of a monitored source including name, URL, description, and enabled/disabled status, to support scope changes without deleting historical data.
FR2. The system shall allow updating source metadata and enabling or disabling monitoring for a source.
FR3. The system shall present a list of all configured sources and allow filtering by enabled/disabled status.
Capture & versioning
FR4. The system shall retrieve content from each enabled source using its configured access method (scraping).
FR5. The system shall retrieve the timestamp, source URL, and content hash.
FR6. The system shall detect whether retrieved content differs from the previously stored version using content hashing.
FR7. The system shall store a new document version only when a content change is detected.
FR8. The system shall maintain traceability between each document version, its source, and its retrieval timestamp.
The system shall store the retrieved raw content together with metadata, including 
Change detection
FR9. The system shall compute a textual diff between consecutive document versions for a given source.
FR10. The system shall create a change record containing references to the previous and new document versions, the computed diff, and the detection timestamp.
FR11. The system shall not create a change record if the computed diff is empty or contains only whitespace.

AI-assisted analysis
FR12. The system shall generate a concise human-readable summary of each detected change using a locally hosted large language model (LLM).
FR13. The system shall assign each detected change to one category from a predefined taxonomy, with a fallback category for unclear cases (e.g. Other).
FR14. The system shall update the change status to indicate completion of AI-assisted analysis.
Human validation & audit trail
FR15. The system shall allow a user to approve, correct, or reject AI-generated summaries and classifications.
FR16. The system shall store a validation record including validator identity (or demo user), timestamp, final summary, final category, and optional notes.
FR17. The system shall update the change status to reflect the validation outcome (validated, corrected, or rejected).

UI & pipeline execution
FR18. The system shall provide a user interface to list detected changes with source, date, status, category, and summary, and allow basic filtering.
FR19. The system shall provide a detailed view for each change including document diff, AI output, and validation history.
FR20. The system shall provide a user interface to execute the monitoring pipeline steps (seeding, scraping, change detection, AI analysis).
FR21. The system shall support controlled maintenance operations (database initialisation and reset), accessible only through explicit confirmation to prevent accidental data loss.
FR22. The system shall present step-by-step execution results and error indicators for each pipeline run.
NON-FUNCTIONAL REQUIREMENTS 
The non-functional requirements below define quality constraints that must hold across all functional capabilities, with emphasis on local execution, traceability, and operational robustness.

NFR1. Local-first execution
System runs locally (FastAPI + PostgreSQL + locally hosted LLM Ollama) without cloud dependencies.
NFR2. Reliability and fault tolerance 
Failures in scraping, diffing, or AI analysis for one source or change shall not cause the entire pipeline to fail and shall be logged and reported.
NFR3. Traceability and auditability
All stored records shall preserve source URLs, timestamps, version links, and relationships between sources, documents, changes, and validations.
NFR4. Maintainability
The system architecture shall separate scraping, change detection, AI analysis, validation logic, and UI into distinct modules or services.
NFR5. Usability
A non-technical user shall be able to run the monitoring pipeline and validate changes through the UI without using command-line tools.
NFR6. Data boundary and security
The system shall process only publicly available regulatory information and shall not ingest confidential or proprietary internal documents.
NFR7. Scraping limitations awareness
The system shall acknowledge that certain authoritative sources (e.g., legislation.gov.uk) impose technical or legal scraping constraints, which may limit automated content retrieval in the pilot scope.
