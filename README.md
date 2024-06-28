# RAG Backend For CAP
## Framework:
* LangChain
* LLaMAIndex
  
## Components
* VectorDB: Chroma
* Embedding Model: sentence-transformers/all-MiniLM-L6-v2
* LLM: OpenAI GPT3.5 Turbo

## Advanced RAG
* pre-retrieval, retrieval, and post-retrieval optimization

## External Data
* 故宮博物館展品資料 (format: PDF, Text File)
* Internet (format: HTML)

## Other Tools
* Translate Tool: Google Cloud Translate API

## Reference
* [Basic RAG](https://medium.com/@cch.chichieh/rag%E5%AF%A6%E4%BD%9C%E6%95%99%E5%AD%B8-langchain-llama2-%E5%89%B5%E9%80%A0%E4%BD%A0%E7%9A%84%E5%80%8B%E4%BA%BAllm-d6838febf8c4)
* [Google Cloud Translate API](https://cloud.google.com/translate/docs/reference/rest/v2/translate)
* [Advanced RAG](https://towardsdatascience.com/advanced-retrieval-augmented-generation-from-theory-to-llamaindex-implementation-4de1464a9930)
* [Question Answering in RAG using Llama-Index: Part 1](https://medium.com/@aneesha161994/question-answering-in-rag-using-llama-index-92cfc0b4dae3)
* [Extracting Metadata for Better Document Indexing and Understanding](https://docs.llamaindex.ai/en/stable/examples/metadata_extraction/MetadataExtractionSEC/)
```

CAP
├─ .DS_Store
├─ .env
├─ README.md
├─ __pycache__
│  └─ main.cpython-310.pyc
├─ app
│  ├─ __init__.py
│  ├─ __pycache__
│  │  ├─ __init__.cpython-310.pyc
│  │  └─ api.cpython-310.pyc
│  ├─ api.py
│  └─ services
│     ├─ __init__.py
│     ├─ __pycache__
│     │  ├─ __init__.cpython-310.pyc
│     │  └─ translate_service.cpython-310.pyc
│     └─ translate_service.py
├─ assets
│  ├─ .DS_Store
│  ├─ 康侯方鼎_故宮.txt
│  ├─ 毛公鼎_故宮.txt
│  ├─ 翠玉白菜_故宮.txt
│  └─ 肉形石_wiki.txt
├─ chroma
│  ├─ 379e7f20-dc49-4092-af32-3ee328736706
│  │  ├─ data_level0.bin
│  │  ├─ header.bin
│  │  ├─ length.bin
│  │  └─ link_lists.bin
│  └─ chroma.sqlite3
├─ main.py
├─ rag
│  ├─ __init__.py
│  ├─ __pycache__
│  │  ├─ __init__.cpython-310.pyc
│  │  ├─ langchain.cpython-310.pyc
│  │  ├─ llama_index.cpython-310.pyc
│  │  ├─ rag.cpython-310.pyc
│  │  └─ retrieval.cpython-310.pyc
│  ├─ langchain.py
│  ├─ llama_index.py
│  └─ rag.py
├─ requirements.txt
└─ store
   ├─ __init__.py
   ├─ __pycache__
   │  ├─ __init__.cpython-310.pyc
   │  └─ store.cpython-310.pyc
   └─ store.py
```