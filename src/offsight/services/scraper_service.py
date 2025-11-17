"""
Scraper service for retrieving and storing regulatory documents.

Handles fetching content from sources, extracting text, and storing
new document versions when content changes.
"""

import hashlib
from datetime import datetime

from bs4 import BeautifulSoup
import httpx
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

    def fetch_raw_content(self, source: Source) -> str:
        """
        Fetch and extract text content from a source URL.

        Args:
            source: The Source entity to fetch content from

        Returns:
            Extracted text content as a string

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        # Fetch the HTML content
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(source.url)
            response.raise_for_status()
            html_content = response.text

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
            New RegulationDocument if content changed, None otherwise

        Raises:
            ValueError: If source not found
            httpx.HTTPError: If the HTTP request fails
        """
        # Load the source
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source with id {source_id} not found")

        if not source.enabled:
            return None

        # Fetch raw content
        content = self.fetch_raw_content(source)

        # Compute content hash (SHA256)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Get the latest document for this source
        latest_doc = (
            db.query(RegulationDocument)
            .filter(RegulationDocument.source_id == source_id)
            .order_by(desc(RegulationDocument.retrieved_at))
            .first()
        )

        # Check if content has changed
        if latest_doc and latest_doc.content_hash == content_hash:
            # Content unchanged, return None
            return None

        # Determine next version number
        if latest_doc:
            # Try to parse version as integer and increment
            try:
                next_version = str(int(latest_doc.version) + 1)
            except ValueError:
                # If version is not numeric, append a suffix
                next_version = f"{latest_doc.version}.1"
        else:
            # First document for this source
            next_version = "1"

        # Create new document
        new_doc = RegulationDocument(
            source_id=source_id,
            version=next_version,
            content=content,
            content_hash=content_hash,
            retrieved_at=datetime.utcnow(),
            url=source.url,
            document_metadata=None,
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return new_doc

