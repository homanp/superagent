import logging
from typing import Any, Literal, Optional

from decouple import config
from langchain.docstore.document import Document

from app.models.request import EmbeddingsModelProvider
from app.utils.helpers import get_first_non_null
from app.vectorstores.abstract import VectorStoreBase
from app.vectorstores.astra import AstraVectorStore
from app.vectorstores.pinecone import PineconeVectorStore
from app.vectorstores.qdrant import QdrantVectorStore
from app.vectorstores.supabase import SupabaseVectorStore
from app.vectorstores.weaviate import WeaviateVectorStore
from prisma.enums import VectorDbProvider

# TODO: use the VectorDbProvider enum
VECTOR_DB_MAPPING = {
    "pinecone": "PINECONE",
    "qdrant": "QDRANT",
    "astra": "ASTRA_DB",
    "weaviate": "WEAVIATE",
    "supabase": "SUPABASE",
    # NOTE: we used "supabase" name initially for the pgvector databases in our database
    "pgvector": "SUPABASE",
}

REVERSE_VECTOR_DB_MAPPING = {v: k for k, v in VECTOR_DB_MAPPING.items()}

logger = logging.getLogger(__name__)


class VectorStoreMain(VectorStoreBase):
    def __init__(
        self,
        options: Optional[dict],
        vector_db_provider: Optional[str],
        embeddings_model_provider: EmbeddingsModelProvider,
    ):
        """
        Determine the vectorstore
        """
        self.DEFAULT_INDEX_NAME = "superagent"
        self.options = options
        self.vectorstore = get_first_non_null(
            vector_db_provider,
            # config VECTORSTORE returns lowercase
            # vectorstore name (e.g. pinecone, astra)
            VECTOR_DB_MAPPING.get(config("VECTORSTORE", None)),
            VectorDbProvider.PINECONE.value,
        )
        self.embeddings_model_provider = embeddings_model_provider
        self.instance = self.get_database()

    def get_database(self, index_name: Optional[str] = None) -> Any:
        vectorstore_classes = {
            "PINECONE": PineconeVectorStore,
            "ASTRA_DB": AstraVectorStore,
            "WEAVIATE": WeaviateVectorStore,
            "QDRANT": QdrantVectorStore,
            "SUPABASE": SupabaseVectorStore,
        }
        index_names = {
            "PINECONE": get_first_non_null(
                self.options.get("PINECONE_INDEX"),
                config("PINECONE_INDEX", None),
                self.DEFAULT_INDEX_NAME,
            ),
            "ASTRA_DB": get_first_non_null(
                self.options.get("ASTRA_DB_COLLECTION_NAME"),
                config("ASTRA_DB_COLLECTION_NAME", None),
                self.DEFAULT_INDEX_NAME,
            ),
            "WEAVIATE": get_first_non_null(
                self.options.get("WEAVIATE_INDEX"),
                config("WEAVIATE_INDEX", None),
                self.DEFAULT_INDEX_NAME,
            ),
            "QDRANT": get_first_non_null(
                self.options.get("QDRANT_INDEX"),
                config("QDRANT_INDEX", None),
                self.DEFAULT_INDEX_NAME,
            ),
            "SUPABASE": get_first_non_null(
                self.options.get("SUPABASE_TABLE_NAME"),
                config("SUPABASE_TABLE_NAME", None),
                self.DEFAULT_INDEX_NAME,
            ),
        }

        logger.info(f"Using {self.vectorstore} vectorstore")

        if index_name is None:
            index_name = index_names.get(self.vectorstore)
        return vectorstore_classes.get(self.vectorstore)(
            index_name=index_name,
            options=self.options,
            embeddings_model_provider=self.embeddings_model_provider,
        )

    def query(
        self,
        prompt: str,
        metadata_filter: dict | None = None,
        top_k: int = 5,
        namespace: str | None = None,
        min_score: float | None = None,  # new argument for minimum similarity score
    ):
        return self.instance.query(prompt, metadata_filter, top_k, namespace, min_score)

    def query_documents(
        self,
        prompt: str,
        datasource_id: str,
        top_k: int | None,
        query_type: Literal["document", "all"] = "document",
    ):
        return self.instance.query_documents(prompt, datasource_id, top_k, query_type)

    def delete(self, datasource_id: str):
        self.instance.delete(datasource_id)

    # @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    # def _embed_with_retry(self, texts):
    #     return self.instance.embeddings.embed_documents(texts)

    def embed_documents(
        self, documents: list[Document], datasource_id: str, batch_size: int = 20
    ):
        newDocuments = [
            document.metadata.update({"datasource_id": datasource_id}) or document
            for document in documents
        ]
        self.instance.embed_documents(documents=newDocuments, batch_size=batch_size)

    def clear_cache(self, agent_id: str, datasource_id: str | None = None):
        self.instance.clear_cache(agent_id, datasource_id)
