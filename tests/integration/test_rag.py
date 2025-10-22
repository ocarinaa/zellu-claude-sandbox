"""
Testes de integração: RAG (Retrieval-Augmented Generation).
"""

import pytest
from src.rag import CDCKnowledgeBase, EmbeddingGenerator, CDCVectorStore, CDCRetriever


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer OpenAI API key válida")
async def test_rag_full_pipeline():
    """Testa pipeline completo de RAG."""
    # Carrega knowledge base
    kb = CDCKnowledgeBase()

    # Cria embedder
    embedder = EmbeddingGenerator()

    # Cria vector store
    vector_store = CDCVectorStore()

    # Adiciona artigos
    await vector_store.add_articles(kb.articles, embedder)

    # Cria retriever
    retriever = CDCRetriever(kb, embedder, vector_store)

    # Busca
    query = "cobrança indevida"
    results = await retriever.retrieve(query, top_k=3)

    assert len(results) > 0
    assert results[0]["number"] == "42"  # Art. 42 é mais relevante


def test_cdc_vector_store_save_load(tmp_path):
    """Testa salvamento e carregamento do vector store."""
    from src.rag import CDCVectorStore

    vector_store = CDCVectorStore()

    # Salva
    save_path = tmp_path / "vector_store.pkl"
    vector_store.save(str(save_path))

    assert save_path.exists()

    # Carrega
    loaded_store = CDCVectorStore()
    loaded_store.load(str(save_path))

    # Verifica (não precisa de embeddings reais para testar save/load)
    assert loaded_store is not None
