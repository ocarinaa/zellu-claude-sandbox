"""
Vector store com FAISS para busca rápida.
"""

from typing import List, Tuple
import numpy as np
import faiss
import pickle
from pathlib import Path

from .cdc_loader import CDCArticle

import logging

logger = logging.getLogger(__name__)


class CDCVectorStore:
    """
    Vector store para busca semântica em artigos CDC.
    """

    def __init__(self, dimension: int = 1536):
        """
        Inicializa vector store.

        Args:
            dimension: Dimensão dos embeddings (1536 para OpenAI)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.articles: List[CDCArticle] = []
        self.embeddings: np.ndarray | None = None

    def add_articles(
        self,
        articles: List[CDCArticle],
        embeddings: List[List[float]],
    ) -> None:
        """
        Adiciona artigos ao vector store.

        Args:
            articles: Lista de artigos CDC
            embeddings: Lista de embeddings correspondentes
        """
        if len(articles) != len(embeddings):
            raise ValueError("Número de artigos e embeddings deve ser igual")

        self.articles.extend(articles)

        # Converte para numpy array
        emb_array = np.array(embeddings, dtype=np.float32)

        if self.embeddings is None:
            self.embeddings = emb_array
        else:
            self.embeddings = np.vstack([self.embeddings, emb_array])

        # Adiciona ao índice FAISS
        self.index.add(emb_array)

        logger.info(f"[VECTOR STORE] {len(articles)} artigos adicionados (total: {len(self.articles)})")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[Tuple[CDCArticle, float]]:
        """
        Busca artigos mais similares.

        Args:
            query_embedding: Embedding da query
            top_k: Número de resultados

        Returns:
            Lista de (artigo, distance_score)
        """
        if len(self.articles) == 0:
            logger.warning("[VECTOR STORE] Nenhum artigo no store")
            return []

        # Busca no FAISS
        query_array = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_array, top_k)

        # Monta resultados
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.articles):
                article = self.articles[idx]
                # Distance menor = mais similar (L2 distance)
                similarity = 1.0 / (1.0 + distance)  # Normaliza para 0-1
                results.append((article, similarity))

        logger.info(f"[VECTOR STORE] {len(results)} resultados retornados")
        return results

    def save(self, path: str) -> None:
        """Salva vector store em disco."""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Salva índice FAISS
        faiss.write_index(self.index, str(save_path / "faiss.index"))

        # Salva metadados
        with open(save_path / "metadata.pkl", 'wb') as f:
            pickle.dump({
                "articles": self.articles,
                "embeddings": self.embeddings,
            }, f)

        logger.info(f"[VECTOR STORE] Salvo em {path}")

    @classmethod
    def load(cls, path: str) -> "CDCVectorStore":
        """Carrega vector store do disco."""
        load_path = Path(path)

        # Carrega índice
        index = faiss.read_index(str(load_path / "faiss.index"))

        # Carrega metadados
        with open(load_path / "metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)

        # Reconstrói store
        store = cls(dimension=index.d)
        store.index = index
        store.articles = metadata["articles"]
        store.embeddings = metadata["embeddings"]

        logger.info(f"[VECTOR STORE] Carregado de {path}")
        return store
