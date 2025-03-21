from rag.rag import RAGInterface

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser

import weaviate
from weaviate.connect import ConnectionParams

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.weaviate import WeaviateVectorStore

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core import get_response_synthesizer, PromptTemplate

import os
from app.services.translate_service import Translate
import time

from .personality import get_personality_prompt
import openai

import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('llama_index.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

class LLaMAIndexRAG(RAGInterface):
    def __init__(self):
        super().__init__()
        Settings.llm = OpenAI(
            model="gpt-4", 
            temperature=0.1, 
            # max_tokens=50
        )  
        Settings.embed_model = OpenAIEmbedding() 
        
        # Load data
        filename_fn = lambda filename: {
            "file_name": filename,
            "dynasty": filename.split("/")[-1].split("_")[0],
            "weapon_type": filename.split("/")[-1].split("_")[1],
            "title": filename.split("/")[-1].split("_")[2].replace(".txt", ""),
        }

        ########### INDEXING ###########
        documents = SimpleDirectoryReader(
            input_dir="assets",
            file_metadata=filename_fn,
            recursive=True,
        ).load_data() 

        # Chunk the documents
        node_parser = SimpleNodeParser.from_defaults(
            chunk_size=512, 
            chunk_overlap=128
        )
        # Extract nodes from documents
        nodes = node_parser.get_nodes_from_documents(documents)

        # Build Index (VectorDB)
        client = weaviate.connect_to_wcs(
            cluster_url=os.getenv("WCS_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WCS_API_KEY")),
            headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
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
        ######################

        # The QueryEngine class is equipped with the generator
        # and facilitates the retrieval and generation steps
        assert index is not None
        # self.query_engine = index.as_query_engine()

        # configure retriever
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=3,
        )
        
        # configure response synthesizer
        response_synthesizer = get_response_synthesizer(
            # response_mode="refine"
            response_mode="compact" # less LLM calls
        )
        
        # assemble query engine
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)],
        )

        ##### For simple query LLM #####
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

    def generate_response(self, question):
        pass
    
    def generate_response_with_retrieval(self, query_info):
        personality_type = query_info['personality']
        personality_prompt = get_personality_prompt(personality_type)
        is_rag = query_info['is_rag']

        qa_prompt_str = ""
        if query_info['role'] == "博物館導覽員":
            qa_prompt_str = (
                f"{personality_prompt} \n"

                f"你現在的身份是：{query_info['role']}\n"
                f"你的背景資訊是：{query_info['background']}\n"
                f"你回覆的語調是：{query_info['tone']}\n"
                f"你的回覆風格是：{query_info['style']}\n"

                "你現在正在介紹一個博物館中，所有相關資訊"
                "例如：展覽資訊、展覽路線等等"

                "以下是這個展覽的資訊："
                "---------------------\n"
                "這個展覽主要是三個中國古代的武器展，主要有三個朝代：春秋戰國、宋朝與明朝"
                "三個展區各自有NPC，分別是：白起、岳飛與劉綎，每位NPC都會介紹各自朝代的武器"
                "本展區使用混合實境與人工智慧技術，期望帶給觀展者全新的體驗並提升學習效果"
                "---------------------\n"

                "以下是展覽路線：本展覽按照朝代成環形路線，分別是：春秋戰國、宋朝與明朝"

                "以下是展覽的武器："
                "---------------------\n"
                "春秋戰國：秦國弓弩、吳王夫差矛、越王勾踐劍"
                "宋朝：朴刀、毒藥菸球、神臂弓"
                "明朝：雁翎刀、鐵殼地雷、鳥銃"
                "---------------------\n"

                "以下是展覽時間：早上九點到下午五點"

                "以下是可能相關的武器資訊，請斟酌參考："
                "---------------------\n"
                "{context_str}\n"
                "---------------------\n"

                "根據以上信息與你的個人資訊，請回答以下問題。\n"
                # "回答的內容不要超過50個字。\n"

                "問題：{query_str}\n"

                # f"請將你的回答翻譯成'{query_info['target_lang']}'\n"

                "回答："
            )
        else:
            if is_rag:
                qa_prompt_str = (
                    "# 你的個性 \n"
                    f"{personality_prompt} \n"

                    "# 你的身份 \n"
                    f"你現在的身份是：{query_info['role']}\n"
                    f"你所身處的朝代是：{query_info['dynasty']} (請不要回答超過你朝代的問題或資訊)\n"
                    f"你的背景資訊是：{query_info['background']}\n"
                    # f"你回覆的語調是：{query_info['tone']}\n"
                    # f"你的回覆風格是：{query_info['style']}\n"
                    "\n"
                    "# 上下文資訊： \n"
                    f"以下是{query_info['dynasty']}朝代展覽一些武器的信息。\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"

                    "根據以上信息與你的個人資訊，請回答以下問題。\n"
                    "\n"
                    "# 問題： \n"
                    "{query_str} \n"

                    f"請將你的回答翻譯成'{query_info['target_lang']}'\n"
                    "\n"
                    "# 回答： \n"
                )
            else:
                qa_prompt_str = (
                    f"{personality_prompt} \n"

                    f"你現在的身份是：{query_info['role']}\n"
                    f"你所身處的朝代是：{query_info['dynasty']} (請不要回答超過你朝代的問題或資訊)\n"
                    f"你的背景資訊是：{query_info['background']}\n"
                    # f"你回覆的語調是：{query_info['tone']}\n"
                    # f"你的回覆風格是：{query_info['style']}\n"

                    "根據以上信息與你的個人資訊，請回答以下問題。\n"
                    "使用繁體中文、白話文。\n"

                    f"問題：{query_info['query']}\n"

                    # f"請將你的回答翻譯成'{query_info['target_lang']}'\n"

                    "回答："
                )

        qa_prompt_tmpl = PromptTemplate(qa_prompt_str)
        self.query_engine.update_prompts(
            {
                "response_synthesizer:text_qa_template": qa_prompt_tmpl
            }
        )

        # 這個search engine有兩個prompt template(因為設定成refine mode)
        # 現在修改refine template成中文
        # 翻譯的動作放在這裡
        refine_prompt_str = (
            "原始問題如下：{query_str}\n"
            "我們提供了一個現有的答案：{existing_answer}\n"
            "我們有機會使用下面的更多上下文來改進現有的答案（僅在需要時）。\n"
            "------------\n"
            "{context_msg}\n"
            "------------\n"
            "根據新的上下文，改進原始答案以更好地回答問題。如果上下文沒有幫助，請返回原始答案。\n"

            f"務必將你的回答翻譯成'{query_info['target_lang']}'\n"

            "改進後的回答："
        )
        refine_prompt_tmpl = PromptTemplate(refine_prompt_str)
        self.query_engine.update_prompts(
            {
                "response_synthesizer:refine_template": refine_prompt_tmpl
            }
        )

        # Start total timing
        total_start_time = time.time()

        logger.info(f"Start of Processing "+"="*10)
        # Timing retrieval
        if is_rag:
            retrieval_start_time = time.time()
            retrieved_nodes = self.query_engine.retriever.retrieve(query_info['query'])
            retrieval_end_time = time.time()

            logger.info(f"User's Query: {query_info['query']}")
            # From llamaindex's implementation
            context_str = "\n\n".join([r.get_content() for r in retrieved_nodes])
            synthesized_prompt = qa_prompt_str.format(
                context_str=context_str, query_str=query_info['query']
            )
            logger.info(f"Synthesized Prompt:\n{synthesized_prompt}")

            synthesis_start_time = time.time()
            response = self.query_engine._response_synthesizer.synthesize(
                query=query_info['query'],
                nodes=retrieved_nodes
            )
            synthesis_end_time = time.time()

            logger.info(f"LLM's Response:\n{response}")
            logger.info(f"Retrieval time: {retrieval_end_time - retrieval_start_time:.2f} seconds")
            logger.info(f"Generation time: {synthesis_end_time - synthesis_start_time:.2f} seconds")
        else:
            # Query the LLM directly
            generation_start_time = time.time()
            try:        
                response = self.openai_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": qa_prompt_str
                                }
                            ],
                        }
                    ],
                    model="gpt-4",
                )
            except Exception as e:
                print(f"OpenAI API error: {e}")
                return []

            response_text = response.choices[0].message.content.strip()
            response = {
                "response": response_text,
                "metadata": {}
            }

            generation_end_time = time.time()
            print(f"Generation time: {generation_end_time - generation_start_time:.2f} seconds")

        # End total timing
        total_end_time = time.time()
        logger.info(f"Total time: {total_end_time - total_start_time:.2f} seconds")
        logger.info(f"End of Processing "+"="*10+"\n")

        translator = Translate()
        response_text = response['response'] if not is_rag else response.response

        # if the response is stil not the target language, translate using google translate
        if translator.detect_language(response_text) != query_info['target_lang_code']:
            translated_response_text = translator.translate(response_text, query_info['target_lang_code'])
            if is_rag:
                response.response = translated_response_text
            else:
                response['response'] = translated_response_text

        return response
