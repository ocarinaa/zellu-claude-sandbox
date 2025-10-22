"""
Retriever para busca semântica no CDC.
"""

from typing import List, Tuple
from .cdc_loader import CDCKnowledgeBase, CDCArticle
from .embeddings import EmbeddingGenerator
from .vector_store import CDCVectorStore

import logging

logger = logging.getLogger(__name__)


class CDCRetriever:
    """
    Retriever inteligente para busca no CDC.
    """

    def __init__(
        self,
        kb: CDCKnowledgeBase,
        embedder: EmbeddingGenerator,
        vector_store: CDCVectorStore,
    ):
        """
        Inicializa retriever.

        Args:
            kb: Base de conhecimento CDC
            embedder: Gerador de embeddings
            vector_store: Vector store
        """
        self.kb = kb
        self.embedder = embedder
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Tuple[CDCArticle, float]]:
        """
        Busca artigos CDC relevantes para a query.

        Args:
            query: Descrição do problema do usuário
            top_k: Número de artigos a retornar

        Returns:
            Lista de (artigo, score de similaridade)
        """
        logger.info(f"[RETRIEVER] Buscando artigos para: '{query[:100]}...'")

        # Gera embedding da query
        query_embedding = await self.embedder.generate(query)

        # Busca no vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        logger.info(f"[RETRIEVER] {len(results)} artigos encontrados")

        # Log dos resultados
        for article, score in results:
            logger.info(f"[RETRIEVER]   - Art. {article.number}: {score:.3f}")

        return results

    async def retrieve_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 3,
    ) -> List[CDCArticle]:
        """
        Busca por keywords (fallback se embeddings falharem).

        Args:
            keywords: Lista de palavras-chave
            top_k: Número de artigos

        Returns:
            Lista de artigos
        """
        results = []
        seen = set()

        for keyword in keywords:
            articles = self.kb.search_by_keyword(keyword)
            for article in articles:
                if article.number not in seen:
                    results.append(article)
                    seen.add(article.number)

                if len(results) >= top_k:
                    break

            if len(results) >= top_k:
                break

        logger.info(f"[RETRIEVER] Keyword search: {len(results)} artigos")
        return results[:top_k]


async def initialize_cdc_retriever() -> CDCRetriever:
    """
    Inicializa retriever com CDC (helper function).

    Returns:
        CDCRetriever pronto para uso
    """
    logger.info("[RETRIEVER] Inicializando CDC retriever")

    # 1. Carrega base CDC
    kb = CDCKnowledgeBase()

    # 2. Cria embedder
    embedder = EmbeddingGenerator()

    # 3. Gera embeddings dos artigos
    texts = [
        f"{article.title}. {article.content}"
        for article in kb.articles
    ]

    embeddings = await embedder.generate_batch(texts)

    # 4. Cria vector store
    vector_store = CDCVectorStore()
    vector_store.add_articles(kb.articles, embeddings)

    # 5. Cria retriever
    retriever = CDCRetriever(kb, embedder, vector_store)

    logger.info("[RETRIEVER] ✅ Inicializado com sucesso")
    return retriever
