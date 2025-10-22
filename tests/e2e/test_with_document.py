"""
Teste End-to-End: Fluxo com upload de documento.
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.skip(reason="Requer LLM API keys, Tesseract e setup completo")
async def test_flow_with_pdf_upload():
    """
    Testa fluxo completo: Upload de PDF com análise.

    Cenário:
    1. Usuário inicia conversa
    2. Usuário faz upload de PDF (fatura ou protocolo)
    3. Sistema extrai texto com PyMuPDF
    4. IA analiza documento (tipo, valores, datas)
    5. IA integra análise na conversa
    6. IA coleta informações adicionais
    7. IA finaliza com has_documents=True
    """
    # TODO: Implementar com mocks ou API real

    # Simulação do fluxo:
    # - POST /upload com PDF
    # - Sistema retorna análise do documento
    # - Conversa continua com contexto do documento
    # - Finalização usa bonus de documentação

    # Assertivas esperadas:
    # assert upload_response["success"] is True
    # assert "document_type" in upload_response["analysis"]
    # assert extracted_info.has_documents is True

    assert True  # Placeholder


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.skip(reason="Requer LLM API keys, Tesseract e setup completo")
async def test_flow_with_image_upload():
    """
    Testa fluxo completo: Upload de imagem com OCR.

    Cenário:
    1. Usuário inicia conversa
    2. Usuário faz upload de imagem (foto de fatura/protocolo)
    3. Sistema extrai texto com Tesseract OCR
    4. IA analiza documento
    5. IA integra na conversa
    6. IA finaliza com has_documents=True
    """
    # TODO: Implementar com mocks ou API real

    assert True  # Placeholder
