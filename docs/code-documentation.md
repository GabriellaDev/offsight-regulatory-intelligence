# Code Documentation Guide

This document explains the code documentation standards used in OffSight and how to generate API documentation.

## Python Docstrings

Python uses **docstrings** (triple-quoted strings) for documentation, similar to Javadoc in Java. Docstrings are placed immediately after function/class definitions and are accessible at runtime via the `__doc__` attribute.

### Docstring Formats

OffSight uses the **Google-style** docstring format, which is widely adopted and readable:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief one-line description.
    
    Longer description explaining what the function does, its purpose,
    and any important details about its behavior.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When parameter is invalid
        KeyError: When key is not found
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Class Docstrings

```python
class MyClass:
    """
    Brief description of the class.
    
    Longer description explaining the class's purpose, its main
    responsibilities, and how it fits into the system architecture.
    
    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """
    
    def __init__(self, param: str):
        """
        Initialize the class instance.
        
        Args:
            param: Description of initialization parameter
        """
        self.attribute1 = param
```

### Module Docstrings

Every module should start with a docstring:

```python
"""
Module name and purpose.

This module provides [brief description of what the module does].
It handles [key responsibilities] and integrates with [other components].

Key classes:
    - ClassName1: Description
    - ClassName2: Description
"""
```

## Generating API Documentation

### Using Sphinx (Recommended)

Sphinx is the standard tool for generating Python documentation from docstrings.

**Installation:**
```bash
pip install sphinx sphinx-rtd-theme
```

**Setup:**
```bash
cd docs
sphinx-quickstart
# Follow prompts, select "autodoc" extension
```

**Configuration (`conf.py`):**
```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # For Google-style docstrings
]

import sys
import os
sys.path.insert(0, os.path.abspath('../src'))
```

**Generate documentation:**
```bash
sphinx-build -b html . _build/html
```

### Using pydoc (Built-in)

Python includes a built-in documentation generator:

```bash
# View module documentation in browser
python -m pydoc -p 1234 offsight.services.pipeline_service

# Generate HTML
python -m pydoc -w offsight.services.pipeline_service
```

### FastAPI Auto-Generated Docs

FastAPI automatically generates interactive API documentation from docstrings:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The docstrings in API endpoint functions are automatically displayed in these interfaces.

## Documentation Standards in OffSight

### What to Document

1. **All public functions and methods** - Include purpose, parameters, return values, exceptions
2. **All classes** - Include purpose, main responsibilities, key attributes
3. **Complex algorithms** - Explain the approach and any important implementation details
4. **API endpoints** - Include request/response examples
5. **Configuration options** - Explain what each setting does

### What NOT to Document

1. **Trivial getters/setters** - Unless they have special behavior
2. **Private methods** (starting with `_`) - Internal implementation details
3. **Obvious code** - If the code is self-explanatory, minimal docs are fine

### Docstring Sections

Use these sections in order:

1. **Brief description** (one line)
2. **Detailed description** (if needed)
3. **Args** - Parameter descriptions
4. **Returns** - Return value description
5. **Raises** - Exceptions that may be raised
6. **Note** - Important implementation notes
7. **Example** - Usage examples (optional but helpful)

## Viewing Documentation

### In Code Editors

Most modern IDEs (VS Code, PyCharm) show docstrings in tooltips when hovering over functions.

### In Python REPL

```python
>>> from offsight.services.pipeline_service import run_pipeline
>>> help(run_pipeline)
>>> print(run_pipeline.__doc__)
```

### FastAPI Interactive Docs

Visit http://localhost:8000/docs to see all API endpoints with their docstrings rendered in an interactive interface.

## Best Practices

1. **Keep docstrings up to date** - Update them when code changes
2. **Be concise but complete** - Include all necessary information without verbosity
3. **Use type hints** - They complement docstrings and provide better IDE support
4. **Include examples** - Especially for complex functions
5. **Document edge cases** - Mention any important limitations or special behaviors
6. **Use consistent format** - Stick to Google-style throughout the project

## Example: Well-Documented Function

```python
def fetch_and_store_if_changed(
    self, source_id: int, db: Session
) -> RegulationDocument | None:
    """
    Fetch content from a source and store a new document version if content changed.
    
    This method performs the complete scraping workflow:
    1. Loads the source from the database
    2. Fetches current content from the source URL
    3. Computes SHA256 hash of the content
    4. Compares with the latest stored document's hash
    5. Stores a new RegulationDocument only if the hash differs
    6. Increments version numbers appropriately
    
    The method is idempotent - calling it multiple times with unchanged content
    will not create duplicate document versions.
    
    Args:
        source_id: The ID of the Source to fetch and store
        db: SQLAlchemy database session for queries and commits
        
    Returns:
        New RegulationDocument instance if content changed and was stored,
        None if content is unchanged (hash matches) or if fetch failed.
        
    Raises:
        ValueError: If source with the given ID is not found in the database
        
    Note:
        HTTP/network errors are handled gracefully and logged; the method
        returns None on failure rather than raising exceptions.
        
    Example:
        >>> scraper = ScraperService()
        >>> new_doc = scraper.fetch_and_store_if_changed(source_id=1, db=session)
        >>> if new_doc:
        ...     print(f"Stored new version: {new_doc.version}")
        ... else:
        ...     print("No changes detected")
    """
    # Implementation...
```

