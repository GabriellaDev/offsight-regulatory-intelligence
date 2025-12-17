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
    """
    Service for detecting changes between document versions.
    
    This service compares consecutive versions of RegulationDocument entities
    from the same source, computes textual diffs using Python's difflib,
    and creates RegulationChange records when differences are detected.
    """

    def get_ordered_documents(
        self, source_id: int, db: Session
    ) -> list[RegulationDocument]:
        """
        Retrieve all RegulationDocument entries for a source, ordered chronologically.
        
        Documents are sorted by numeric version if available, otherwise by
        retrieved_at timestamp. This ensures proper chronological ordering
        for change detection.
        
        Args:
            source_id: The ID of the Source to retrieve documents for
            db: SQLAlchemy database session
            
        Returns:
            List of RegulationDocument instances ordered by version/retrieved_at,
            oldest first. Returns empty list if source has no documents.
            
        Example:
            >>> service = ChangeDetectionService()
            >>> docs = service.get_ordered_documents(source_id=1, db=session)
            >>> print(f"Found {len(docs)} document versions")
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
        Detect changes between consecutive document versions for a source.
        
        This method performs the following steps:
        1. Loads all documents for the source in chronological order
        2. Iterates through consecutive document pairs
        3. Checks if a RegulationChange already exists for each pair (prevents duplicates)
        4. Computes a unified diff between document contents using difflib
        5. Creates a new RegulationChange record if diff is non-empty
        
        The method is idempotent - running it multiple times will not create
        duplicate change records for the same document pairs.
        
        Args:
            source_id: The ID of the Source to detect changes for
            db: SQLAlchemy database session for queries and commits
            
        Returns:
            List of newly created RegulationChange instances. Returns empty list
            if source has fewer than 2 documents, or if all document pairs
            already have change records, or if all diffs are empty.
            
        Note:
            Empty or whitespace-only diffs are skipped and not stored as changes.
            
        Example:
            >>> service = ChangeDetectionService()
            >>> changes = service.detect_changes_for_source(source_id=1, db=session)
            >>> print(f"Detected {len(changes)} new changes")
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

