from django.shortcuts import render, redirect
from .forms import CourseForm
from django.http import JsonResponse
from .models import *
from .api import *
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib import messages
import datetime
from datetime import timedelta
import PyPDF2
import openai
from django.db.models import Q
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.urls import reverse

from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ValidationError
import codecs,math
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum
from langchain_openai import AzureChatOpenAI
from langchain_openai import  AzureOpenAIEmbeddings

@login_required
def index(request):
    
    progress_percentage=0
    cours = Cours.objects.all()
    
    percents_etud = {}
    list_etu = Etudiant.objects.all()
    for etud in list_etu: 
        total_score = sum(score['score'] for score in etud.scores)
        try:
            progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
            
        except:
            progress_etud = 0
        percents_etud[f"{etud.username.first_name} {etud.username.last_name}"]= progress_etud
    
    if request.user.is_staff:
        prof = Professeur.objects.get(username = request.user)
        cours = Cours.objects.filter(professeur=prof)
        context = {'is_staff': request.user.is_staff, 'cours': cours,  'cours': cours,
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
#print("Base :" ,os.path.join(settings.BASE_DIR, "/media/uploads/cuisine-proffessionnelle-avancee-1.pdf"))



def dash(request):

    progress_percentage=0
    cours = Cours.objects.all()
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
    percents_etud = {}
    list_etu = Etudiant.objects.all()
    for etud in list_etu: 
        total_score = sum(score['score'] for score in etud.scores)
        progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
        percents_etud[f"{etud.username.first_name} {etud.username.last_name}"]= progress_etud
    
    
    context = {'progress_percentage': round(progress_percentage, 2),
                'is_staff': request.user.is_staff,
                'list_etud': list_etu,
                'percents_etud': percents_etud,
                'scores': scores}
    
    return render(request, "dash.html", context)

#print("Base :" ,os.path.join(settings.BASE_DIR, "/media/uploads/cuisine-proffessionnelle-avancee-1.pdf"))


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

from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings

from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import openai
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key ="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"
os.environ["OPENAI_API_KEY"] ="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"
os.environ['HUGGINGFACEHUB_API_TOKEN'] ="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"# Charger les documents

#embeddings = OpenAIEmbeddings()
embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                    azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15",
                                    api_key="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j",
                                    openai_api_version="2023-05-15")

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
        cours_path = course.file.path
        save_db(cours_path, folder_path, embeddings)
        #process_message_with_rag(cours)
        messages.info(request, f"Cours {title} a été bien ajouté.")
        
        courses = Cours.objects.all()
        return redirect('quiz')

    return render(request, 'upload_cours.html')

def quiz1(request, course_id=None):
    courses = Cours.objects.all() 
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title')
        quiz_description = request.POST.get('quiz_description')
        course_id = request.POST.get('course_id')
        number = request.POST.get('number')
        tone = request.POST.get('tone')
        course = Cours.objects.get(id=course_id)
        quiz, created = Quiz.objects.get_or_create(
            quiz_title=quiz_title,
            quiz_description=quiz_description,
            course=course
        )

       
        cours = Cours.objects.get(id = course.id)
        path = cours.file.path
        print("lien: ", path)
        #return render(request, "quiz.html", {'courses': courses})
        text = parse_file(path)
        grade=10
        data = chat_with_openai(text[:1000], number, grade, tone, response_json)
        data = json.loads(data)
        quiz_data = []
        i = 1
        for key, value in data.items():
            #print(f"Question {value['no']}: {value['mcq']}")
            #print("Options:")
            """for option_key, option_value in value['options'].items():
                print(f"  {option_key}: {option_value}")
            print(f"Correct Answer: {value['correct']}")"""
            #print("-" * 50)
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


from django.http import JsonResponse

def quiz(request, course_id=None):
    courses = Cours.objects.all()
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title')
        quiz_description = request.POST.get('quiz_description')
        course_id = request.POST.get('course_id')
        number = request.POST.get('number')
        tone = request.POST.get('tone')
        course = Cours.objects.get(id=course_id)
       
        quiz, created = Quiz.objects.get_or_create(
            quiz_title=quiz_title,
            quiz_description=quiz_description,
            course=course, 
            
        )

        # Générer le quiz (logique existante)
        cours = Cours.objects.get(id=course.id)
        path = cours.file.path
        text = parse_file(path)
        grade = 5
        data = chat_with_openai(text[:1000], number, grade, tone, response_json)
        data = json.loads(data)

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
        for etudiant in etudiants:
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

def listecours(request):
    cours = Cours.objects.all()
    return render(request, 'lescours.html', {'cours': cours, 'is_staff': request.user.is_staff,})

def course_details(request, course_id):
    # Récupération du cours
    course = get_object_or_404(Cours, id=course_id)
    
    # Récupération du quiz associé
    quizzes = Quiz.objects.filter(course=course)
   
    context = {
        'course': course,
        'quizzes': quizzes,
        'is_staff': request.user.is_staff,
    }
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
        quiz.total_score = total_score
        quiz.max_score=max_score
        quiz.save()
        etudiant.scores.append({
            'quiz_id': quiz.id,
            'score': total_score,
            'max_score': max_score,
        })
        etudiant.save()
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

        # Rediriger vers une page de résultat ou afficher un message de succès
        return render(request, 'quiz_result.html', {
            'quiz': quiz,
            'total_score': total_score,
            'max_score': max_score,
            'questions': questions,
            'is_staff': request.user.is_staff,
                            })

    return render(request, 'quiz_display.html', {'quiz': quiz, 'questions': questions})

def register(request):
    mess = ""
    if request.method == "POST":
        
        print("="*5, "NEW REGISTRATION", "="*5)
        
        prenom= request.POST.get("firstname", None)
        nom= request.POST.get("lastname", None)
        username = f"{nom} {prenom}"
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

                    emailsender(subject, email_message, user.email)

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

                    emailsender(subject, email_message, user.email)


                    #Membre.objects.create(user=user, email=email, nom= username ).save()
                    return redirect("code")
            except Exception as e:
                    print("error: ", e)
                    #err = " ".join(e)
                    messages.error(request, e)
                    return render(request, template_name="register.html")
            
        #messages.info(request, "Bonjour")

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


def forgotpassword(request):
     if request.method =="POST":
          username = request.user.username
          email = request.POST.get("email")
          user = User.objects.filter(email= email).first()
          print("user", user )
          if user:
               print("User exist")
               token = default_token_generator.make_token(user)
               uid = urlsafe_base64_encode(force_bytes(user.id))
               current_host = request.META["HTTP_HOST"]
               
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
               emailsender(Subject, code_message, user.email)

              
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
        
        print("="*5, "NEW CONECTION", "="*5)
        email = request.POST.get("email")
        code_v = request.POST.get("code")
        user = User.objects.filter(email= email).first()
        verification_code, created = VerificationCode.objects.get_or_create(user=user)
        
        print(verification_code.code)
        if str(code_v) == str(verification_code.code) :
            messages.info(request, "Votre compte est activé . Connectez vous!")
            return redirect("login")
        else:
            mess = "Invalid code !!!"
      
        messages.info(request, mess)

    return render(request, template_name="code.html")



def deconnexion(request):
         print("Deconnexion")
         logout(request)
         return redirect("index")
    
@login_required
def contact(request):
    context={}
    if request.method =="POST":
        
            Subject = request.POST.get("subject")

            Gmail = request.POST.get("email")
            message = f"Nom d'utilisateur: {request.user.username} " f'Adresse mail: {Gmail}\n' + request.POST.get("message")
            print(message)
            
            print(Gmail,  [settings.EMAIL_HOST_USER])
            emailsender(Subject, message, Gmail)

            messages.success(request, "Your message is succesfull send  !!!")
           

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


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Professeur, Etudiant

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




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def ask_ia(request, course_id=None):
    
    if request.method == 'POST':
        print("Ok")
        data = json.loads(request.body)
        user_message = data.get('message', '')
        # Remplacez ceci par l'appel réel à votre modèle RAG
        cours = Cours.objects.get(id = course_id)
        path = cours.file.path
        #relevant_document =  parse_file(path)[:500]# from chat import process_message_with_rag relevant_document= process_message_with_rag(user_message, path)
        #ia_response= chat(document_text=relevant_document, question= user_message, cours=cours)
        ia_response = load_db_qa(f"{course_id}", embeddings,  user_message)
        #ia_response = f"Voici une réponse générée pour : {user_message}, {text}"
        source_documents = []
        for doc in ia_response.get("source_documents", []):
            # Extraire les informations pertinentes de chaque document
            doc_info = {
                "source": doc.metadata.get('source', 'Non spécifié'),
                "page_content": doc.page_content[:500]  # Limiter à 500 caractères pour éviter trop de texte
            }
            source_documents.append(doc_info)
        
        # Renvoyer la réponse dans un format JSON sérialisable
        return JsonResponse({
            'response': ia_response["answer"],
            'source_documents': source_documents
        })
       
    return render(request, "chat.html", {"course_id":course_id})








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

def chat_with_openai(text, number, grade, tone, response_json):
 
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
def chat(document_text, question,cours):
    open_client = AzureOpenAI(
        api_key='6xv3rz6Asc5Qq86B8vqjhKQzSTUZPmCcSuDm5CLEV5dj9m8gTHlNJQQJ99AKACYeBjFXJ3w3AAABACOGyHXT',
        api_version="2023-12-01-preview",
        azure_endpoint="https://chatlearning.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    )
    prompt = (
        f"Vous êtes un expert en cuisine et un formateur aidant un étudiant à se préparer pour son examen de cuisine. "
        f"L'étudiant étudie le contenu suivant tiré de son document :\n\n"
        f"{document_text}\n\n"
        f"L'étudiant pose la question suivante : {question}\n\n"
        f"Fournissez une réponse résumée, pratique et facile à comprendre, comme si vous étiez un instructeur en cuisine. "
        f"Répondez en français."
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
    """path = cours.file.path
    save_path='_'.join(path.split("/")[-1].split(".")[:-1]) 
    # Save the vector store
    dir = os.path.join(settings.MEDIA_ROOT, f"{save_path}")
    relevants_docs = relevant_doc(question, dir)
    response = f"{response} \n\n Références du cours qui en parlent: {relevants_docs}"
    """
    return response



from django.http import JsonResponse
import json

# Mémoire de session pour stocker l'historique des conversations
chat_memory = []
from langchain_community.chat_models import AzureChatOpenAI
from langchain_openai import  AzureOpenAIEmbeddings
import numpy as np
#import pandas as pd
from dotenv import load_dotenv, set_key
# callbacks
from langchain_community.callbacks import get_openai_callback
# messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# output parsers
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
os.environ["AZURE_OPENAI_ENDPOINT"]="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
os.environ["AZURE_OPENAI_API_KEY"]="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j"
os.environ["AZURE_OPENAI_API_VERSION"]="2024-07-01-preview"


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
        embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                    azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15",
                                    api_key="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j",
                                    openai_api_version="2023-05-15")
        #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


        llm_azure = AzureChatOpenAI(
                #openai_api_base="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
                openai_api_version="2024-07-01-preview",
                deployment_name="gpt-35-turbo-chefquiz",
                openai_api_key='h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j',
                openai_api_type='azure',
                azure_endpoint= "https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
            )

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
    path = cours.file.path
    
    loader = PyPDFLoader(path)
    pages = loader.load()
    print(f'This document have {len(pages)} pages')
    print(pages[0].page_content)
    print(pages[0].metadata)
    
    r_splitter = RecursiveCharacterTextSplitter(chunk_size= 300, chunk_overlap= 5)
    docs = r_splitter.split_documents(pages)
    print(len(docs))
    
    #embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(docs, huggingface_embeddings)
    save_path='_'.join(path.split("/")[-1].split(".")[:-1]) 
    # Save the vector store
    dir = os.path.join(settings.MEDIA_ROOT, f"{save_path}")
    if not os.path.exists(dir):
        os.mkdir(dir)
    print("Dir: ", dir)
    vectordb.save_local(dir)
    return dir

    
def relevant_doc(query, save_path):
    if Cours.Object.get().vector_db_file:
        vector_db_path = quiz.vector_db_file.path
        
    # Load the vector store
    vectordb = FAISS.load_local(
          vector_db_path, huggingface_embeddings, allow_dangerous_deserialization=True
      )
    
    #relevant information
    
    relevant_docs = vectordb.similarity_search(query=query, k=3)
    
    return  relevant_docs




from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl

email_address = 'voicetranslator0@gmail.com'
email_password = 'rfqzyhocddgmehbe'

smtp_address = 'smtp.gmail.com'
smtp_port = 465

def emailsender(Subject, html, user_email):
    message = MIMEMultipart("alternative")
    # on ajoute un sujet
    message["Subject"] = Subject
    # un émetteur
    message["From"] = f"Chefquiz <{email_address}>"
    # un destinataire
    message["To"] = user_email
    # on crée deux éléments MIMEText 
    html_mime = MIMEText(html, 'html')

    # on attache ces deux éléments 
    message.attach(html_mime)

    # on crée la connexion
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
        # connexion au compte
        server.login(email_address, email_password)
        # envoi du mail
        server.sendmail(email_address, user_email, message.as_string())





from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA,  ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI, ChatOpenAI

def save_db(doc_path, folder_path, embeddings):

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

def load_db_qa(path, embeddings,  question):
    embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                    azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15",
                                    api_key="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j",
                                    openai_api_version="2023-05-15")
    #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


    llm_azure = AzureChatOpenAI(
            #openai_api_base="https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
            openai_api_version="2024-07-01-preview",
            deployment_name="gpt-35-turbo-chefquiz",
            openai_api_key='h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j',
            openai_api_type='azure',
            azure_endpoint= "https://realtimekokou.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview",
        )
    #llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    folder_path = os.path.join(settings.MEDIA_ROOT, path)
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
    
    return result



def save_db_azure(doc_path, folder_path):
    
    embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large",
                                    azure_endpoint="https://realtimekokou.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15",
                                    api_key="h5R1YOBt2Q5WU56488stKWc7GiO9nEG3Z344ITLK3mTb6uGkdlKLJQQJ99BAACYeBjFXJ3w3AAABACOGLM5j",
                                    openai_api_version="2023-05-15")
    
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

'''folder_path = os.path.join(settings.MEDIA_ROOT, "videocall_boat")
print("chemin", settings.BASE_DIR)
save_db(os.path.join(settings.BASE_DIR, "lessons/rag_videocall.pdf"), folder_path, embeddings)'''