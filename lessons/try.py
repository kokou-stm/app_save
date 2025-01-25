#import packages
from langchain_community.document_loader import PyPDFLoader
from langchain_community.text_split import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import FAISS, Chroma
from langchain_community.embeddings.openai import OpenAIEmbeddings


# Load Documents
path= "ml_algo.pdf"
loader = PyPDFLoader(path)
pages = loader.load()
print(f'{len(pages)}')