"""
OCR para imagens usando Tesseract.
"""

from pathlib import Path
from PIL import Image
import pytesseract

import logging

logger = logging.getLogger(__name__)


class ImageOCR:
    """
    Realiza OCR em imagens.
    """

    @staticmethod
    async def extract_text(file_path: Path | str) -> str:
        """
        Extrai texto de imagem via OCR.

        Args:
            file_path: Caminho da imagem

        Returns:
            Texto extraído
        """
        logger.info(f"[IMAGE OCR] Processando {file_path}")

        try:
            # Abre imagem
            image = Image.open(str(file_path))

            # Realiza OCR (português)
            text = pytesseract.image_to_string(image, lang='por')

            logger.info(f"[IMAGE OCR] ✅ {len(text)} caracteres extraídos")

            return text.strip()

        except Exception as e:
            logger.error(f"[IMAGE OCR] Erro: {e}")
            return ""
