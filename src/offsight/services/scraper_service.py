"""
Scraper service for retrieving and storing regulatory documents.

Handles fetching content from sources, extracting text, and storing
new document versions when content changes.
"""

import hashlib
from datetime import UTC, datetime

from bs4 import BeautifulSoup
import httpx
from httpx import HTTPStatusError, RequestError
from sqlalchemy import desc
from sqlalchemy.orm import Session

from offsight.models.regulation_document import RegulationDocument
from offsight.models.source import Source


class ScraperService:
    """Service for scraping regulatory sources and storing document versions."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the scraper service.

        Args:
            timeout: HTTP request timeout in seconds (default: 30)
        """
        self.timeout = timeout

    def fetch_raw_content(self, source: Source) -> str | None:
        """
        Fetch and extract text content from a source URL.

        Args:
            source: The Source entity to fetch content from

        Returns:
            Extracted text content as a string, or None if the fetch failed.

        Notes:
            HTTP/network errors are caught and logged; returns None on failure.
        """
        # Fetch the HTML content
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(source.url)
                response.raise_for_status()
                html_content = response.text
        except HTTPStatusError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            print(
                f"[ERROR] HTTP status error while fetching {source.url}: {status} ({exc})"
            )
            return None
        except RequestError as exc:
            print(f"[ERROR] Network error while fetching {source.url}: {exc}")
            return None

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract text from paragraph tags
        # This is a simple extraction strategy; can be enhanced later
        paragraphs = soup.find_all("p")
        text_content = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # If no paragraphs found, fall back to body text
        if not text_content:
            body = soup.find("body")
            if body:
                text_content = body.get_text(separator="\n\n", strip=True)
            else:
                text_content = soup.get_text(separator="\n\n", strip=True)

        return text_content

    def fetch_and_store_if_changed(
        self, source_id: int, db: Session
    ) -> RegulationDocument | None:
        """
        Fetch content from a source and store a new document version if content changed.

        Args:
            source_id: The ID of the Source to fetch
            db: SQLAlchemy database session

        Returns:
            New RegulationDocument if content changed, None if unchanged or fetch failed.

        Raises:
            ValueError: If source not found

        Notes:
            HTTP/network errors are handled and logged; returns None on failure.
        """
        # Load the source
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source with id {source_id} not found")

        if not source.enabled:
            return None

        # Fetch raw content
        content = self.fetch_raw_content(source)
        if content is None:
            return None

        # Compute content hash (SHA256)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Get the latest document for this source (by retrieved_at for hash comparison)
        latest_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.source_id == source_id)
            .order_by(desc(RegulationDocument.retrieved_at))
            .first()
        )

        # Check if content has changed - prevent duplicate storage
        if latest_doc:
            print(f"  Comparing with latest document: ID {latest_doc.id}, version {latest_doc.version}")
            print(f"  Latest hash: {latest_doc.content_hash[:16]}...")
            print(f"  New hash:    {content_hash[:16]}...")
            
            if latest_doc.content_hash == content_hash:
                # Content unchanged - DO NOT store a new document
                print(f"  No changes detected; skipping storage.")
                return None
            else:
                print(f"  Content hash differs - new version will be created.")
        else:
            print(f"  No previous documents found for this source - creating first version.")

        # Determine next version number
        # Get all documents for this source to find the highest version number
        all_docs = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.source_id == source_id)
            .all()
        )

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
                # Use highest version + 1
                next_version = str(max_version_num + 1)
                print(f"  Incrementing version: {max_version_num} → {next_version}")
            else:
                # No numeric versions found, use latest doc's version + suffix
                if latest_doc:
                    next_version = f"{latest_doc.version}.1"
                    print(f"  Non-numeric version detected, appending suffix: {latest_doc.version} → {next_version}")
                else:
                    next_version = "1"
                    print(f"  Creating first document version: {next_version}")
        else:
            # First document for this source
            next_version = "1"
            print(f"  Creating first document version: {next_version}")

        # Create new document
        new_doc = RegulationDocument(
            source_id=source_id,
            version=next_version,
            content=content,
            content_hash=content_hash,
            retrieved_at=datetime.now(UTC),
            url=source.url,
            document_metadata=None,
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return new_doc

