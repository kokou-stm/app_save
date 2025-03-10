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
    print('User: ', user)
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

from django.db.models import Sum

from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])  # Permettre à la fois GET et POST pour plus de flexibilité
def progress(request):
    # Calcul du score maximum possible
    max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
    
    # Vérifier si max_score est None ou 0 pour éviter la division par zéro
    if not max_score:
        max_score = 1
    
    # Dictionnaire pour stocker les pourcentages de progression des étudiants
    students_progress = {}
    
    # Récupérer tous les étudiants
    list_etu = Etudiant.objects.all()
    total_progress = 0  # Pour calculer la moyenne de progression globale
    
    # Calculer la progression pour chaque étudiant
    for etud in list_etu:
        # Calculer le score total de l'étudiant
        total_score = sum(score['score'] for score in etud.scores)
        
        # Calculer le pourcentage de progression arrondi à une décimale
        progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
        
        # Ajouter au dictionnaire des progressions
        full_name = f"{etud.username.first_name} {etud.username.last_name}"
        students_progress[full_name] = progress_etud
        
        # Ajouter à la progression totale pour la moyenne
        total_progress += progress_etud
    
    # Calculer la progression moyenne (pourcentage global)
    if list_etu.count() > 0:
        average_progress = total_progress / list_etu.count()
    else:
        average_progress = 0
    
    # Trier les étudiants par progression (du plus élevé au plus bas)
    students_progress = dict(sorted(students_progress.items(), key=lambda item: item[1], reverse=True))
    
    # Logging pour le débogage
    print("Max score:", max_score)
    print("Students progress:", students_progress)
    print("Average progress:", average_progress)
    
    # Réponse avec à la fois la progression moyenne et le détail par étudiant
    return Response({
        'progress_percentage': round(average_progress, 2),
        'students_progress': students_progress
    })  



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from django.db.models import Sum
import numpy as np

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Assure que seul un utilisateur authentifié peut accéder à cette vue
def dash(request):
    try:
        progress_percentage = 0
        cours = Cours.objects.all()
        quiz = Quiz.objects.all().count()
        quiz_number = [i for i in range(1, 1 + quiz)]
        max_score = QuestionAnswers.objects.aggregate(total=Sum('score'))['total']
        max_score = max_score if max_score else 1  # Défaut à 1 pour éviter la division par zéro

        percents_etud = {}
        list_etu = Etudiant.objects.all()
        for etud in list_etu:
            total_score = sum(score['score'] for score in etud.scores)
            progress_etud = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
            percents_etud[f"{etud.username.first_name} {etud.username.last_name}"] = progress_etud

        percents_etud = dict(sorted(percents_etud.items(), key=lambda item: item[1], reverse=True))
        moyenne = [[score['score'] for score in etudiant_i.scores] for etudiant_i in list_etu]

        for i in range(len(moyenne)):
            if len(moyenne[i]) < len(quiz_number):
                moyenne[i].extend([0] * (len(quiz_number) - len(moyenne[i])))

        best_calcul = [np.mean(np.array(value)) for value in moyenne]
        context = {
            'is_staff': request.user.is_staff,
            'list_etud': [f"{etu.username.first_name} {etu.username.last_name}" for etu in list_etu],
            'percents_etud': percents_etud,
        }

        try:
            best_list = moyenne[best_calcul.index(max(best_calcul))]
            moyenne = np.array(moyenne)
            moyenne = list(np.mean(moyenne, axis=0, dtype=np.int32))
            context['best_list'] = best_list
            context['moyenne'] = [float(m) for m in moyenne]
        except Exception as e:
            print("Erreur lors du calcul des moyennes :", e)

        if not request.user.is_staff:
            etudiant = Etudiant.objects.get(username=request.user)
            scores = [score['score'] for score in etudiant.scores]
            total_score = sum(score['score'] for score in etudiant.scores)
            progress_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            context['progress_percentage'] = round(progress_percentage, 2)
            context['scores'] = scores

        context['quiz_number'] = quiz_number
        context['nbre_quiz'] = len(quiz_number)

        return Response(context)

    except Exception as error:
        print("Erreur :", error)
        raise AuthenticationFailed("Problème avec l'authentification ou traitement des données.")

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


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

#@permission_classes([IsAuthenticated])  # Nécessite une authentification
@csrf_exempt
@api_view(['POST'])
def edit_profile(request):
    """
    Vue pour mettre à jour les informations de l'utilisateur connecté.
    """
    try:
        # Récupérer l'utilisateur actuel
        user = request.user
        
        # Extraire les données du corps de la requête
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        card_number = request.data.get('cardNumber', '').strip()
        phone_number = request.data.get('phoneNumber', '').strip()
        print(len(card_number), card_number)
        # Vérifications de base
        if not username:
            return Response({'detail': "Le nom d'utilisateur est requis."}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'detail': "L'email est requis."}, status=status.HTTP_400_BAD_REQUEST)
        '''if len(card_number) != 19 or not card_number.isdigit():
            return Response({'detail': "Le numéro de carte doit contenir 16 chiffres."}, status=status.HTTP_400_BAD_REQUEST)
        if len(phone_number) < 8 or not phone_number.isdigit():
            return Response({'detail': "Le numéro de téléphone est invalide."}, status=status.HTTP_400_BAD_REQUEST)'''

        # Mettre à jour les champs utilisateur
        user.username = username
        user.email = email
        user.save()

        # Mettre à jour les champs additionnels (ex. cardNumber, phoneNumber)
        # Si ces champs sont stockés dans un modèle séparé comme un profil
        etudiant = Etudiant.objects.get(username = user)
        etudiant.numero_de_carte = card_number
        etudiant.phone = phone_number
        etudiant.save()
 
        return Response({'detail': "Profil mis à jour avec succès !"}, status=status.HTTP_200_OK)

    except Exception as e:
        print("Erreur lors de la mise à jour du profil :", e)
        return Response({'detail': "Une erreur est survenue lors de la mise à jour du profil."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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