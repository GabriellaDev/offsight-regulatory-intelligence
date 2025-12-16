"""
Change detection service for comparing document versions.

Handles detection of changes between consecutive RegulationDocument versions
and creates RegulationChange entries with textual diffs.
"""

import difflib
from datetime import UTC, datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from offsight.models.regulation_change import RegulationChange
from offsight.models.regulation_document import RegulationDocument


class ChangeDetectionService:
    """Service for detecting changes between document versions."""

    def get_ordered_documents(
        self, source_id: int, db: Session
    ) -> list[RegulationDocument]:
        """
        Return all RegulationDocument entries for the given source,
        ordered by version (or by retrieved_at if version is not numeric).

        Args:
            source_id: The ID of the Source to get documents for
            db: SQLAlchemy database session

        Returns:
            List of RegulationDocument entries ordered by version/retrieved_at
        """
        documents = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.source_id == source_id)
            .all()
        )

        # Try to sort by numeric version, fall back to retrieved_at
        def sort_key(doc: RegulationDocument) -> tuple[int, datetime]:
            try:
                version_num = int(doc.version)
            except ValueError:
                # If version is not numeric, use a large number and sort by retrieved_at
                version_num = 999999
            return (version_num, doc.retrieved_at)

        return sorted(documents, key=sort_key)

    def detect_changes_for_source(
        self, source_id: int, db: Session
    ) -> list[RegulationChange]:
        """
        For the given source, detect changes between consecutive document versions.

        - Load ordered documents.
        - For each pair of consecutive documents (previous, current):
          - Check if a RegulationChange already exists linking these two documents.
          - If not, compute a textual diff between previous.content and current.content
            (using difflib.unified_diff line-by-line).
          - Create a new RegulationChange with:
            - previous_document_id
            - new_document_id
            - diff_content (string)
            - detected_at (current UTC timestamp)
            - status = "pending"

        Args:
            source_id: The ID of the Source to detect changes for
            db: SQLAlchemy database session

        Returns:
            List of RegulationChange rows created in this run
        """
        documents = self.get_ordered_documents(source_id, db)

        if len(documents) < 2:
            # Need at least 2 documents to detect changes
            return []

        created_changes: list[RegulationChange] = []

        # Iterate through consecutive pairs
        for i in range(len(documents) - 1):
            previous_doc = documents[i]
            current_doc = documents[i + 1]

            # Check if a RegulationChange already exists for this pair
            existing_change = (
                db.query(RegulationChange)
                .filter(
                    and_(
                        RegulationChange.previous_document_id == previous_doc.id,
                        RegulationChange.new_document_id == current_doc.id,
                    )
                )
                .first()
            )

            if existing_change:
                # Skip if change already detected
                continue

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

            # Skip if diff is empty or only whitespace (no real change)
            if not diff_content or diff_content.strip() == "":
                continue

            # Create new RegulationChange
            new_change = RegulationChange(
                previous_document_id=previous_doc.id,
                new_document_id=current_doc.id,
                diff_content=diff_content,
                detected_at=datetime.now(UTC),
                status="pending",
            )

            db.add(new_change)
            created_changes.append(new_change)

        # Commit all changes at once
        if created_changes:
            db.commit()
            # Refresh all created changes to get their IDs
            for change in created_changes:
                db.refresh(change)

        return created_changes

