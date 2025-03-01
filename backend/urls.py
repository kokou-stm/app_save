from django.urls import path
from .views import *

urlpatterns = [
    path('connexion/', connexion, name='connexion'),
    path('register/', register, name='register'),
    path('cours/', cours, name='cours'),
    path('quiz/', quiz, name='quiz'),
    path('quiz_questions/', quiz_questions, name='quiz_questions'),
    
]

