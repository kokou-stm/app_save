from langchain_openai import AzureChatOpenAI
from langchain_openai import  AzureOpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import os
os.environ["AZURE_OPENAI_ENDPOINT"]="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
os.environ["AZURE_OPENAI_API_KEY"]="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j"
os.environ["AZURE_OPENAI_API_VERSION"]="2024-05-01-preview"

"""text = "LangChain is the framework for building context-aware reasoning applications"
text2 = "LangChain is the framework for building context-aware reasoning applications"

embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                   azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15",
                                   api_key="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j",
                                   openai_api_version="2023-05-15")
# Create a vector store with a sample text
loader = PyPDFLoader("./rag_videocall.pdf")
pages = loader.load()
print(f'This document have {len(pages)} pages')
print(pages[0].metadata)

r_splitter = RecursiveCharacterTextSplitter(chunk_size= 500, chunk_overlap= 10)
docs = r_splitter.split_documents(pages)
print(len(docs))

vectordb = FAISS.from_documents(docs, embeddings)"""

def save_db_azure(doc_path, folder_path):
    
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Sauvegarder l'index FAISS
    vectordb.save_local(folder_path)
    return 
