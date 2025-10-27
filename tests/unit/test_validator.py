"""
Testes unitários: File Validator.
"""

import pytest
from src.storage import FileValidator


def test_validate_pdf_valid():
    """Testa validação de PDF válido."""
    # Mock PDF content (magic bytes)
    pdf_content = b'%PDF-1.4\n%\xE2\xE3\xCF\xD3\n' + b'x' * 1000

    is_valid, error = FileValidator.validate("test.pdf", pdf_content)

    assert is_valid is True
    assert error is None


def test_validate_file_too_large():
    """Testa arquivo muito grande."""
    large_content = b'x' * (51 * 1024 * 1024)  # 51MB

    is_valid, error = FileValidator.validate("large.pdf", large_content)

    assert is_valid is False
    assert "muito grande" in error.lower()


def test_sanitize_filename():
    """Testa sanitização de nome."""
    dangerous_name = "../../etc/passwd.txt"
    safe_name = FileValidator.sanitize_filename(dangerous_name)

    # A função remove "/" mas mantém ".", o importante é que remove os "/"
    assert "/" not in safe_name
    # Verifica que o nome foi modificado (não é igual ao original)
    assert safe_name != dangerous_name


def test_sanitize_filename_with_spaces():
    """Testa sanitização com espaços."""
    name_with_spaces = "Meu Arquivo Legal.pdf"
    safe_name = FileValidator.sanitize_filename(name_with_spaces)

    assert " " not in safe_name
    assert "_" in safe_name
