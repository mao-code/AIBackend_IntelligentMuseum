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

# AI助理
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
    # chi_query += f"。請用{lang_chinese_name}回答"

    # 預設AI助理使用博物館導覽員
    role = '博物館導覽員'
    role_features = roles_config.get(role, {})
    tone = role_features.get("tone", "中立")
    style = role_features.get("style", "正常")
    background = role_features.get("background", "")
    dynasty = role_features.get("dynasty", "現代")

    query_info = {
        'query': chi_query,
        'target_lang_code': lang,
        'target_lang': lang_chinese_name,
        'role': role,
        'dynasty': dynasty,
        'background': background,
        'tone': tone,
        'style': style
    }

    ########## LLaMA Index RAG ##########
    rag = LLaMAIndexRAG()
    response = rag.generate_response_with_retrieval(query_info)
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
    # chi_query += f"。請用'{lang_chinese_name}'回答"

    # Get the role features
    role_features = roles_config.get(npc_role, {})
    tone = role_features.get("tone", "中立")
    style = role_features.get("style", "正常")
    background = role_features.get("background", "")
    dynasty = role_features.get("dynasty", "現代")
    
    # Apply the role features to the query
    # 讓NPC query內多加一點NPC的資訊，這樣retrive document會更準確（和prompt template無關）
    # 這邊的資訊要和document相關，例如朝代
    chi_query = f"({npc_role}-{dynasty})"+chi_query

    query_info = {
        'query': chi_query,
        'target_lang_code': lang,
        'target_lang': lang_chinese_name,
        'role': npc_role,
        'dynasty': dynasty,
        'background': background,
        'tone': tone,
        'style': style
    }

    rag = LLaMAIndexRAG()
    response = rag.generate_response_with_retrieval(query_info)
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