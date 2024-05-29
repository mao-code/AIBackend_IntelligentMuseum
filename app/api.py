from flask import Blueprint, request, jsonify
from langchain_community.document_loaders import (
    TextLoader, 
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from rag.llama_index import LLaMAIndexRAG
from store.store import VectorDB
from rag.langchain import LangChainRAG

from app.services.translate_service import Translate

import json

api = Blueprint('api', __name__)

# Load roles configuration from JSON file
with open('npc_role_config.json', 'r') as f:
    roles_config = json.load(f)

@api.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to generate responses using the RAG model.
    Expects a JSON payload with a 'query' field.
    """
    data = request.json
    query = data.get('query', '')
    lang = data.get('lang', 'en')

    if query.strip() == '':
        return jsonify({
            'error': 'Query field is required'
        })
    
    ########## Detect and Translate ##########
    # Translate to Chinese and plug in target language to the prompt
    translator = Translate()
    chi_query = translator.translate(query, "zh-TW")

    lang_chinese_name = translator.get_language_name_in_chinese(lang)
    if lang_chinese_name is None:
        return jsonify({
            'error': 'Error in your language code. Please use a valid language code.'
        })
    chi_query += f"。請用{lang_chinese_name}回答"

    ########## LLaMA Index RAG ##########
    rag = LLaMAIndexRAG()
    response = rag.generate_response_with_retrieval(chi_query)
    response_text, metadata = response.response, response.metadata

    # Google translate doesn't work well for specific terms
    # translator = Translate()
    # response_text = translator.translate(response_text, lang)

    return jsonify({
        'parsed_query': chi_query,
        'response': response_text,
        'metadata': metadata
    })

@api.route('/npc/ask', methods=['POST'])
def npc_ask():
    data = request.json
    query = data.get('query', '')
    lang = data.get('lang', 'en')
    npc_role = data.get('npc_role', '博物館導覽員')

    # Translate to Chinese and plug in target language to the prompt
    translator = Translate()
    chi_query = translator.translate(query, "zh-TW")

    lang_chinese_name = translator.get_language_name_in_chinese(lang)
    if lang_chinese_name is None:
        return jsonify({
            'error': 'Error in your language code. Please use a valid language code.'
        })
    chi_query += f"。請用{lang_chinese_name}回答"

    # Get the role features
    role_features = roles_config.get(npc_role, {})
    tone = role_features.get("tone", "中立")
    style = role_features.get("style", "正常")
    background = role_features.get("background", "")
    
    # Apply the role features to the query
    chi_query = f"你現在是一個{npc_role}({background})。你的語調{tone}，且回答方式{style}。請回答以下問題："+chi_query

    rag = LLaMAIndexRAG()
    response = rag.generate_response_with_retrieval(chi_query)
    response_text, metadata = response.response, response.metadata

    return jsonify({
        'parsed_query': chi_query,
        'response': response_text,
        'metadata': metadata
    })


@api.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    target_language = data.get('target_language', 'en')

    # Set up translator
    translator = Translate()
    response = translator.translate(text, target_language)

    return jsonify(response)

########## ARCHIVED ##########
########## LangChain RAG ##########
# # Set up vector store
# loader = DirectoryLoader(path="assets", glob="./*.txt", loader_cls=TextLoader) 
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=20)

# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# model_kwargs = {'device': 'cpu'}
# embedding = HuggingFaceEmbeddings(
#     model_name=model_name, 
#     model_kwargs=model_kwargs
# )

# persist_directory = 'chroma'

# store = VectorDB(loader, text_splitter, embedding, persist_directory)
# # vectordb = store.init_vectordb()
# vectordb = store.get_vectordb_from_disk()

# # Generate response
# rag = LangChainRAG(vectordb)
# response = rag.generate_response_with_retrieval(query)

# response = {
#     "query": response["query"],
#     "result": response["result"],
#     "source_documents": [doc.metadata["source"] for doc in response["source_documents"]],
#     "source_content": [doc.page_content for doc in response["source_documents"]]
# }