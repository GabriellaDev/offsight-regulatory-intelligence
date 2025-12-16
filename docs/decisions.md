# Architecture Decision Records

_This document will record key architectural decisions for OffSight along with the reasoning behind it._

## ADR-011 – Handling Protected/Blocked Sources

- Some official sites (e.g., GOV.UK/HSE) may use bot protection or return non-standard HTTP codes when scraped.
- OffSight logs HTTP/network errors and skips the offending source instead of crashing the pipeline.
- For development and testing, we prefer scrape-friendly public guidance pages or locally mirrored text.
- Rationale: respect site policies, maintain pipeline resilience, and keep the focus on architecture and downstream processing rather than evading protections.

## ADR-012 – Change Detection Approach

- Change detection is implemented by comparing consecutive versions of RegulationDocument per source.
- RegulationChange rows store:
  - References to old and new documents (previous_document_id, new_document_id)
  - A text-based diff representation (using Python's difflib.unified_diff)
  - Detection timestamp and status ("pending" initially, before AI processing)
- Duplicate change records are prevented by checking for existing RegulationChange entries linking the same document pair.
- AI summarisation will use RegulationChange as input instead of re-computing diffs, keeping concerns separated.
- Rationale: store diffs once at detection time, enable efficient AI processing later, and maintain clear separation between change detection and AI analysis.

## ADR-013 – AI Analysis Using Local Ollama Model

- OffSight uses a local Ollama LLM instead of cloud-based AI services (e.g., OpenAI, Anthropic).
- Rationale: privacy and data control – regulatory documents may contain sensitive information, and local processing ensures data never leaves the developer's machine. This aligns with Siemens Gamesa's focus on data security and compliance.
- The AI service consumes RegulationChange.diff_content as input and produces:
  - A short natural-language summary (stored in ai_summary)
  - An impact category from a fixed taxonomy (grid_connection, safety_and_health, environment, certification_documentation, other)
- The AI response is constrained to JSON format for robust parsing and error handling.
- The service uses Ollama's `/api/generate` endpoint with JSON format enforcement.
- Future work could swap Ollama for another local LLM provider (e.g., LM Studio, vLLM) without changing the high-level architecture, as the AiService abstracts the HTTP API interaction.
- Rationale: local-first approach supports development and testing without external dependencies, reduces costs, and maintains full control over data processing.

## ADR-014 – Fixed Requirement Class Taxonomy

- OffSight uses a predefined, seeded requirement-class ontology based on UK authority mapping instead of free-form AI categories.
- The fixed taxonomy consists of seven requirement classes:
  - Spatial constraints
  - Temporal constraints
  - Procedural obligations
  - Technical performance expectations
  - Operational restrictions
  - Evidence and reporting requirements
  - Other / unclear
- Categories are seeded into the database via `seed_categories.py` and must match exactly (case-sensitive).
- The AI service is constrained to return exactly one of these category names, with robust normalization for minor variations (case-insensitive matching, handling of "&" vs "and", etc.).
- If the AI returns a category that cannot be mapped to the taxonomy, it defaults to "Other / unclear".
- Rationale: comparability across regulatory changes, auditability of classifications, and reduced category drift over time. This ensures consistent classification that aligns with UK regulatory authority frameworks.
- Consequences: AI must be explicitly instructed to return one of the allowed category names; unknown or unmappable categories are automatically assigned to "Other / unclear"; the taxonomy can be extended by seeding additional categories, but existing categories should remain stable for historical consistency.

