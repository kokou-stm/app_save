from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS, Chroma
from langchain_community.llms import HuggingFaceHub
from langchain.chains import QAGenerationChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
#from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.llms import HuggingFacePipeline

from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import openai
from dotenv import load_dotenv, find_dotenv

from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain

from langchain_community.llms import CTransformers
import os
import glob
from django.conf import settings
settings.configure()

_ = load_dotenv(find_dotenv())
openai.api_key ="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"
os.environ["OPENAI_API_KEY"] ="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"
os.environ['HUGGINGFACEHUB_API_TOKEN'] ="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"# Charger les documents

path= "./cuisine.pdf"

save_path = "faiss_index"
folder_path = os.path.join(settings.MEDIA_ROOT, save_path)
embeddings = OpenAIEmbeddings()

"""loader = PyPDFLoader(path)
pages = loader.load()
print(f'This document have {len(pages)} pages')
print(pages[0].metadata)

r_splitter = RecursiveCharacterTextSplitter(chunk_size= 500, chunk_overlap= 10)
docs = r_splitter.split_documents(pages)
print(len(docs))

vectordb = FAISS.from_documents(docs, embeddings)
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
# Sauvegarder l'index FAISS
vectordb.save_local(folder_path)"""

# Générer les embeddings

#doc_embeddings = [embeddings.embed_query(doc) for doc in documents]
#print(doc_embeddings)



#Load Embedding
vectordb = FAISS.load_local(folder_path, embeddings,  allow_dangerous_deserialization=True)
query = "Qu'est-ce que la cuisine ?"
#relevant_docs = vectordb.similarity_search(query=query, k=2)

# Afficher les résultats
"""for doc in relevant_docs:
    print("==="*10)
    print(doc.page_content)
"""


from langchain_community.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Configuration de votre LLM (par exemple, OpenAI)
from langchain_openai import OpenAI, ChatOpenAI
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)  # ou remplacez par le modèle de votre choix

prompt_template = """
Vous êtes un assistant intelligent spécialisé en cuisine. Utilisez les informations suivantes pour répondre à la question de manière claire et concise.

Contexte :
{context}

Question :
{question}

Réponse :
"""
prompt = PromptTemplate.from_template(
    prompt_template, 
    #input_variables=["context", "question"]  # Inclure les deux variables nécessaires
)


# Configurer la chaîne RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,  # Le LLM configuré
    retriever=vectordb.as_retriever(),  # Base vectorielle chargée précédemment
    return_source_documents=True,  # Pour retourner les documents sources (optionnel)
    chain_type_kwargs={"prompt": prompt},  # Ajout du prompt personnalisé
)

query = "Qu'est-ce que la cuisine ?"
result = qa_chain.invoke({"query": query})

# Résultat
print("Réponse :", result["result"])

# Documents sources (si return_source_documents=True)
for doc in result["source_documents"]:
    print("\nSource :")
    print(doc.metadata)
    print(doc.page_content)


#Memory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

retriever=vectordb.as_retriever()
qa = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=retriever,
    memory=memory
)
'''print(f"Index sauvegardé à l'emplacement : {save_path}")
#relevant information
query = "Qu'est ce la cuisine "
relevant_docs = vectordb.similarity_search(query=query, k=3)
print(relevant_docs)'''


