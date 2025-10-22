"""Módulo de storage."""

from .local import LocalStorage
from .validator import FileValidator

__all__ = [
    "LocalStorage",
    "FileValidator",
]
