"""
Gerador de embeddings para busca vetorial.
"""

from typing import List
import openai
import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

load_dotenv()


class EmbeddingGenerator:
    """
    Gera embeddings usando OpenAI.
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Inicializa gerador de embeddings.

        Args:
            model: Modelo OpenAI (text-embedding-3-small é mais barato)
        """
        self.model = model
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate(self, text: str) -> List[float]:
        """
        Gera embedding para um texto.

        Args:
            text: Texto para gerar embedding

        Returns:
            Vetor de embeddings (1536 dimensões)
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"[EMBEDDINGS] Erro ao gerar embedding: {e}")
            raise

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos (mais eficiente).

        Args:
            texts: Lista de textos

        Returns:
            Lista de vetores de embeddings
        """
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model,
            )

            return [data.embedding for data in response.data]

        except Exception as e:
            logger.error(f"[EMBEDDINGS] Erro ao gerar batch: {e}")
            raise
