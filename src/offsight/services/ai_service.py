"""
AI service for analyzing regulatory changes using a local Ollama model.

Handles communication with Ollama API to generate summaries and classify
regulatory changes into impact categories.
"""

import json

import httpx
from sqlalchemy.orm import Session

from offsight.models.category import Category
from offsight.models.regulation_change import RegulationChange


class AiServiceError(Exception):
    """Custom exception for AI service errors."""

    pass


class AiService:
    """
    Service for calling a local Ollama model to analyse regulatory changes.

    Uses the Ollama HTTP API to generate summaries and classify changes
    into predefined impact categories.
    """

    # Fixed requirement class taxonomy (must match seeded Category names exactly)
    REQUIREMENT_CLASSES = [
        "Spatial constraints",
        "Temporal constraints",
        "Procedural obligations",
        "Technical performance expectations",
        "Operational restrictions",
        "Evidence and reporting requirements",
        "Other / unclear",
    ]

    def __init__(self, base_url: str, model: str, timeout: int = 120):
        """
        Initialize the AI service.

        Args:
            base_url: Base URL for Ollama API (e.g., "http://localhost:11434")
            model: Model name to use (e.g., "llama3.1")
            timeout: HTTP request timeout in seconds (default: 120)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def analyse_change_text(self, change_text: str) -> dict:
        """
        Calls Ollama with the given change_text and returns analysis results.

        Args:
            change_text: The diff content or change text to analyze

        Returns:
            Dictionary with keys:
                - summary: short natural-language summary of the change
                - impact_category: one of the valid categories
                - confidence: float (0.0–1.0) or None

        Raises:
            AiServiceError: If the API call fails or response cannot be parsed
        """
        # Build the prompt
        prompt = self._build_prompt(change_text)

        # Call Ollama API
        try:
            response = self._call_ollama(prompt)
        except httpx.HTTPError as e:
            raise AiServiceError(f"Failed to call Ollama API: {e}") from e

        # Parse JSON response
        try:
            result = self._parse_response(response)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise AiServiceError(f"Failed to parse AI response: {e}") from e

        # Validate and normalize requirement class
        result["requirement_class"] = self._normalize_category(result.get("requirement_class", "Other / unclear"))

        return result

    def _build_prompt(self, change_text: str) -> str:
        """
        Build the prompt for the AI model.

        Args:
            change_text: The change/diff text to analyze

        Returns:
            Complete prompt string
        """
        categories_list = ", ".join([f'"{cat}"' for cat in self.REQUIREMENT_CLASSES])
        prompt = f"""You are analyzing regulatory changes in UK offshore wind regulations.

Below is a text diff showing changes between two versions of a regulatory document:

{change_text}

Analyze this change and respond ONLY with a JSON object in this exact format:
{{
  "summary": "A brief 1-2 sentence summary of what changed and its significance",
  "requirement_class": "EXACTLY one of the following category names",
  "confidence": 0.85
}}

REQUIREMENT CLASS OPTIONS (you MUST return EXACTLY one of these, with exact spelling and capitalization):
{categories_list}

Rules:
- summary: Keep it concise (max 200 words), focus on what changed and why it matters
- requirement_class: MUST be EXACTLY one of the category names listed above, with exact spelling and capitalization
- confidence: A number between 0.0 and 1.0 indicating your confidence in the classification

Respond ONLY with the JSON object, no additional text or explanation."""
        return prompt

    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API and return the response text.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Response text from the model

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Request JSON format
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

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse the JSON response from Ollama.

        Args:
            response_text: Raw response text from Ollama

        Returns:
            Parsed dictionary with summary, impact_category, and confidence

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required keys are missing
        """
        # Clean the response - remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Parse JSON
        data = json.loads(text)

        # Validate required keys
        if "summary" not in data:
            raise KeyError("Missing 'summary' in AI response")
        # Accept either 'requirement_class' or legacy 'impact_category'
        if "requirement_class" not in data and "impact_category" not in data:
            raise KeyError("Missing 'requirement_class' or 'impact_category' in AI response")

        # Ensure confidence is a float or None
        confidence = data.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
                # Clamp to [0.0, 1.0]
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                confidence = None

        return {
            "summary": str(data["summary"]).strip(),
            "requirement_class": str(data.get("requirement_class", data.get("impact_category", ""))).strip(),
            "confidence": confidence,
        }

    def _normalize_category(self, category: str) -> str:
        """
        Normalize and validate the requirement class category.

        Args:
            category: Category string from AI response

        Returns:
            Exact category name matching one of REQUIREMENT_CLASSES, or "Other / unclear" if no match
        """
        # Trim whitespace
        normalized = category.strip()

        # Case-insensitive exact match first
        for valid_class in self.REQUIREMENT_CLASSES:
            if normalized.lower() == valid_class.lower():
                return valid_class

        # Handle common variations and mappings
        normalized_lower = normalized.lower()
        
        # Map variations to exact category names
        category_mappings = {
            "spatial": "Spatial constraints",
            "spatial constraint": "Spatial constraints",
            "temporal": "Temporal constraints",
            "temporal constraint": "Temporal constraints",
            "procedural": "Procedural obligations",
            "procedural obligation": "Procedural obligations",
            "procedure": "Procedural obligations",
            "technical": "Technical performance expectations",
            "technical performance": "Technical performance expectations",
            "performance": "Technical performance expectations",
            "operational": "Operational restrictions",
            "operational restriction": "Operational restrictions",
            "restriction": "Operational restrictions",
            "evidence": "Evidence and reporting requirements",
            "reporting": "Evidence and reporting requirements",
            "evidence & reporting": "Evidence and reporting requirements",
            "evidence and reporting": "Evidence and reporting requirements",
            "evidence and reporting requirement": "Evidence and reporting requirements",
            "other": "Other / unclear",
            "unclear": "Other / unclear",
            "unknown": "Other / unclear",
        }

        if normalized_lower in category_mappings:
            return category_mappings[normalized_lower]

        # If no match found, default to "Other / unclear"
        return "Other / unclear"

    def _get_or_create_category(self, category_name: str, db: Session) -> Category:
        """
        Get a Category by exact name (categories should be pre-seeded).

        Args:
            category_name: Exact requirement class name (e.g., "Spatial constraints")
            db: Database session

        Returns:
            Category instance

        Raises:
            ValueError: If category not found (should not happen if seeding is correct)
        """
        # Try to find existing category by exact name
        category = db.query(Category).filter(Category.name == category_name).first()

        if not category:
            # Category should exist from seeding, but create fallback if missing
            category = Category(
                name=category_name,
                description=f"Regulatory changes classified as {category_name.lower()}",
            )
            db.add(category)
            db.flush()  # Flush to get the ID without committing

        return category

    def analyse_and_update_change(
        self, change: RegulationChange, db: Session
    ) -> RegulationChange:
        """
        Analyze a RegulationChange and update it with AI results.

        Uses analyse_change_text on change.diff_content, then:
        - Updates change.ai_summary with the summary
        - Looks up or creates the Category matching impact_category and sets change.category_id
        - Updates change.status to "ai_suggested"
        - Commits the transaction and returns the updated change

        Args:
            change: The RegulationChange to analyze
            db: Database session

        Returns:
            Updated RegulationChange instance

        Raises:
            AiServiceError: If analysis fails
        """
        # Analyze the change text
        result = self.analyse_change_text(change.diff_content)

        # Update the change with AI results
        change.ai_summary = result["summary"]

        # Get or create the category
        category = self._get_or_create_category(result["requirement_class"], db)
        change.category_id = category.id

        # Update status
        change.status = "ai_suggested"

        # Commit changes
        db.commit()
        db.refresh(change)

        return change

    def analyse_pending_changes(
        self, db: Session, limit: int = 10
    ) -> list[RegulationChange]:
        """
        Find and analyze pending RegulationChange rows.

        Finds RegulationChange rows with:
        - status = "pending"
        - ai_summary is NULL

        Processes up to `limit` of them and returns the list of updated changes.

        Args:
            db: Database session
            limit: Maximum number of changes to process (default: 10)

        Returns:
            List of updated RegulationChange instances
        """
        # Find pending changes without AI summaries
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
                updated_change = self.analyse_and_update_change(change, db)
                updated_changes.append(updated_change)
            except AiServiceError as e:
                print(f"[WARN] Failed to analyze change ID {change.id}: {e}")
                # Continue with next change
                continue

        return updated_changes

