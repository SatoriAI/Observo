from functools import lru_cache

from django.conf import settings
from langchain_community.vectorstores import PGVector
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings


@lru_cache(maxsize=1)
def store() -> PGVector:
    return PGVector(
        connection_string=settings.DATABASE_URL,
        collection_name="opportunities",
        embedding_function=GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY,
        ),
        use_jsonb=True,
    )


def retriever_topk(k: int = 10, _filter: dict | None = None) -> VectorStoreRetriever:
    return store().as_retriever(search_type="similarity", search_kwargs={"k": k, "filter": (_filter or {})})
