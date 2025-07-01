from django.shortcuts import render, redirect, get_object_or_404
from .forms import CourseForm
from django.http import JsonResponse
from .models import *
from .api import *
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import PyPDF2
import openai
from django.db.models import Q
from django.core.mail import EmailMessage
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ValidationError
import codecs, math

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA,  ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum


from django.db.models.signals import post_save
from django.dispatch import receiver
import json
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl



email_address = settings.EMAIL_HOST_USER
email_password = settings.EMAIL_HOST_PASSWORD

smtp_address = settings.EMAIL_HOST
smtp_port = 465
embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                    azure_endpoint=settings.AZURE_EMBEDDING_ENDPOINT,
                                    api_key=settings.AZURE_EMBEDDING_API_KEY,
                                    openai_api_version="2023-05-15")

open_client = AzureOpenAI(
        api_key=settings.AZURE_CHAT_API_KEY,
        api_version="2023-12-01-preview",
        azure_endpoint=settings.AZURE_CHAT_ENDPOINT
    )

llm_azure = AzureChatOpenAI(
                #openai_api_base="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
                openai_api_version="2024-07-01-preview",
                deployment_name="gpt-35-turbo-chefquiz",
                openai_api_key=settings.AZURE_EMBEDDING_API_KEY,
                openai_api_type='azure',
                azure_endpoint= "https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
            )


@login_required
def index(request):
    etudiants = Etudiant.objects.all()
    print("Etudiants: ", etudiants)
    progress_percentage=0
    cours = Cours.objects.all()
    max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
    print("Max_score: ", max_score)
    if not max_score:
        max_score = 1
    percents_etud = {}
    
    list_etu = Etudiant.objects.all()
    try:
        for etud in list_etu: 
            total_score = sum(score['score'] for score in etud.scores)
            progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
            percents_etud[f"{etud.username.first_name} {etud.username.last_name}"]= progress_etud
    except:
        pass
    percents_etud = dict(sorted(percents_etud.items(), key=lambda item: item[1], reverse=True))

    print("Percent",percents_etud)
    
    if request.user.is_staff:
        prof = Professeur.objects.get(username = request.user)
        cours = Cours.objects.filter(professeur=prof)
        context = {'is_staff': request.user.is_staff, 'cours': cours,  
                   'list_etud': list_etu,
                  'percents_etud': percents_etud}
       
    else:
        etudiant = Etudiant.objects.get(username = request.user)
        scores =  [score['score'] for score in etudiant.scores]
        print("scores! ", scores)
        max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
        print("Max_score: ", max_score)
        try:
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        except:
            pass

      
        context = {'progress_percentage': round(progress_percentage, 2),
                   'is_staff': request.user.is_staff,
                   'cours': cours,
                   'list_etud': list_etu,
                    'percents_etud': percents_etud,
                    'scores': scores}
    
    print(cours)
    return render(request, "index.html", context)


from django.http import JsonResponse
from .models import Cours

def search_courses(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('query', '')
        if query:
            results = Cours.objects.filter(title__icontains=query) | Cours.objects.filter(description__icontains=query)
           
            if results.count()==0:
              results = Cours.objects.all()
            courses = [{'title': cours.title, 'description': cours.description, 'professeur': cours.professeur.username.username, "cours_id":cours.id} for cours in results]
            return JsonResponse({'courses': courses})
    return JsonResponse({'courses': []})


def dash(request):

    progress_percentage=0
    cours = Cours.objects.all()
    quiz = Quiz.objects.all().count()
    quiz_number = [i for i in range(1, 1+quiz)]
    print("Number: ", len(quiz_number))
    max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
    print("Max_score: ", max_score)
    if max_score == None:
        max_score = 1
    percents_etud = {}
    list_etu = Etudiant.objects.all()
    for n, etud in enumerate(list_etu): 
        total_score = sum(score['score'] for score in etud.scores)
        progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
        percents_etud[f"{etud.username.first_name} {etud.username.last_name}"]= progress_etud
        if n==2:
            print("Etudiant: ",etud, len(etud.scores))
    percents_etud = dict(sorted(percents_etud.items(), key=lambda item: item[1], reverse=True))
    moyenne = [[score['score'] for score in etudiant_i.scores] for etudiant_i in list_etu]
    
    #moyenne = [i.extend([0]*(len(quiz_number)-len(i))) for i in moyenne if len(i)< len(quiz_number)]
    for i in range(len(moyenne)):
        if len(moyenne[i]) < len(quiz_number):
            moyenne[i].extend([0] * (len(quiz_number) - len(moyenne[i])))

    best_calcul = [np.mean(np.array(value)) for value in moyenne ]
    context = {
                'is_staff': request.user.is_staff,
                'list_etud': list_etu,
                'percents_etud': percents_etud,
                }
    #print("best_calcul ", best_calcul)
    try:
        best_list =moyenne[best_calcul.index(max(best_calcul))]
        
        #print("moyenne1",moyenne)
        moyenne = np.array(moyenne)#, dtype=np.int32)
        moyenne = list(np.mean(moyenne, axis = 0, dtype=np.int32))
        moyenne = [float(m) for m in moyenne]
        #print("Percent",percents_etud) 

        #print("moyenne", moyenne, len(moyenne))
        #print("best_list", best_list, len(best_list))
        
        context['scores'] =[0]
        context['best_list']= best_list
        context['moyenne'] = moyenne
    except:
        pass
    
    
    
    
    if not request.user.is_staff:
        etudiant = Etudiant.objects.get(username = request.user)
        scores =  [score['score'] for score in etudiant.scores]
        print("scores! ", scores)
        try:
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            context['progress_percentage']= round(progress_percentage, 2)
            context['scores'] =scores
        except:
            pass
    
    context['quiz_number'] =quiz_number
    context['nbre_quiz'] = len(quiz_number)
    print(context['nbre_quiz'])
    return render(request, "dash.html", context)

from django.shortcuts import render
from django.http import Http404
from django.db.models import Sum
import numpy as np

def dash_add(request, id):
    try:
        # Récupérer l'utilisateur correspondant à l'ID
        etudiant = Etudiant.objects.get(id=id)
    except Etudiant.DoesNotExist:
        raise Http404("Utilisateur non trouvé")

    progress_percentage = 0
    cours = Cours.objects.all()
    quiz = Quiz.objects.all().count()
    quiz_number = [i for i in range(1, 1 + quiz)]
    print("Number: ", len(quiz_number))
    
    max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
    if max_score is None:
        max_score = 1

    percents_etud = {}
    list_etu = Etudiant.objects.all()

    # Calcul des pourcentages pour chaque étudiant
    for n, etud in enumerate(list_etu):
        total_score = sum(score['score'] for score in etud.scores)
        progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
        percents_etud[f"{etud.username.first_name} {etud.username.last_name}"] = progress_etud
        if n == 2:
            print("Etudiant: ", etud, len(etud.scores))

    percents_etud = dict(sorted(percents_etud.items(), key=lambda item: item[1], reverse=True))
    moyenne = [[score['score'] for score in etudiant_i.scores] for etudiant_i in list_etu]

    # Compléter les listes si elles sont plus courtes que le nombre de quiz
    for i in range(len(moyenne)):
        if len(moyenne[i]) < len(quiz_number):
            moyenne[i].extend([0] * (len(quiz_number) - len(moyenne[i])))

    best_calcul = [np.mean(np.array(value)) for value in moyenne]
    context = {
        'is_staff': request.user.is_staff,
        'list_etud': list_etu,
        'percents_etud': percents_etud,
    }

    try:
        best_list = moyenne[best_calcul.index(max(best_calcul))]
        moyenne = np.array(moyenne)
        moyenne = list(np.mean(moyenne, axis=0, dtype=np.int32))
        moyenne = [float(m) for m in moyenne]
        context['best_list'] = best_list
        context['moyenne'] = moyenne
    except Exception as e:
        print("Erreur lors des calculs : ", e)

    # Calculer les scores et progression pour l'étudiant actuel
    scores = [score['score'] for score in etudiant.scores]
    try:
        total_score = sum(score['score'] for score in etudiant.scores)
        progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        context['progress_percentage'] = round(progress_percentage, 2)
        context['scores'] = scores
    except Exception as e:
        print("Erreur pour l'étudiant : ", e)

    context['quiz_number'] = quiz_number
    context['nbre_quiz'] = len(quiz_number)
    print(context['nbre_quiz'])

    # Rendre la page HTML avec le contexte
    return render(request, "dash.html", context)


def profile(request):
    membre=""
    try: 
        membre = get_object_or_404(Etudiant, username=request.user)
    except:
        membre = get_object_or_404(Professeur, username=request.user)

    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        user = get_object_or_404(User, username=request.user)
        print(request.POST.get('firstname'), user)
        user.first_name = request.POST.get('firstname',  membre.username.first_name)
        user.last_name = request.POST.get('lastname', membre.username.last_name)
        user.save()
        membre.phone = request.POST.get('phone', membre.phone)
        membre.numero_de_carte = request.POST.get('numero_de_carte', membre.numero_de_carte)
        
        # Sauvegarder les modifications
        membre.save()
        messages.info(request, f"Modifications enregistrés !")
        return redirect('index')  # Redirige vers la page du profil (ou une autre page)
    
    context = {}
    if request.user.is_staff:
        context = {'is_staff': request.user.is_staff, 'membre': membre}
       
    else:
        progress_percentage=0
       
        etudiant = Etudiant.objects.get(username = request.user)
        max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
        print("Max_score: ", max_score)
        try:
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        except:
            pass
        context = {'progress_percentage': round(progress_percentage, 2),
                   'is_staff': request.user.is_staff,'membre': membre
                   }
    

    return render(request, 'profile.html', context)


def faquestion(request):
    print('Og')
    
    return render(request, "faquestion.html")

@login_required
def home(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')

        # Validation simple des champs
        if not title or not description or not file:
            return render(request, 'home.html', {'error': 'Tous les champs sont obligatoires.'})
        
        # Sauvegarder les données dans le modèle
        course = Cours(title=title, description=description, file=file)
        course.save()
        
        courses = Cours.objects.all()
        return render(request, "quiz.html", {'courses': courses})

    return render(request, 'home.html')


@login_required
def upload_cours(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')

        # Validation simple des champs
        if not title or not description or not file:
            return render(request, 'upload_cours.html', {'error': 'Tous les champs sont obligatoires.'})
        prof = Professeur.objects.get(username = request.user)
        # Sauvegarder les données dans le modèle
        course = Cours(title=title, description=description, file=file, professeur = prof)
        course.save()
        save_path  = f"{course.id}"
        folder_path = os.path.join(settings.MEDIA_ROOT, save_path)
        print("folderpath: ", folder_path)
        cours_path = course.file.url
        
        save_db(cours_path, folder_path, embeddings, course_id=f"{course.id}")
        #process_message_with_rag(cours)
        messages.info(request, f"{title} a été bien ajouté.")
        redirect_url = reverse('quiz_creator', args=[course.id])
        return JsonResponse({'redirect_url': redirect_url})
        
        #return redirect('quiz_creator', course_id=course.id)

    return render(request, 'upload_cours.html')



def delete_course(request, course_id):
    course = get_object_or_404(Cours, id=course_id)
    course.delete()
    messages.info(request, f"{course.title} a été supprimé .")
    return JsonResponse({'message': 'Cours supprimé'})


def quiz(request, course_id=None):
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
            course=course, 
            
        )

        # Générer le quiz (logique existante)
        cours = Cours.objects.get(id=course.id)
        path = cours.file.url
        '''text = parse_file(path)
        grade = 5
        data = chat_with_openai(text[:1000], number, grade, tone, response_json)
        data = json.loads(data)
        '''
        data = chat_with_openai(number, difficulty, f"{course_id}")
        print("==="*4)
        data = json.loads(data)
        print("===="*4)
        

        for key, value in data.items():
            QuestionAnswers.objects.create(
                quiz=quiz,
                question_text=value['mcq'],
                numero=int(value["no"]),
                options=value["options"],
                great_answer=value['correct'],
                required_time=60,
                score=10,
            )
        quiz.max_score = 10*int(len(data.items()))
        quiz.save()
        etudiants = Etudiant.objects.all()
        print("Etudiants: ", etudiants)
        for etudiant in etudiants:
            if etudiant.scores is None:
                etudiant.scores = []
            print(etudiant.scores,10*int(len(data.items())) )
            etudiant.scores.append({
                'quiz_id': quiz.id,
                'score': 0,
                'max_score': 10*int(len(data.items())),
            })
        # Retourne l'URL de redirection
        
        redirect_url = reverse('quiz_details', args=[quiz.id])
        return JsonResponse({'redirect_url': redirect_url})

    if course_id:
        courses = Cours.objects.filter(id=course_id)

    return render(request, "quiz.html", {'courses': courses, 'is_staff': request.user.is_staff})


def update_quiz(request, quiz_id=None):

    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
       
        for key, value in request.POST.items():
            # Ignorer les champs CSRF et non liés aux questions
            
            if key.startswith('question_text_'):
                question_id = key.split('_')[-1]  # Extraire l'ID de la question
                question_text = value
                
                # Récupérer les options pour cette question
                options = {}
                great_answer = ""
                for option_key, option_value in request.POST.items():
                    if option_key.startswith(f'option_{question_id}_'):
                        if "greatanswer" in option_key:
                            option_letter = option_key.split('_')[-2]
                            great_answer = option_value
                        else:
                          option_letter = option_key.split('_')[-1]  # Lettre de l'option (A, B, etc.)
                        options[option_letter] = option_value
                #print('options: ',question_id, question_text, options)
                # Enregistrer la question et ses options dans la base de données
                questions_answers = QuestionAnswers.objects.get(id=question_id)
                questions_answers.question_text = question_text
                questions_answers.options=options
                questions_answers.great_answer = great_answer
                questions_answers.save()
        messages.info(request, "Modifications enregistrés !")
        # Rediriger après soumission
        return redirect("index")  # Changez l'URL en fonction de vos besoins

    return render(request, 'quiz_form.html', {'quiz': quiz})



def generate_quiz(path_quiz):
   return

def upload_file(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'upload_success.html')  # Page de confirmation
    else:
        form = CourseForm()
    return render(request, 'upload_file.html', {'form': form})


def prof_dash(request):
    return render(request, 'prof_dash.html')

@login_required
def listecours(request):
    cours = Cours.objects.all()
    context = {'cours': cours, 'is_staff': request.user.is_staff}
    if not  request.user.is_staff:
        etudiant = Etudiant.objects.get(username = request.user)
        scores =  [score['score'] for score in etudiant.scores]
        print("scores! ", scores)
        max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
        print("Max_score: ", max_score)
        try:
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            context['progress_percentage']= round(progress_percentage, 2)
         
        except:
            pass
    
        
            
    return render(request, 'lescours.html', context)

def course_details(request, course_id):
    # Récupération du cours
    course = get_object_or_404(Cours, id=course_id)
   
    print('Chemin: ', course.file.url)
    quizzes = Quiz.objects.filter(course=course)
    context = {'course': course, 'is_staff': request.user.is_staff, 'quizzes': quizzes}
    # Récupération du quiz associé
    
    print("Quiz: ", quizzes)
    scores = []
    if not request.user.is_staff:
        etudiant = Etudiant.objects.get(username = request.user)
        
        
        max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
        print("Max_score: ", max_score)
        try:
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            context['progress_percentage']= round(progress_percentage, 2)
         
        except:
            pass

        for quizze in quizzes:
            score_dict = next((score for score in etudiant.scores if score['quiz_id'] == quizze.id), 0)
            print("val: ",score_dict)
            if score_dict == 0:
                score_val = 0
            else:
                score_val =  score_dict['score']
            scores.append({
                "quiz_i": quizze,
                "score" : score_val #, score_dict['max_score']
            })
        
    
    context['scores']= scores
    print("Context: ", context)
    return render(request, 'cours_details.html', context)


def quiz_details(request, quiz_id):
    # Récupération du cours
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    
    question_answers= QuestionAnswers.objects.filter(quiz=quiz)
    
    context = {
        'questions': question_answers,
        'quiz': quiz,
        'is_staff': request.user.is_staff
        
    }
    print("Quiz: ",context)
    return render(request, 'quiz_details.html', context)

@login_required
def quiz_score(request, quiz_id):
    # Récupérer le quiz et les questions associées
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = QuestionAnswers.objects.filter(quiz=quiz)

    # Si l'utilisateur soumet ses réponses
    if request.method == 'POST':
        print("Data: ", request.POST)
        total_score = 0
        max_score = 0
        # Calculer le score de l'étudiant
        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")
            user_answer1 = question.options.get(user_answer, None)
            #print(f"{question.options.get(user_answer, None)}")
            question.user_answer = user_answer
            question.save()
            correct_answer = question.great_answer
            print("Correct answer: ", correct_answer)
            score = 10 #question.score or 0

            # Vérifier la réponse de l'utilisateur
            if (user_answer == correct_answer) or (user_answer1 == correct_answer) :
                total_score += score
            else:
                print("User: ", user_answer)
                print("Correct: ", correct_answer)
            
            max_score += score

        # Enregistrer le score de l'étudiant dans la base de données
        etudiant = Etudiant.objects.get(username=request.user)
        if etudiant.scores is None:
            etudiant.scores = []
        messages.success(request,  f"""Votre Score: {total_score}/{max_score} Soit {round((total_score/max_score)*100, 2)}%""")
        #quiz.total_score = total_score
        quiz.max_score=max_score
        quiz.save()
        for existing_score in etudiant.scores:
            if existing_score['quiz_id'] == quiz.id:
                # Mise à jour des données existantes
                existing_score['score'] = score
                existing_score['max_score'] = max_score
                break
        else:
            # Ajouter une nouvelle entrée si le quiz_id n'existe pas
            etudiant.scores.append({
                'quiz_id': quiz_id,
                'score': score,
                'max_score': max_score,
            })
        
        
        for existing_score in etudiant.scores:
            if existing_score['quiz_id'] == quiz.id:
                # Mise à jour des données existantes
                existing_score['score'] = score
                existing_score['max_score'] = max_score
                break
        else:
            # Ajouter une nouvelle entrée si le quiz_id n'existe pas
            etudiant.scores.append({
                'quiz_id': quiz_id,
                'score': score,
                'max_score': max_score,
            })
        etudiant.save()
        # Rediriger vers une page de résultat ou afficher un message de succès
        return render(request, 'quiz_result.html', {
            'quiz': quiz,
            'total_score': total_score,
            'max_score': max_score,
            'questions': questions,
            'is_staff': request.user.is_staff,
                            })

    return render(request, 'quiz_display.html', {'quiz': quiz, 'questions': questions})

def popupquiz(request, add_val=None):
    print(request.build_absolute_uri())
    mess = ""
    print("add_val", str(add_val))
    if str(add_val) == 'add':
        mess= "Passez les quiz et obtenez decouvrez la correction par IA." 
    elif str(add_val) == 'pop':
        mess= "Selectionnez un cours, et decouvrez les quiz associés."
    messages.info(request, str(mess))
    return redirect("index")

def register(request):
    mess = ""
    if request.method == "POST":
        
        print("="*5, "NEW REGISTRATION", "="*5)
        
        prenom= request.POST.get("firstname", None)
        nom= request.POST.get("lastname", None)
        username = ''.join(f"{nom}{prenom}".split())
        email = request.POST.get("email", None)
        pass1 = request.POST.get("password1", None)
        pass2 = request.POST.get("password2", None)
        print(username, email, pass1, pass2)
        try:
            validate_email(email)
        except:
            mess = "Invalid Email"
        if pass1 != pass2 :
            mess += " Password not match"
        if User.objects.filter(Q(email= email)| Q(username=username)).first():
            mess += f" Exist user with email {email}"
        print("Message: ", mess)
        if mess=="":
            try:
                    validate_password(pass1)
                    user = User(username= username, email = email, first_name=prenom, last_name=nom)
                    user.save()
                    user.password = pass1
                    user.set_password(user.password)
                    user.save()
                    

                    #try:
                    # Essayer de récupérer l'étudiant et de lui attribuer des scores
                    etudiant, created = Etudiant.objects.get_or_create(username=user)
                    if etudiant.scores is None:
                        etudiant.scores = []
                    
                    quizes = Quiz.objects.all()
                    for quiz in quizes:
                        etudiant.scores.append({
                            'quiz_id': quiz.id,
                            'score': 0,
                            'max_score': quiz.max_score,
                        })
                    etudiant.save()

                    ''' except Exception as e:
                        print('Erreur lors de l\'assignation des scores:', e)
                        messages.error(request, "Une erreur est survenue lors de l'initialisation des scores.")'''
                




                    subject = "Bienvenue sur ChefQuiz !"

                    email_message = f"""
                    <!DOCTYPE html>
                    <html lang="fr">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Bienvenue sur ChefQuiz !</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background-color: #f4f7fa;
                                color: #333;
                                margin: 0;
                                padding: 0;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 20px auto;
                                padding: 20px;
                                background-color: #ffffff;
                                border-radius: 8px;
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            }}
                            h1 {{
                                color: #d9534f;
                                text-align: center;
                            }}
                            p {{
                                font-size: 16px;
                                line-height: 1.6;
                                margin: 10px 0;
                            }}
                            ul {{
                                font-size: 16px;
                                margin: 10px 0;
                            }}
                            li {{
                                margin-bottom: 8px;
                            }}
                            .highlight {{
                                font-weight: bold;
                                color: #d9534f;
                            }}
                            .footer {{
                                text-align: center;
                                font-size: 14px;
                                margin-top: 20px;
                                color: #888;
                            }}
                            .button {{
                                display: inline-block;
                                padding: 12px 20px;
                                margin-top: 20px;
                                background-color: #d9534f;
                                color: #fff;
                                text-decoration: none;
                                border-radius: 4px;
                                text-align: center;
                            }}
                            .button:hover {{
                                background-color: #c9302c;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>Bienvenue sur ChefQuiz, {prenom} ! 👩‍🍳👨‍🍳</h1>
                            <p>Bonjour {prenom},</p>
                            <p>Bienvenue sur <span class="highlight">ChefQuiz</span>, la plateforme innovante qui vous accompagne dans votre apprentissage culinaire ! Nous sommes ravis de vous avoir parmi nous et convaincus que cette aventure sera aussi savoureuse qu’enrichissante.</p>
                            <p><span class="highlight">ChefQuiz</span> utilise une technologie avancée, le modèle RAG (Retrieval-Augmented Generation), pour vous proposer des quiz personnalisés à partir des cours publiés par vos professeurs. Cela vous permet de tester vos connaissances de manière interactive et dynamique, tout en renforçant les compétences acquises dans chaque leçon.</p>
                            <p><strong>Voici ce que vous pouvez attendre de ChefQuiz :</strong></p>
                            <ul>
                                <li><span class="highlight">Des quiz adaptés à vos cours :</span> Chaque question générée est directement liée au contenu de vos leçons, garantissant une révision ciblée et efficace.</li>
                                <li><span class="highlight">Une progression suivie en temps réel :</span> Vous pourrez suivre votre performance et identifier les sujets à approfondir pour progresser.</li>
                                <li><span class="highlight">Une expérience d’apprentissage flexible :</span> Les quiz sont accessibles à tout moment, pour vous permettre d’apprendre à votre rythme et selon vos disponibilités.</li>
                            </ul>
                            <p>Pour commencer, explorez vos cours disponibles sur votre tableau de bord, et laissez-vous guider par les quiz adaptés à chaque leçon. Plus vous interagissez avec le contenu, plus vous renforcez vos compétences culinaires !</p>
                            <p>Si vous avez des questions ou besoin d’aide, n’hésitez pas à nous contacter. Notre équipe est là pour vous accompagner à chaque étape de votre apprentissage.</p>
                            <p>Bon apprentissage et à très bientôt sur <span class="highlight">ChefQuiz</span> !</p>
                            <div class="footer">
                                <p>Cordialement,</p>
                                <p>L’équipe ChefQuiz</p>
                                <p>03 27 51 77 47</p>
                                <p><a href="https://chefquiz.de" target="_blank">https://chefquiz.de</a></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """

                    emailsender(subject, email_message, email_address,  user.email)

                    mess = f"Welcome, {prenom}! Your account has been successfully created. To activate your account, please retrieve your verification code from the email sent to {user.email}"
                        
                    messages.info(request, mess)

                    verification_code, created = VerificationCode.objects.get_or_create(user=user)
                    verification_code.generate_code()
                    print(verification_code.code)
                    
                    subject = "Votre code de vérification ChefQuiz"

                    email_message = f"""
                    <!DOCTYPE html>
                    <html lang="fr">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Code de vérification</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background-color: #f4f7fa;
                                color: #333;
                                margin: 0;
                                padding: 0;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 20px auto;
                                padding: 20px;
                                background-color: #ffffff;
                                border-radius: 8px;
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            }}
                            h1 {{
                                color: #d9534f;
                                text-align: center;
                            }}
                            p {{
                                font-size: 16px;
                                line-height: 1.6;
                                margin: 10px 0;
                            }}
                            .code-box {{
                                text-align: center;
                                margin: 20px 0;
                            }}
                            .code {{
                                display: inline-block;
                                font-size: 24px;
                                font-weight: bold;
                                background-color: #f8f9fa;
                                padding: 10px 20px;
                                border: 1px solid #ddd;
                                border-radius: 5px;
                                color: #d9534f;
                                letter-spacing: 2px;
                            }}
                            .footer {{
                                text-align: center;
                                font-size: 14px;
                                margin-top: 20px;
                                color: #888;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>Votre code de vérification</h1>
                            <p>Bonjour {prenom},</p>
                            <p>Voici votre code de vérification pour accéder à votre compte ChefQuiz. Entrez ce code sur notre site pour compléter votre connexion ou validation :</p>
                            <div class="code-box">
                                <span class="code">{verification_code.code}</span>
                            </div>
                            <p>Ce code est valide pendant les <strong>30 prochaines minutes</strong>. Si vous n’avez pas demandé ce code, veuillez ignorer cet e-mail ou nous contacter immédiatement.</p>
                            <div class="footer">
                                <p>Merci de faire confiance à <strong>ChefQuiz</strong> !</p>
                                <p>03 27 51 77 47 | <a href="https://chefquiz.de" target="_blank">https://chefquiz.de</a></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """

                    emailsender(subject, email_message, email_address, user.email)
                

                    #Membre.objects.create(user=user, email=email, nom= username ).save()
                    return redirect("code")
            except Exception as e:
                    print("error: ", type(e), e)
                    #err = " ".join(e)
                    
                    messages.error(request, f"Erreur survenue lors de la creation de compte, veuillez reessayer.")
                    return render(request, template_name="register.html")
            
        else:
            messages.info(request, mess)

    return render(request, template_name="register.html")


def connection(request):
    mess = ""

    '''if request.user.is_authenticated:
         return redirect("dashboard")'''
    if request.method == "POST":
        
        print("="*5, "NEW CONECTION", "="*5)
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            validate_email(email)
        except:
            mess = "Invalid Email !!!"
        #authen = User.lo
        if mess=="":
            user = User.objects.filter(email= email).first()
            if user:
                auth_user= authenticate(username= user.username, password= password)
                if auth_user:
                    print("Utilisateur infos: ", auth_user.username, auth_user.email)
                    login(request, auth_user)
                    
                    return redirect("index")
                else :
                    mess = "Incorrect password"
            else:
                mess = "user does not exist"
            
        messages.info(request, mess)

    return render(request, template_name="login.html")



from django.core.mail import send_mail  # Use Django's email sending
from django.utils.html import strip_tags # For plain text version
from django.template.loader import render_to_string # For cleaner HTML

def forgotpassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            current_site = request.META["HTTP_HOST"] # Replace with your actual domain
            subject = "Password Reset Chefquiz"

            # Use a template for cleaner HTML
            html_message = render_to_string('account/password_reset_email.html', {
                'user': user,
                'reset_link': f"{current_site}/updatepassword/{token}/{uid}/",
            })

            plain_message = strip_tags(html_message) # Create plain text version

            send_mail(
                subject,
                plain_message,  # Send plain text version
                email_address,  # From email
                [user.email],  # To email(s)
                html_message=html_message,  # Send HTML version
            )

            messages.success(request, f"A reset password email has been sent to {user.email}.")
        else:
            messages.success(request, "The email address does not match any account.")

    return render(request, "account/forgot_password.html")


def forgotpassword1(request):
     if request.method =="POST":
          username = request.user.username
          email = request.POST.get("email")
          user = User.objects.filter(email= email).first()
          print("user", user )
          if user:
               print("User exist")
               token = default_token_generator.make_token(user)
               uid = urlsafe_base64_encode(force_bytes(user.id))
               current_host =request.META["HTTP_HOST"]
               
               Subject = "Password Reset Chefquiz "
               
               code_message = f"""
                <!DOCTYPE html>
                <html lang="fr">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Réinitialisation de mot de passe</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" 
                        integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: #f8f9fa;
                            color: #333;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 30px auto;
                            padding: 20px;
                            background-color: #ffffff;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        }}
                        h2 {{
                            color: #007bff;
                            text-align: center;
                            margin-bottom: 20px;
                        }}
                        p {{
                            font-size: 16px;
                            line-height: 1.6;
                            margin: 15px 0;
                        }}
                        .link-container {{
                            text-align: center;
                            margin-top: 20px;
                        }}
                        .button {{
                        display: inline-block;
                        padding: 12px 20px;
                        background-color: #007bff;
                        color: #ffffff;
                        text-decoration: none;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                        border: none;
                        cursor: pointer; /* Assurez-vous d'avoir cette ligne */
                        pointer-events: auto; /* Ajouter cette ligne */
                    }}
                        .button:hover {{
                            background-color: #0056b3;
                        }}
                                        .footer {{
                            text-align: center;
                            margin-top: 30px;
                            font-size: 14px;
                            color: #888;
                        }}
                        .footer a {{
                            color: #007bff;
                            text-decoration: none;
                        }}
                        .footer a:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Réinitialisation de mot de passe</h2>
                        <p>Bonjour <strong>{username}</strong>,</p>
                        <p>Vous avez demandé à réinitialiser votre mot de passe pour accéder à votre compte ChefQuiz. Cliquez sur le lien ci-dessous pour choisir un nouveau mot de passe :</p>
                        <div class="link-container">
                            <a href="{current_host}/updatepassword/{token}/{uid}/" class="button">Réinitialiser mon mot de passe</a>
                        </div>
                        <p>Ce lien est valable pendant <strong>1 heure</strong>. Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet e-mail en toute sécurité.</p>
                        <div class="footer">
                            <p>Merci,</p>
                            <p>L'équipe <strong>ChefQuiz</strong></p>
                            <p><a href="https://chefquiz.de">chefquiz.de</a> | +33 327 517 747</p>
                        </div>
                    </div>
                    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" 
                            integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN6jIeHz" crossorigin="anonymous"></script>
                </body>
                </html>
                """
               emailsender(Subject, code_message, email_address, user.email)

              
               messages.success(request, f"We have send a reset password email to {user.email}, open it and follow the instructions !",)
          else:
               print("User not exist")
               messages.success(request,"L'email ne correspond à aucun compte, veuillez vérifier et reessayer.")
     return render(request, "account/forgot_password.html")


def updatepassword(request, token, uid):
    print(request.user.username, token, uid)
    try:
            user_id = urlsafe_base64_decode(uid)
            decode_uid = codecs.decode(user_id, "utf-8")
            user = User.objects.get(id= decode_uid)
                         
    except:
            return HttpResponseForbidden("You are not authorize to edit this page")
    print("Utilisateur: ", user)
    checktoken = default_token_generator.check_token( user, token)
    if not checktoken:
        return HttpResponseForbidden("You are not authorize to edit this page, your token is not valid or have expired")
    if request.method =="POST":
            user = User.objects.get(id= decode_uid)
            pass1= request.POST.get('pass1')
            pass2= request.POST.get('pass2')
            if pass1 == pass2:
                 try:
                        validate_password(pass1)
                        user.password = pass1
                        user.set_password(user.password)
                        user.save()
                        messages.success(request, "Your password is update sucessfully")
                 except ValidationError as e:
                      messages.error(request, str(e))
                      
                       
                 return redirect('login')
            else:
                 messages.eror(request, "Passwords not match")
        
    return render(request, "account/update_password.html")

def code(request):
    mess = ""

    if request.method == "POST":
        print("=" * 5, "NEW CONNECTION_code", "=" * 5)

        email = request.POST.get("email")
        code_v = request.POST.get("code")
        
        # Vérifier si l'email est fourni et s'il existe dans la base de données
        if not email:
            mess = "L'email est requis."
            messages.error(request, mess)
            return render(request, "code.html")
        
        user = User.objects.filter(email=email).first()
        
        # Si l'utilisateur n'existe pas
        if not user:
            mess = "Aucun utilisateur trouvé avec cet email."
            messages.error(request, mess)
            return render(request, "code.html")

        try:
            print("1hjjk")
            # Récupérer ou créer le code de vérification pour l'utilisateur
            verification_code, created = VerificationCode.objects.get_or_create(user=user)
            
            print("code: ", verification_code.code)

            # Vérification du code
            if str(code_v) == str(verification_code.code):
                messages.success(request, "Votre compte est activé. Connectez-vous!")

               
                # Redirection vers la page de connexion
                return redirect("login")

            else:
                # Code incorrect
                mess = "Code de vérification invalide."
                messages.info(request, mess)

        except Exception as e:
            # Gérer les erreurs dans le bloc try, par exemple, si la création du code échoue
            print("Erreur lors de la récupération du code:", str(e))
            mess = "Une erreur est survenue. Veuillez vérifier l'email et/ou le code."
            messages.error(request, mess)

    return render(request, template_name="code.html" )

def deconnexion(request):
         print("Deconnexion")
         logout(request)
         return redirect("login")
    
@login_required
def contact(request):
    context={}
    if request.method =="POST":
        
            Subject = request.POST.get("subject")

            Gmail = request.POST.get("email")
            message = f"Nom d'utilisateur: {request.user.username} " f'Adresse mail: {Gmail}\n' + request.POST.get("message")
            print(message)
            
            print(Gmail,  [settings.EMAIL_HOST_USER])
            emailsender(Subject, message, settings.EMAIL_HOST_USER, settings.EMAIL_HOST_USER, contact="yes")
            

            messages.success(request, "Nous avons bien reçu votre message. Nous vous revenons très bientot !!!")
           

            #return JsonResponse({'success': True, 'mess': "Your message is succesfull send  !!!"})
            return redirect("index")
        #return HttpResponseRedirect("y")
        #return HttpResponse("yours message is succesfull send")
    return redirect("index")

def create_user_profile(user):
    """
    Crée un profil correspondant (Etudiant ou Professeur) en fonction du rôle de l'utilisateur.
    """
    if user.is_staff:
        Professeur.objects.create(
            username=user,
            nom=user.last_name,  # Utilisez les informations disponibles
            email=user.email
        )
    else:
        Etudiant.objects.create(
            username=user,
            nom=user.last_name,  # Utilisez les informations disponibles
            email=user.email
        )

@receiver(post_save, sender=User)
def manage_user_role(sender, instance, created, **kwargs):
    """
    Gère automatiquement les profils Etudiant et Professeur en fonction du rôle is_staff d'un utilisateur.
    """
    if created:
        # Lorsqu'un utilisateur est créé pour la première fois
        if instance.is_staff:
            Professeur.objects.create(
                username=instance,
                nom=instance.last_name or "N/A",  # Nom par défaut si vide
                email=instance.email
            )
        else:
            Etudiant.objects.create(
                username=instance,
                nom=instance.last_name or "N/A",
                email=instance.email
            )
    else:
        # Lorsqu'un utilisateur existant est mis à jour
        if instance.is_staff:
            # Vérifiez s'il n'est pas déjà professeur
            if not Professeur.objects.filter(username=instance).exists():
                # Supprimez l'ancien profil étudiant
                Etudiant.objects.filter(username=instance).delete()
                # Créez un profil professeur
                Professeur.objects.create(
                    username=instance,
                    nom=instance.last_name or "N/A",
                    email=instance.email
                )
        else:
            # Vérifiez s'il n'est pas déjà étudiant
            if not Etudiant.objects.filter(username=instance).exists():
                # Supprimez l'ancien profil professeur
                Professeur.objects.filter(username=instance).delete()
                # Créez un profil étudiant
                Etudiant.objects.create(
                    username=instance,
                    nom=instance.last_name or "N/A",
                    email=instance.email
                )


import shutil



@csrf_exempt
def ask_ia(request, course_id=None):
    cours = Cours.objects.get(id=course_id)
    print('Chemin: ', cours.file.url)
    print('body: ', request.body)

    if request.method == 'POST':
        print("Ok")
        data = json.loads(request.body)
        user_message = data.get('message', '')
        print('La question: ', user_message)
        path = cours.file.url

        # CAS 1 : Démarrer le quiz
        if user_message.strip().upper() == "START_QUIZ":
            quiz_html = generate_quiz_from_course(cours)
            return JsonResponse({
                'response': "Contenu du Quiz: ",
                'quiz_html': quiz_html,
                'source_documents': []
            })


        # CAS 2 : Requête normale à l'IA
        ia_response = load_db_qa(f"{course_id}", embeddings, user_message)
        print("ia: ", ia_response)

        source_documents = []
        for doc in ia_response.get("source_documents", []):
            doc_info = {
                "source": cours.file.url,
                "page_label": doc.metadata.get('page_label', 'Non spécifié'),
                "page_content": doc.page_content[:500] + "..."
            }
            source_documents.append(doc_info)

        return JsonResponse({
            'response': ia_response["answer"],
            'source_documents': source_documents
        })

    # Nettoyage des fichiers temporaires
    folder_path = os.path.join(settings.MEDIA_ROOT, f"{course_id}")
    temp_file_path_faiss = os.path.join(folder_path, "index.faiss")
    temp_file_path_pickle = os.path.join(folder_path, "index.pkl")

    if os.path.exists(temp_file_path_faiss):
        os.remove(temp_file_path_faiss)
        print(f"Fichier temporaire {temp_file_path_faiss} supprimé.")

    if os.path.exists(temp_file_path_pickle):
        os.remove(temp_file_path_pickle)
        print(f"Fichier temporaire {temp_file_path_pickle} supprimé.")

    return render(request, "chat.html", {"course_id": course_id, "cours": cours})


import json, ast

import re
import json
import time


def generate_quiz_from_course(cours, num_questions=3):

    form_id = f"quiz-form-{int(time.time())}"
    prompt = f"""
    Génère un quiz de {num_questions} questions au minimum  sur ce cours.
    Formate la réponse strictement en JSON comme dans cet exemple :
    [
        {{
            "question": "Quel est le rôle des protéines dans l'alimentation ?",
            "options": ["Fournir de l'énergie", "Aider à la croissance", "Réguler le métabolisme", "Autre"],
            "answer": 1
        }}
    ]
    Pas de texte en dehors du JSON.
    """

    try:
        # Appel à l'IA pour obtenir une réponse
        ia_response = load_db_qa(str(cours.id), embeddings, prompt)
        raw_answer = ia_response.get("answer", "")

        # Extraction de JSON strictement valide
        json_like = raw_answer[raw_answer.find("["):raw_answer.rfind("]") + 1]

        # Validation JSON sans manipulation complexe
        quiz = json.loads(json_like)

        # Génération du HTML pour affichage
        quiz_html = '<form class="quiz-form" id="{form_id}">'
        for idx, q in enumerate(quiz):
            quiz_html += f'<div class="quiz-question"><p><strong>Q{idx+1}: {q["question"]}</strong></p>'
            for opt_idx, option in enumerate(q["options"]):
                quiz_html += f'''
                    <label>
                        <input type="radio" name="q{idx}" value="{opt_idx}">
                        {option}
                    </label><br>
                '''
            quiz_html += '</div><br>'
        quiz_html += '<div style="text-align: right;"><button type="submit" class="submit-quiz-btn btn btn-primary">Soumettre</button></div></form>'

        return quiz_html

    except json.JSONDecodeError:
        print("Erreur : Problème de format JSON.")
        return "<p>Erreur : Le format JSON est invalide. Veuillez réessayer.</p>"
    except Exception as e:
        print("Erreur lors de la génération du quiz :", str(e))
        return "<p>Erreur lors de la génération du quiz. Veuillez réessayer.</p>"



def parse_file(path):
    file = open(path, "rb")
    if file.name.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except PyPDF2.utils.PdfReadError:
            raise Exception("Error reading the PDF file.")

    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")

    else:
        raise Exception(
            "Unsupported file format. Only PDF and TXT files are supported."
        )
    
def chat(document_text, question,cours):
    
    prompt = (
        f"Vous êtes un expert en cuisine et un formateur aidant un étudiant à se préparer pour son examen de cuisine. "
        f"L'étudiant étudie le contenu suivant tiré de son document :\n\n"
        f"{document_text}\n\n"
        f"L'étudiant pose la question suivante : {question}\n\n"
        f"Fournissez une réponse résumée, pratique et facile à comprendre, comme si vous étiez un instructeur en cuisine. "
        f"Répondez dans la langue dans laquelle la question est posée."
    )

    # Appel à l'API GPT
    chat_completion = open_client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": "Vous êtes un expert en cuisine et un instructeur professionnel."},
            {"role": "user", "content": prompt},
        ]
    )

    response = chat_completion.choices[0].message.content
    """path = cours.file.url
    save_path='_'.join(path.split("/")[-1].split(".")[:-1]) 
    # Save the vector store
    dir = os.path.join(settings.MEDIA_URL, f"{save_path}")
    relevants_docs = relevant_doc(question, dir)
    response = f"{response} \n\n Références du cours qui en parlent: {relevants_docs}"
    """
    return response




# Mémoire de session pour stocker l'historique des conversations
chat_memory = []



"""messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm_api.invoke(messages)
print(ai_msg["content"])
"""
def boat(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('message', '')
        print('La question: ', question)
        
        #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


        

        folder_path = os.path.join(settings.MEDIA_ROOT, "chat_boat_azure")
        vectordb =FAISS.load_local(folder_path, embeddings , allow_dangerous_deserialization=True )
        memory = ConversationBufferMemory(
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
        

        return JsonResponse({'response': result["answer"],})

# Fonction utilitaire pour formater l'historique des conversations
def format_conversation(memory):
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in memory])

def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html")


def error_403(request, exception):
    return render(request, "error/error_403.html")


def error_400(request, exception):
    return render(request, "error/error_400.html")

#RAG


def process_message_with_rag(cours):
    """
    Process a user's message using RAG to return the AI's response and the relevant document paragraph.

    Args:
        message (str): The user's question.
        pdf_path (str): The path to the PDF document to use as context.

    Returns:
        dict: A dictionary containing the AI's response and the relevant paragraph.
    """
    # Step 1: Load and split the PDF
    path = cours.file.url
    
    loader = PyPDFLoader(path)
    pages = loader.load()
    print(f'This document have {len(pages)} pages')
    print(pages[0].page_content)
    print(pages[0].metadata)
    
    r_splitter = RecursiveCharacterTextSplitter(chunk_size= 500, chunk_overlap= 5)
    docs = r_splitter.split_documents(pages)
    print(len(docs))
    
    #embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(docs, huggingface_embeddings)
    save_path='_'.join(path.split("/")[-1].split(".")[:-1]) 
    # Save the vector store
    dir = os.path.join(settings.MEDIA_URL, f"{save_path}")
    if not os.path.exists(dir):
        os.mkdir(dir)
    print("Dir: ", dir)
    vectordb.save_local(dir)
    return dir

    
def relevant_doc(query, save_path):
    if Cours.Object.get().vector_db_file:
        vector_db_path = quiz.vector_db_file.url
        
    # Load the vector store
    vectordb = FAISS.load_local(
          vector_db_path, huggingface_embeddings, allow_dangerous_deserialization=True
      )
    
    #relevant information
    
    relevant_docs = vectordb.similarity_search(query=query, k=3)
    
    return  relevant_docs




def emailsender(Subject, html, email_address,  user_email, contact = None):
    message = MIMEMultipart("alternative")
    # on ajoute un sujet
    message["Subject"] = Subject
    # un émetteur
    message["From"] = f"Chefquiz <{email_address}>"
    # un destinataire
    message["To"] = user_email
    # on crée deux éléments MIMEText 
    html_mime = MIMEText(html, 'html')
    if contact:
        user_email = [user_email, "sitsopekokou@gmail.com"]
    # on attache ces deux éléments 
    message.attach(html_mime)

    # on crée la connexion
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
        # connexion au compte
        server.login(email_address, email_password)
        # envoi du mail
        server.sendmail(email_address, user_email, message.as_string())

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import os

# def save_db(doc_path, folder_path, embeddings):
#     azure_container_name= "media"
#     azure_connection_string= settings.AZURE_CONNECTION_STRING
#     # Connexion au service Azure Blob Storage
#     blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=chefquizstockage;AccountKey=N6V8qPO4CgJoS4ZBQZ7Cd3wl1vNXJBoviAGuQku1PpibTJ6xQaD+aa5L/LkhYDJum6cVDz8u7Kuk+AStiBOxSQ==;EndpointSuffix=core.windows.net")
#     container_client = blob_service_client.get_container_client(azure_container_name)
#     loader = PyPDFLoader(doc_path)
#     pages = loader.load()
#     print(f'This document have {len(pages)} pages')
#     print(pages[0].metadata)

#     r_splitter = RecursiveCharacterTextSplitter(chunk_size= 500, chunk_overlap= 10)
#     docs = r_splitter.split_documents(pages)
#     print(len(docs))

#     vectordb = FAISS.from_documents(docs, embeddings)
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)
#     # Sauvegarder l'index FAISS
#     vectordb.save_local(folder_path)
#     return 



def save_db(doc_path, folder_path, embeddings, course_id):

    azure_container_name= "media"
    azure_connection_string= settings.AZURE_CONNECTION_STRING
    #
    # Charger le document PDF
    loader = PyPDFLoader(doc_path)
    pages = loader.load()
    print(f"This document has {len(pages)} pages")
    print(pages[0].metadata)

    # Diviser le document en chunks
    r_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    docs = r_splitter.split_documents(pages)
    print(len(docs))

    # Créer l'index FAISS
    vectordb = FAISS.from_documents(docs, embeddings)

    # Créer un dossier local pour enregistrer les fichiers FAISS et .pkl
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Définir les chemins de sauvegarde pour FAISS et .pkl
    faiss_file_path = os.path.join(folder_path, "index.faiss")
    pkl_file_path = os.path.join(folder_path, "index.pkl")

    # Sauvegarder FAISS et .pkl localement
    vectordb.save_local(folder_path)

    # Upload des fichiers vers Azure Blob Storage
    upload_to_azure(azure_connection_string, azure_container_name, faiss_file_path, course_id)
    upload_to_azure(azure_connection_string, azure_container_name, pkl_file_path, course_id)

    # Supprimer les fichiers locaux après l'upload
    if os.path.exists(faiss_file_path):
        os.remove(faiss_file_path)
        print(f"Fichier local {faiss_file_path} supprimé.")

    if os.path.exists(pkl_file_path):
        os.remove(pkl_file_path)
        print(f"Fichier local {pkl_file_path} supprimé.")

from azure.storage.blob import BlobServiceClient
import os

def upload_to_azure(azure_connection_string, container_name, file_path, course_id):
    """
    Fonction qui upload un fichier vers Azure Blob Storage dans un dossier spécifique basé sur course_id.
    """
    # Vérifier si le fichier existe localement
    if not os.path.exists(file_path):
        print(f"Fichier {file_path} introuvable.")
        return

    # Connexion au service Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=chefquizstockage;AccountKey=N6V8qPO4CgJoS4ZBQZ7Cd3wl1vNXJBoviAGuQku1PpibTJ6xQaD+aa5L/LkhYDJum6cVDz8u7Kuk+AStiBOxSQ==;EndpointSuffix=core.windows.net")
    container_client = blob_service_client.get_container_client("media")
    
    # Extraire le nom du fichier et créer le chemin du fichier dans le dossier basé sur course_id
    blob_name = os.path.basename(file_path)
    blob_path = f"{course_id}/{blob_name}"  # Créer le chemin dans le "dossier" course_id
    
    # Créer un client blob avec le chemin complet
    blob_client = container_client.get_blob_client(blob_path)

    # Upload du fichier
    with open(file_path, "rb") as file:
        blob_client.upload_blob(file, overwrite=True)
        print(f"Fichier {file_path} téléchargé sur Azure Blob Storage sous le nom {blob_path}.")


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

def load_db_qa1(path, embeddings,  question):
    
    #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    folder_path = os.path.join(settings.MEDIA_URL, path)
    vectordb =FAISS.load_local(folder_path, embeddings , allow_dangerous_deserialization=True )
    memory = ConversationBufferMemory(
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
   
    
    result = qa.invoke({"question": question})
    
    return result



import os
import shutil

def load_db_qa(path, embeddings, question):
    folder_path = os.path.join(settings.MEDIA_ROOT, path)

    # URL du fichier FAISS dans Azure Blob Storage
    faiss_url = f"https://chefquizstockage.blob.core.windows.net/media/{path}/index.faiss"
    pickle_url = f"https://chefquizstockage.blob.core.windows.net/media/{path}/index.pkl"

    # Chemins temporaires locaux pour les fichiers téléchargés
    temp_file_path_faiss = os.path.join(folder_path, "index.faiss")
    temp_file_path_pickle = os.path.join(folder_path, "index.pkl")

    # Si les fichiers n'existent pas localement, les télécharger
    if not os.path.exists(temp_file_path_faiss) or not os.path.exists(temp_file_path_pickle):
        print("Téléchargement des fichiers depuis Azure Blob Storage...")
        download_file_from_url(faiss_url, temp_file_path_faiss)
        download_file_from_url(pickle_url, temp_file_path_pickle)

    # Charger l'index FAISS localement
    vectordb = FAISS.load_local(folder_path, embeddings, allow_dangerous_deserialization=True)

    # Création du mécanisme de mémoire pour la conversation
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True
    )

    # Définir le prompt personnalisé
    custom_prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template="""Tu es un assistant intelligent qui répond aux questions en fonction du contexte donné.
        
        Contexte : {context}
        Historique du chat : {chat_history}
        Question : {question}
        
        Réponds de manière claire et précise.
        """
    )

    # Chaîne de récupération conversationnelle avec le prompt personnalisé
    qa = ConversationalRetrievalChain.from_llm(
        llm_azure,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
        return_generated_question=True,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt},  # Ajout du prompt ici
    )

    # Répondre à la question posée
    result = qa.invoke({"question": question})
    return result


def save_db_azure(doc_path, folder_path):
    
    
    
    loader = PyPDFLoader(doc_path)
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
    vectordb.save_local(folder_path)
    return 



RESPONSE_JSON = {
    "1": {
        "no": "1",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
    "2": {
        "no": "2",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
    "3": {
        "no": "3",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
}


# def relevant_docs(path):
    
#     llm_azure = AzureChatOpenAI(
#                 #openai_api_base="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
#                 openai_api_version="2024-07-01-preview",
#                 deployment_name="gpt-35-turbo-chefquiz",
#                 openai_api_key=settings.AZURE_EMBEDDING_API_KEY,
#                 openai_api_type='azure',
#                 azure_endpoint= "https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
#             )
#     folder_path = os.path.join(settings.MEDIA_URL ,path)
#     print("Folder: ", folder_path)
#     vectordb =FAISS.load_local(folder_path, embeddings , allow_dangerous_deserialization=True )

#     # Run chain
#     qa_chain = RetrievalQA.from_chain_type(
#         llm_azure,
#         retriever=vectordb.as_retriever(),
#         return_source_documents=True,
#         #chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
#     )
    
#     result = qa_chain.invoke({"query": "Donne moi les parties les plus pertinentes de ce documents un peu difficiles à comprendre",
#                               "search_kwargs": {"k": 8}})
    
#     documents = " ".join([docs.page_content for docs in result['source_documents']])
#     print(result)
#     return documents




def chat_with_openai(number, difficulty, path):
    AZURE_CHAT_ENDPOINT="https://realtimekokou.openai.azure.com/openai/deployments/gpt-4-0613/chat/completions?api-version=2024-10-21"
    AZURE_CHAT_API_KEY="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j"
    client = AzureOpenAI(
                api_key=AZURE_CHAT_API_KEY,
                api_version="2024-10-21",
                azure_endpoint=AZURE_CHAT_ENDPOINT
            )
    print('path: ', path, "=="*4)
    context= relevant_docs(path)
    print("Context: ", context)
    
    """Communicate with Azure OpenAI to generate questions and answers."""
    
    prompt = f"""
    Génère un quiz de {number} questions basé sur ce texte :
    
    {context}
    
    Niveau de difficulté : {difficulty}.
    Le quiz doit etre en français.
    Le format de sortie doit être :
    {json.dumps(RESPONSE_JSON)}
    Assurez vous que les options soient des phrases complètes, pas que des mots.
    """
    print("Seconde step: ", "=="*5)
    #print("intialisation: ", response)

    chat_completion = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are an expert MCQ maker."},
                {"role": "user", "content": prompt},
            ]
        )
    print("intialisation: ")
    response = chat_completion.choices[0].message.content
    print("Response: ", response)
    return response





import os
from azure.storage.blob import BlobServiceClient
import tempfile
from azure.storage.blob import BlobServiceClient

from azure.storage.blob import BlobServiceClient

import requests

def download_file_from_url(url, local_path):
    #try:
    # Télécharger le fichier depuis l'URL
    response = requests.get(url)
    response.raise_for_status()  # Vérifie si la requête a échoué

    # Sauvegarder le contenu dans un fichier local
    with open(local_path, 'wb') as file:
        file.write(response.content)
    print(f"Fichier téléchargé depuis {url} vers {local_path}")
    # except requests.exceptions.RequestException as e:
    #     print(f"Erreur lors du téléchargement du fichier : {str(e)}")


def relevant_docs(path):
    print("__"*10)
    llm_azure = AzureChatOpenAI(
        openai_api_version="2024-07-01-preview",
        deployment_name="gpt-35-turbo-chefquiz",
        openai_api_key=settings.AZURE_EMBEDDING_API_KEY,
        openai_api_type='azure',
        azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
    )

    # URL du fichier FAISS dans Azure Blob Storage
    faiss_url = f"https://chefquizstockage.blob.core.windows.net/media/{path}/index.faiss"
    pickle_url = f"https://chefquizstockage.blob.core.windows.net/media/{path}/index.pkl"

    # Créer un chemin temporaire local pour les fichiers téléchargés
    folder_path = os.path.join(settings.MEDIA_ROOT, path)
    temp_file_path_faiss = os.path.join(folder_path, "index.faiss")
    temp_file_path_pickle = os.path.join(folder_path, "index.pkl")

    print(folder_path, )
    # Télécharger les fichiers depuis Azure Blob Storage
    download_file_from_url(faiss_url, temp_file_path_faiss)
    download_file_from_url(pickle_url, temp_file_path_pickle)
    print("=="*10, "downlad")
    # Charger l'index FAISS localement depuis le fichier téléchargé
    vectordb = FAISS.load_local(folder_path, embeddings, allow_dangerous_deserialization=True)
    
    # Supprimer les fichiers locaux temporaires après utilisation
    if os.path.exists(temp_file_path_faiss):
        os.remove(temp_file_path_faiss)
        print(f"Fichier local temporaire {temp_file_path_faiss} supprimé.")

    if os.path.exists(temp_file_path_pickle):
        os.remove(temp_file_path_pickle)
        print(f"Fichier local temporaire {temp_file_path_pickle} supprimé.")

    # Exécuter la chaîne de questions-réponses
    qa_chain = RetrievalQA.from_chain_type(
        llm_azure,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
    )
    print("="*4, qa_chain, "="*4)
    result = qa_chain.invoke({
        "query": "Donne moi les parties les plus pertinentes de ce document un peu difficiles à comprendre",
        "search_kwargs": {"k": 8}
    })

    documents = " ".join([docs.page_content for docs in result['source_documents']])
    print(result)
    return documents



"""doc_path = os.path.join(settings.BASE_DIR, "lessons", "formation_cuisine_rag.pdf")
folder_path = os.path.join(settings.MEDIA_URL, "chat_boat_azure_deploy")
save_db_azure(doc_path, folder_path)"""