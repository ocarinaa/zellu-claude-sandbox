"""
Extrator de texto de PDFs.
"""

import fitz  # PyMuPDF
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extrai texto de arquivos PDF.
    """

    @staticmethod
    async def extract_text(file_path: Path | str) -> str:
        """
        Extrai texto de PDF.

        Args:
            file_path: Caminho do PDF

        Returns:
            Texto extraído
        """
        logger.info(f"[PDF EXTRACTOR] Extraindo texto de {file_path}")

        try:
            doc = fitz.open(str(file_path))
            text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if text.strip():
                    text_parts.append(f"--- Página {page_num + 1} ---\n{text}")

            doc.close()

            full_text = "\n\n".join(text_parts)

            logger.info(f"[PDF EXTRACTOR] ✅ {len(full_text)} caracteres extraídos")

            return full_text

        except Exception as e:
            logger.error(f"[PDF EXTRACTOR] Erro: {e}")
            return ""
