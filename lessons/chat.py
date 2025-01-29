from langchain.prompts import PromptTemplate
import faiss.contrib.torch_utils
from langchain_community.vectorstores import FAISS
import sentence_transformers
from langchain_huggingface import HuggingFaceEmbeddings
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader




# Initialisation des embeddings
huggingface_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-l6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

def process_message_with_rag(message, path="cuisine1.pdf"):
    """
    Process a user's message using RAG to return the AI's response and the relevant document paragraph.

    Args:
        message (str): The user's question.
        path (str): The path to the PDF document to use as context.

    Returns:
        dict: A dictionary containing the AI's response and the relevant paragraph.
    """
    # Step 1: Load and split the PDF
    loader = PyPDFLoader(path)
    pages = loader.load()
    print(f'This document has {len(pages)} pages')
    print(pages[0].page_content)
    print(pages[0].metadata)

    # Step 2: Split the document into chunks
    r_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    docs = r_splitter.split_documents(pages)
    print(len(docs))

    # Step 3: Get document embeddings
    doc_embeddings = huggingface_embeddings.embed_documents([doc.page_content for doc in docs])
    print(doc_embeddings)

    # Step 4: Create FAISS index from documents and their embeddings
    vectordb = FAISS.from_documents(docs, huggingface_embeddings)

    # Step 5: Perform similarity search for the query
    relevant_docs = vectordb.similarity_search(query=message, k=3)
    
    return relevant_docs

# Test the function
#response = process_message_with_rag("Qu'est-ce que la cuisine ?", path="cuisine1.pdf")
#print(response)
