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

