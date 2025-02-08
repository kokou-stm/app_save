




path = "ml_algo.pdf"

import openai
import os, sys
from dotenv import load_dotenv, find_dotenv
import datetime
from datetime import timedelta
from langchain_openai import OpenAI, ChatOpenAI
#import pandas as pd
from dotenv import load_dotenv, set_key
# callbacks
from langchain_community.callbacks import get_openai_callback
# messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# output parsers
from langchain_core.output_parsers import StrOutputParser
# Créer un index vectoriel
#from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv
from langchain_community.vectorstores import FAISS, Chroma
from langchain.chains import RetrievalQA,  ConversationalRetrievalChain
from api import RESPONSE_JSON

_ = load_dotenv(find_dotenv())
# Build prompt
template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer. 
{context}
Question: {question}
Helpful Answer:"""
number = 5
grade=10
tone = "High"
context= f"""
        
        Vous êtes un expert en création de QCM. A partir du texte ci-dessus, vous devez
        créer un quiz de {number} questions à choix multiples pour les élèves de {grade} dans {tone}.
        Veillez à ce que les questions ne se répètent pas et vérifiez que toutes les questions sont conformes au texte.
        Veillez à formater votre réponse comme le RESPONSE_JSON ci-dessous et utilisez-le comme guide.
        Veillez à faire les QCM {number}.
        ### RESPONSE_JSON
        {RESPONSE_JSON}

        """


template = f"""Vous êtes un expert en création de QCM. 
créer un quiz de {number} questions à choix multiples pour les élèves de {grade} dans {tone}.
 """
QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

openai.api_key = os.environ['OPENAI_KEY']
os.environ["OPENAI_API_KEY"] ="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"
#"sk-svcacct-3cvULDpqG7CPYdQXCHp3pmpgRGUQJRWfvHu0odM_r1nr9nUv-QS4u_wEPMUb_Pj-7AeOT3BlbkFJWLcb3LagvbIlH1C6YWa-WXJ31iB9ffdQxWfqOCTSdQzbcAeplOZG7Pg686o-coB4qbUA"
# Créer des embeddings




def quiz1(request, course_id=None):
    courses = Cours.objects.all() 
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title')
        quiz_description = request.POST.get('quiz_description')
        course_id = request.POST.get('course_id')
        number = request.POST.get('number')
        difficulty = request.POST.get('tone')
        course = Cours.objects.get(id=course_id)
        quiz, created = Quiz.objects.get_or_create(
            quiz_title=quiz_title,
            quiz_description=quiz_description,
            course=course
        )

       
        cours = Cours.objects.get(id = course.id)
        path = cours.file.path
        print("lien: ", path)
        
        data = chat_with_openai(number, difficulty, path)
        data = data
        data = json.loads(data)
        quiz_data = []
        i = 1
        for key, value in data.items():
            
            quiz_element = {
            "no": value["no"],
            "mcq": value["mcq"],
            "options": value["options"],
            "correct": value["correct"]
             }
            print(f"{i}: ", quiz_element)
            quiz_data.append(quiz_element)
            i+=1
            
            question = QuestionAnswers.objects.create(
                quiz=quiz,
                question_text=value['mcq'],
                numero = int(value["no"]),
                options=value["options"],
                great_answer=value['correct'],
                required_time=60,  # Temps requis par défaut
                score=10  # Score par défaut
            )
            
        quiz_data = json.dumps(quiz_data)
        questions = QuestionAnswers.objects.filter(quiz=quiz)

        # Afficher le quiz et les questions dans la vue
        return render(request, 'quiz_details.html', {
            'quiz': quiz,
            'questions': questions
        })
       
        '''for qa in qa_data:
            question = QuestionAnswers.objects.create(
                quiz=quiz,
                question_text=qa.get("question", ""),
               
                great_answer=qa.get("answer", ""),  # Assuming the correct answer is the same as the given one
                required_time=60,  # Set default time or compute based on the question length
                score=10  # Assign a score per question or calculate dynamically
            )
        quiz = Quiz.objects.get(id=quiz.id)
        questions = QuestionAnswers.objects.filter(quiz=quiz)

        return render(request, 'quiz_display.html', {
            'quiz': quiz,
            'questions': questions
        })'''
    if course_id:
       
       courses = Cours.objects.filter(id=course_id)      
    
      
    return render(request, "quiz.html", {'courses': courses, 'is_staff': request.user.is_staff})


#print("Base :" ,os.path.join(settings.BASE_DIR, "/media/uploads/cuisine-proffessionnelle-avancee-1.pdf"))
#print("Base :" ,os.path.join(settings.BASE_DIR, "/media/uploads/cuisine-proffessionnelle-avancee-1.pdf"))
#return render(request, "quiz.html", {'courses': courses})
        #text = parse_file(path)
        #grade=10
        #data = chat_with_openai(text[:1000], number, grade, tone, response_json)
#print(f"Question {value['no']}: {value['mcq']}")
            #print("Options:")
"""for option_key, option_value in value['options'].items():
    print(f"  {option_key}: {option_value}")
print(f"Correct Answer: {value['correct']}")"""
#print("-" * 50)
'''memory = ConversationBufferMemory(
memory_key="chat_history",
output_key="answer",
return_messages=True
)
qa = ConversationalRetrievalChain.from_llm(
    llm_azure,
    retriever=vectordb.as_retriever(),
    return_source_documents=True,
    #chain_type_kwargs={"prompt": prompt},
    return_generated_question=True,
    memory=memory,
    
)

#question = "Qu'est ce que la cuisine?"
result = qa.invoke({"question": question})

return result'''




'''def chat_with_openai(text, number, grade, tone, response_json):
 
    """Communicate with Azure OpenAI to generate questions and answers."""
    open_client = AzureOpenAI(
        api_key='6xv3rz6Asc5Qq86B8vqjhKQzSTUZPmCcSuDm5CLEV5dj9m8gTHlNJQQJ99AKACYeBjFXJ3w3AAABACOGyHXT',
        api_version="2023-12-01-preview",
        azure_endpoint="https://chatlearning.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    )
    
    # Construct the prompt
    prompt = (
        f"""
        Texte : {text}
        Vous êtes un expert en création de QCM. A partir du texte ci-dessus, vous devez
        créer un quiz de {number} questions à choix multiples pour les élèves de {grade} dans {tone}.
        Veillez à ce que les questions ne se répètent pas et vérifiez que toutes les questions sont conformes au texte.
        Veillez à formater votre réponse comme le RESPONSE_JSON ci-dessous et utilisez-le comme guide.
        Veillez à faire les QCM {number}.
        ### RESPONSE_JSON
        {response_json}

        """
        )
   
    open_client = AzureOpenAI(
        api_key='6xv3rz6Asc5Qq86B8vqjhKQzSTUZPmCcSuDm5CLEV5dj9m8gTHlNJQQJ99AKACYeBjFXJ3w3AAABACOGyHXT',
        api_version="2023-12-01-preview",
        azure_endpoint="https://chatlearning.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    )

    chat_completion = open_client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are an expert MCQ maker."},
                {"role": "user", "content": prompt},
            ]
        )

    response = chat_completion.choices[0].message.content
    return response

'''


"""
from langchain.prompts import PromptTemplate
import numpy as np

from langchain_community.vectorstores import FAISS
import sentence_transformers
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
os.environ['HUGGINGFACEHUB_API_TOKEN'] ="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"
# Step 2: Embed and store in a FAISS vector database
import faiss.contrib.torch_utils

huggingface_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-l6-v2",  # alternatively use "sentence-transformers/all-MiniLM-l6-v2" for a light and faster experience.
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

"""


'''docs = relevant_docs(path='./../media/16')
out=chat_with_openai(context=docs, number=6, difficulty="Intermediaire",)
print(out)'''

'''folder_path = os.path.join(settings.MEDIA_ROOT, "videocall_boat")
print("chemin", settings.BASE_DIR)
save_db(os.path.join(settings.BASE_DIR, "lessons/rag_videocall.pdf"), folder_path, embeddings)'''





"""
 az ad sp create-for-rbac --name "chef" --role owner --scopes subscriptions/8bede6c4-35d9-4f6c-976f-d23a506b0f82/resourceGroups/projet
 {
  "clientId": "1e870251-4d06-4f0b-a710-c7ffe6928653",
  "clientSecret": "Oa_8Q~5g_6zpaF6I~0fPYi-rxVPekIc4KbBUycOF",
  "subscriptionId": "8bede6c4-35d9-4f6c-976f-d23a506b0f82",
  "tenantId": "5f78ed12-449b-44ba-9b45-daa863525cf2"
}
"""