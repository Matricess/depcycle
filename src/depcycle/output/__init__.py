"""Output writers for serializing dependency graph data."""

from .base import IOutputWriter
from .json_writer import JsonWriter

__all__ = ["IOutputWriter", "JsonWriter"]
