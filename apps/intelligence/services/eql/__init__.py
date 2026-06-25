"""EOR Query Language (EQL) package."""

from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql

__all__ = ["parse_eql", "validate_eql"]
