# load llm via openai
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.chains.prompt_selector import ConditionalPromptSelector
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from rag.rag import RAGInterface

class LangChainRAG(RAGInterface):
    def __init__(self, vectordb):
        super().__init__()
        self.vectordb = vectordb
        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key
        )

        DEFAULT_LLAMA_SEARCH_PROMPT = PromptTemplate(
            input_variables=["question"],
            template="""<<SYS>> \n You are an assistant tasked with improving Google search \
        results. \n <</SYS>> \n\n [INST] Generate THREE Google search queries that \
        are similar to this question. The output should be a numbered list of questions \
        and each should have a question mark at the end: \n\n {question} [/INST]""",
        )

        DEFAULT_SEARCH_PROMPT = PromptTemplate(
            input_variables=["question"],
            template="""You are an assistant tasked with improving Google search \
        results. Generate THREE Google search queries that are similar to \
        this question. The output should be a numbered list of questions and each \
        should have a question mark at the end: {question}""",
        )

        self.QUESTION_PROMPT_SELECTOR = ConditionalPromptSelector(
            default_prompt=DEFAULT_SEARCH_PROMPT,
            conditionals=[(lambda llm: isinstance(llm, ChatOpenAI), DEFAULT_LLAMA_SEARCH_PROMPT)],
        )
    
    def generate_response(self, question):
        prompt = self.QUESTION_PROMPT_SELECTOR.get_prompt(self.llm)

        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        llm_chain.invoke({"question": question})

    def generate_response_with_retrieval(self, question):
        retriever = self.vectordb.as_retriever()

        # make a chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm, 
            chain_type="stuff", # insert doc to prompt
            retriever=retriever, 
            verbose=True,
            return_source_documents=True
        )

        return qa_chain.invoke(question)