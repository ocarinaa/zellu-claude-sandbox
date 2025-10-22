"""
Testes de integração: Upload de arquivos.
"""

import pytest
from src.storage import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_save_and_read(local_storage):
    """Testa salvar e ler arquivo."""
    content = b"Conteudo de teste"
    filename = "test.txt"
    chat_id = "chat-123"

    # Salva
    relative_path = await local_storage.save(filename, content, chat_id)

    assert relative_path is not None
    assert chat_id in relative_path

    # Lê
    read_content = await local_storage.read(relative_path)

    assert read_content == content


@pytest.mark.asyncio
async def test_local_storage_multiple_files(local_storage):
    """Testa salvamento de múltiplos arquivos."""
    chat_id = "chat-456"

    # Salva 3 arquivos
    paths = []
    for i in range(3):
        content = f"Arquivo {i}".encode()
        filename = f"file_{i}.txt"
        path = await local_storage.save(filename, content, chat_id)
        paths.append(path)

    # Verifica que todos foram salvos
    assert len(paths) == 3
    assert len(set(paths)) == 3  # Todos diferentes

    # Lê todos
    for i, path in enumerate(paths):
        content = await local_storage.read(path)
        assert content == f"Arquivo {i}".encode()


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer Tesseract instalado")
async def test_pdf_extraction():
    """Testa extração de texto de PDF."""
    from src.ocr import PDFExtractor

    # TODO: Adicionar PDF de teste
    pass


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer Tesseract instalado")
async def test_image_ocr():
    """Testa OCR em imagem."""
    from src.ocr import ImageOCR

    # TODO: Adicionar imagem de teste
    pass
