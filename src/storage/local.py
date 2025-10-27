"""
Storage local para desenvolvimento.
"""

from pathlib import Path
import uuid
import aiofiles
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class LocalStorage:
    """
    Armazena arquivos localmente.
    """

    def __init__(self, base_path: str = "uploads"):
        """
        Inicializa storage local.

        Args:
            base_path: Diretório base para uploads
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        filename: str,
        content: bytes,
        chat_id: str,
    ) -> str:
        """
        Salva arquivo localmente.

        Args:
            filename: Nome do arquivo
            content: Conteúdo em bytes
            chat_id: ID da conversa

        Returns:
            URL/path do arquivo salvo
        """
        # Cria diretório por chat_id
        chat_dir = self.base_path / chat_id
        chat_dir.mkdir(parents=True, exist_ok=True)

        # Nome único com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"

        file_path = chat_dir / unique_name

        # Salva arquivo
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f"[STORAGE] ✅ Arquivo salvo: {file_path}")

        # Retorna path relativo
        return str(file_path.relative_to(self.base_path))

    async def read(self, relative_path: str) -> bytes:
        """
        Lê arquivo do storage.

        Args:
            relative_path: Path relativo

        Returns:
            Conteúdo em bytes
        """
        file_path = self.base_path / relative_path

        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()

        return content

    def get_full_path(self, relative_path: str) -> Path:
        """Retorna path completo."""
        return self.base_path / relative_path
