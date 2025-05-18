from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import HuggingFacePipeline

def load_knowledge_base(path='data\CustomerFAQ.pdf'):
    loader = PyPDFLoader(path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma.from_documents(docs, embeddings, persist_directory="rag_db")
    return db




def get_chatbot_chain():
    db = load_knowledge_base()
    retriever = db.as_retriever()

    
    model_name = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=512)
    llm = HuggingFacePipeline(pipeline=pipe)

    prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful and friendly customer service chatbot.

Your job is to help users file complaints and answer their questions using the following company policies and FAQs.

Always respond naturally, like you're chatting with a real person. Be empathetic when the user expresses a problem.

Context:
{context}

User:
{question}

Chatbot:
"""
)

    
    qa_chain = load_qa_chain(llm=llm, chain_type="stuff", prompt=prompt)

    return RetrievalQA(combine_documents_chain=qa_chain, retriever=retriever)
