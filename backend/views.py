from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
from django.conf import settings
from lessons.models import *
 
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


"""{
    "email": "nouvelutilisateur@example.com",
    "first_name": "nouvelutilisateur",
    "last_name": "kokou",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123"
}"""

@api_view(['POST'])
def register(request):
    # Récupère les informations d'inscription
    email = request.data.get("email")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    username = ''.join(f"{last_name}{first_name}".split())
    password = request.data.get("password")
    password_confirm = request.data.get("password_confirm")

    # Vérifie que l'email est valide
    try:
        validate_email(email)
    except ValidationError:
        return Response({"detail": "L'email n'est pas valide."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie si les mots de passe correspondent
    if password != password_confirm:
        return Response({"detail": "Les mots de passe doivent être identiques."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie si l'email est déjà utilisé
    if User.objects.filter(email=email).exists():
        return Response({"detail": "Cet email est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie si le nom d'utilisateur est déjà pris
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Ce nom d'utilisateur est déjà pris."}, status=status.HTTP_400_BAD_REQUEST)

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

