from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA,  ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
import openai, os
from django.conf import settings
settings.configure()

#Config
_ = load_dotenv(find_dotenv())
openai.api_key ="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"
os.environ["OPENAI_API_KEY"] ="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"

path= "./cuisine.pdf"
save_path = "faiss_index"
folder_path = os.path.join(settings.MEDIA_ROOT, save_path)


embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
prompt_template = """
Vous êtes un assistant intelligent spécialisé en cuisine. Utilisez les informations suivantes pour répondre à la question de manière claire et concise.



Question :
{question}

Réponse :
"""
prompt = PromptTemplate.from_template(
    prompt_template, 
    #input_variables=[ "question"]  # Inclure les deux variables nécessaires
)


def load_db_qa(path, embeddings, llm):
    vectordb =FAISS.load_local(path, embeddings,allow_dangerous_deserialization=True )
    memory = ConversationBufferMemory(
    memory_key="chat_history",
    output_key="answer",
    return_messages=True
    )
    print("==="*10)
    print(memory)
    print("==="*10)
    
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
       #chain_type_kwargs={"prompt": prompt},
        return_generated_question=True,
        memory=memory,
       
    )
    
    return qa 
 
qa = load_db_qa(save_path, embeddings, llm)
question = "Qu'est ce que la cuisine?"
result = qa.invoke({"question": question})

question = "Comment reussir bien la cuisine ?"
result = qa.invoke({"question": question})
