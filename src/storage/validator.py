"""
Validador de arquivos uploaded.
"""

from typing import Tuple
import mimetypes
import magic
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# Tipos permitidos
ALLOWED_MIME_TYPES = {
    # Documentos
    "application/pdf",
    "application/msword",  # DOC
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/vnd.ms-excel",  # XLS
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
    "text/plain",

    # Imagens
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",

    # Comprimidos
    "application/zip",
    "application/x-rar-compressed",
}

# Tamanhos máximos
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


class FileValidator:
    """
    Valida arquivos uploaded.
    """

    @staticmethod
    def validate(
        filename: str,
        content: bytes,
    ) -> Tuple[bool, str | None]:
        """
        Valida arquivo.

        Args:
            filename: Nome do arquivo
            content: Conteúdo em bytes

        Returns:
            (is_valid, error_message)
        """
        # 1. Valida tamanho
        size = len(content)

        if size > MAX_FILE_SIZE:
            return False, f"Arquivo muito grande: {size / (1024*1024):.1f}MB (máx: 50MB)"

        # 2. Detecta MIME type real (não confia na extensão)
        try:
            mime = magic.from_buffer(content, mime=True)
        except Exception as e:
            logger.error(f"[VALIDATOR] Erro ao detectar MIME: {e}")
            # Fallback para extensão
            mime = mimetypes.guess_type(filename)[0]

        if not mime:
            return False, "Não foi possível detectar tipo do arquivo"

        # 3. Valida MIME type
        if mime not in ALLOWED_MIME_TYPES:
            return False, f"Tipo de arquivo não permitido: {mime}"

        # 4. Validações específicas por tipo
        if mime.startswith("image/"):
            if size > MAX_IMAGE_SIZE:
                return False, f"Imagem muito grande: {size / (1024*1024):.1f}MB (máx: 10MB)"

        logger.info(f"[VALIDATOR] ✅ Arquivo válido: {filename} ({mime}, {size / 1024:.1f}KB)")
        return True, None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza nome do arquivo.

        Args:
            filename: Nome original

        Returns:
            Nome sanitizado
        """
        # Remove caracteres perigosos
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip().replace(" ", "_")

        # Limita tamanho
        if len(safe_name) > 200:
            name, ext = Path(safe_name).stem, Path(safe_name).suffix
            safe_name = name[:200 - len(ext)] + ext

        return safe_name.lower()
