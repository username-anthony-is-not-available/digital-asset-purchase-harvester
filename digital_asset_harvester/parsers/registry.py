"""Registry for template-based parsers."""

from typing import Any, Dict, List, Optional
from .models import ExtractionTemplate
from .definitions import EXCHANGE_TEMPLATES
from .engine import TemplateEngine

class ParserRegistry:
    """Registry to manage and select template engines."""

    def __init__(self, templates: Optional[List[ExtractionTemplate]] = None):
        if templates is None:
            templates = EXCHANGE_TEMPLATES
        self.engines = [TemplateEngine(t) for t in templates]

    def extract(self, subject: str, sender: str, body: str) -> Optional[List[Dict[str, Any]]]:
        """Find a matching template and extract data."""
        for engine in self.engines:
            if engine.can_handle(subject, sender):
                results = engine.extract(subject, body)
                if results:
                    return results
        return None

# Global registry instance
parser_registry = ParserRegistry()
