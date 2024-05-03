from langchain_community.vectorstores import Chroma
import os

class VectorDB:
    def __init__(self, loader, text_splitter, embedding, persist_directory):
        self.loader = loader
        self.text_splitter = text_splitter
        self.embedding = embedding
        self.persist_directory = persist_directory

        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)

    def init_vectordb(self):
        # Load external dataset
        documents = self.loader.load()

        # Split the documents into chunks
        all_splits = self.text_splitter.split_documents(documents)

        # Embed and store the texts
        # delete the existing db files first
        vectordb = Chroma.from_documents(
            documents=all_splits,
            embedding=self.embedding, 
            persist_directory=self.persist_directory
        )

        return vectordb
    
    def get_vectordb_from_disk(self):
        return Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embedding
        )

