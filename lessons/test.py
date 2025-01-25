path = "ml_algo.pdf"

import openai
import os, sys
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

openai.api_key = os.environ['OPENAI_KEY']
os.environ["OPENAI_API_KEY"] ="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"
#"sk-svcacct-3cvULDpqG7CPYdQXCHp3pmpgRGUQJRWfvHu0odM_r1nr9nUv-QS4u_wEPMUb_Pj-7AeOT3BlbkFJWLcb3LagvbIlH1C6YWa-WXJ31iB9ffdQxWfqOCTSdQzbcAeplOZG7Pg686o-coB4qbUA"
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader(path)
pages = loader.load()
page = pages[0]
print(page.page_content[:500])
print(page.metadata)

# For web content
from langchain_community.document_loaders import WebBaseLoader
'''
loader = WebBaseLoader("https://github.com/basecamp/handbook/blob/master/37signals-is-you.md")
pages = loader.load()
page = pages[0]
print(page.page_content[:500])
print(page.metadata)'''


import os
from langchain_community.llms import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
# Fractionner le texte en morceaux plus petits
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
texts = text_splitter.split_documents(pages)
print(len(texts))

# Créer un index vectoriel
#from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma

# Créer des embeddings
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# Construire un index vectoriel
vectorstore = FAISS.from_documents(texts, embeddings)

# Construire le pipeline RAG
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Définir un modèle de langage
llm = OpenAI(model="gpt-3.5.turbo")

# Configurer un retrieveur
retriever = vectorstore.as_retriever()

# Définir un prompt pour la génération de quiz
quiz_prompt = PromptTemplate(
    input_variables=["context"],
    template="""
    Crée un quiz à partir des informations suivantes :
    {context}
    Génère des questions à choix multiples avec 4 options et indique la bonne réponse.
    """
)

# Construire le pipeline RAG
qa_chain = RetrievalQA(
    retriever=retriever,
    llm=llm,
    prompt=quiz_prompt
)


###Générer des questions de quiz
# Entrée utilisateur ou sujet
query = "what are machine learing algo?"

# Générer le quiz
quiz = qa_chain.run(query)
print(quiz)
