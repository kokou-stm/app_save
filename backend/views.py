from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
from django.conf import settings
from lessons.models import *
from .serializers import *

email_address = settings.EMAIL_HOST_USER
email_password = settings.EMAIL_HOST_PASSWORD

smtp_address = settings.EMAIL_HOST
smtp_port = 465


@api_view(['POST'])
def connexion(request):
    # Récupère les informations d'identification
    #username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    user_find = User.objects.filter(email= email).first()
    if user_find:
    # Authentifie l'utilisateur
        user = authenticate(username=user_find, password=password)
        if not user:
            return Response({"detail": "Identifiant ou mot de passe incorrecte."}, status=status.HTTP_400_BAD_REQUEST)
            #raise AuthenticationFailed("Identifiants invalides")

        # Crée un token
        refresh = RefreshToken.for_user(user)

        # Retourne les tokens
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })





from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rest_framework.decorators import api_view
from rest_framework.response import Response

'''@api_view(["POST"])
def deconnexion(request):
    if request.method=='POST':
        if request.user.is_authenticated:
            refresh_token = request.data.get("refresh")
            print(request.data)
            if not refresh_token:
                return Response({"detail": "Token non fourni"}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklister le token
            token = RefreshToken(refresh_token)
            token.blacklist()  # Ajoute le token à la liste noire
            print("Deconnexion reussie")
            print('deonnexion reussie')
            return Response(status=status.HTTP_200_OK)
        

    return Response({"error": "Utilisateur non authentifié"}, status=401)
'''
@api_view(['POST'])
def deconnexion(request):
    try:
       if request.method=='POST':
            print(request.headers)
            # Récupérer le token d'actualisation (refresh token)
            refresh_token = request.data.get("refresh")
            #print(request.data)
            if not refresh_token:
                return Response({"detail": "Token non fourni"}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklister le token
            token = RefreshToken(refresh_token)
            token.blacklist()  # Ajoute le token à la liste noire
            print("Deconnexion reussie")
            return Response({"message": "Déconnexion réussie"})
 
    except Exception as e:
        return Response({"detail": "Erreur lors de la déconnexion"}, status=status.HTTP_400_BAD_REQUEST)



from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    serializer = UserProfileSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_user(request):
    data = request.data
    try:
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




'''
    
'''
'''
@api_view
def deconnexion(request):
     logout(request)

     return Response({})
'''

@api_view(['POST'])
def register(request):
    # Récupère les informations d'inscription
    email = request.data.get("email")
    first_name = request.data.get("firstName")
    last_name = request.data.get("lastName")
    username = ''.join(f"{last_name}{first_name}".split())
    password = request.data.get("password")
    
    print(email, first_name, last_name, username, password)
    print(request.data)
    # Vérifie que l'email est valide
    try:
        validate_email(email)
    except ValidationError:
        print('1')
        return Response({"detail": "L'email n'est pas valide."}, status=status.HTTP_400_BAD_REQUEST)

   
    # Vérifie si l'email est déjà utilisé
    if User.objects.filter(email=email).exists():
        print(3)
        return Response({"detail": "Cet email est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie si le nom d'utilisateur est déjà pris
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Ce nom d'utilisateur est déjà pris."}, status=status.HTTP_400_BAD_REQUEST)
    print(4)
    # Crée un nouvel utilisateur
    user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
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
                            <h1>Bienvenue sur ChefQuiz, {first_name} ! 👩‍🍳👨‍🍳</h1>
                            <p>Bonjour {first_name},</p>
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
                            <p>Bonjour {first_name},</p>
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

    # Crée un token pour l'utilisateur
    refresh = RefreshToken.for_user(user)

    # Retourne une réponse avec les tokens
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
def edit_profile(request):
    # Récupère les informations d'inscription
    if request.method =='POST':
        email = request.data.get("email")
        username = request.data.get("username")
        cardNumber = request.data.get("cardNumber")
        phoneNumber = request.data.get("phoneNumber")
        print(email, username,cardNumber, phoneNumber )
        
        # Vérifie que l'email est valide
        try:
            validate_email(email)
        except ValidationError:
            print('1')
            return Response({"detail": "L'email n'est pas valide."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail":"Enregistré avec succes"})


'''@api_view(['GET'])
def cours(request):
     courses = Cours.objects.all()
     cours_serializer = Courseserializer(courses, many=True)
     return Response(cours_serializer.data)
'''

@api_view(['GET'])
def cours(request):
    courses = Cours.objects.all()
    data = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
           "professeur": {"nom": course.professeur.username.username},
            "file": course.file.url if course.file else None,
            "quizzes": [
                {"id": quiz.id, "quiz_title": quiz.quiz_title, "quiz_description": quiz.quiz_description}
                for quiz in course.quizzes.all()
            ],
        }
        for course in courses
    ]
    return Response(data)


@api_view(['GET'])
def quiz(request):
     quizes = Quiz.objects.all()
     quizes_serializer = Quizserializer(quizes, many=True)
     return Response(quizes_serializer.data)


@api_view(['POST'])
def quiz_questions(request):
    quiz_id = request.data.get('quiz_id')
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return JsonResponse({'error': 'Quiz not found'}, status=404)

    questions = QuestionAnswers.objects.filter(quiz=quiz)
    questions_serializer = QuestionAnswersSerializer(questions, many=True)
    return JsonResponse(questions_serializer.data, safe=False)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

@api_view(['POST'])
def contact(request):
    if request.method == "POST":
        #subject = request.data.get("subject")
        email = request.data.get("email")
        username = request.data.get("name")
        message = request.data.get('message')
        message = f"Nom d'utilisateur: {request.user.username}\nAdresse mail: {email}\n{request.data.get('message')}"

        try:
            #send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=False)
            return Response({"message": "Nous avons bien reçu votre message. Nous vous revenons très bientôt !!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"error": "Erreur lors de l'envoi du message. Veuillez réessayer plus tard."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"error": "Méthode non autorisée"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


from django.contrib.auth.models import User

@api_view(['POST'])
def save_quiz_score(request):

    quiz_id = request.data.get('quiz_id')
    score = request.data.get('score')
    max_score = request.data.get('max_score')
    if request.user.is_authenticated:
         print(request.user.username)

    else:
         print("=="*5, "Not auth")
    try:
        etudiant = Etudiant.objects.get(username=request.user)
    except Etudiant.DoesNotExist:
        return JsonResponse({'error': 'Etudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    if etudiant.scores is None:
        etudiant.scores = []

    # Mettre à jour ou ajouter le score pour le quiz donné
    quiz_scores = etudiant.scores
    for quiz_score in quiz_scores:
        if quiz_score['quiz_id'] == quiz_id:
            quiz_score['score'] = score
            quiz_score['max_score'] = max_score
            break
    else:
        quiz_scores.append({'quiz_id': quiz_id, 'score': score, 'max_score': max_score})

    etudiant.save()
    return JsonResponse({'message': 'Score enregistré avec succès'}, status=status.HTTP_200_OK)



@api_view(['GET'])
def get_total_score(request):
    user_id = request.user.id

    try:
        etudiant = Etudiant.objects.get(username_id=user_id)
    except Etudiant.DoesNotExist:
        return JsonResponse({'error': 'Etudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    if etudiant.scores:
        total_score = sum(score['score'] for score in etudiant.scores)
        max_score = sum(score['max_score'] for score in etudiant.scores)
        progress = (total_score / max_score) * 100 if max_score > 0 else 0
    else:
        progress = 0

    return JsonResponse({'progress': progress}, status=status.HTTP_200_OK)


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



from django.shortcuts import get_object_or_404

@api_view(['GET'])
def cours_details(request, cours_id):
    """
    Récupère les détails complets d'un cours avec ses quiz associés
    """
    try:
        # Récupérer le cours ou renvoyer une 404
        cours = get_object_or_404(Cours, id=cours_id)
        
        # Préparer les données du cours avec tous les détails
        course_data = {
            "id": cours.id,
            "title": cours.title,
            "description": cours.description,
            "professeur": {
                "id": cours.professeur.id,
                "nom": cours.professeur.nom,
                "email": cours.professeur.email  # Ajoutez d'autres détails si nécessaire
            },
            "file": cours.file.url if cours.file else None,
            "quizzes": [
                {
                    "id": quiz.id, 
                    "quiz_title": quiz.quiz_title, 
                    "quiz_description": quiz.quiz_description,
                    # Ajoutez d'autres détails du quiz si nécessaire
                }
                for quiz in cours.quizzes.all()
            ]
        }
        
        return Response(course_data, status=status.HTTP_200_OK)
    
    except Cours.DoesNotExist:
        return Response({
            "error": "Cours non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)