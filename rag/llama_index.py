from rag.rag import RAGInterface

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser

import weaviate
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.weaviate import WeaviateVectorStore
import os

class LLaMAIndexRAG(RAGInterface):
    def __init__(self):
        super().__init__()
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
        Settings.embed_model = OpenAIEmbedding() 
        
        # Load data
        documents = SimpleDirectoryReader(
            input_dir="assets",
            recursive=True,
        ).load_data() 

        # Chunk the documents
        node_parser = SimpleNodeParser.from_defaults(chunk_size=1024)
        # Extract nodes from documents
        nodes = node_parser.get_nodes_from_documents(documents)

        # Build Index (VectorDB)
        client = weaviate.Client(
            embedded_options=weaviate.embedded.EmbeddedOptions(), 
        )
        # Construct vector store
        index_name = "Museum_index"
        vector_store = WeaviateVectorStore(
            weaviate_client = client, 
            index_name = index_name
        )

        # Set up the storage for the embeddings
        # for a remote vector store, we don't need to persist the embeddings
        # cuz it is already stored in the remote weaviate instance
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Setup the index
        # build VectorStoreIndex that takes care of chunking documents
        # and encoding chunks to embeddings for future retrieval
        index = VectorStoreIndex(
            nodes,
            storage_context = storage_context,
        )

        # The QueryEngine class is equipped with the generator
        # and facilitates the retrieval and generation steps
        assert index is not None
        self.query_engine = index.as_query_engine()

    def generate_response(self, question):
        pass
    
    def generate_response_with_retrieval(self, question):
        response = self.query_engine.query(question)
        # print("Response: ", response.response)
        # print("Metadata: ", response.metadata)
        return response
