from django.urls import path
from .views import *
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     path('contact/', contact, name='contact'),
    path('connexion/', connexion, name='connexion'),
    path('register/', register, name='register'),
    path('cours/', cours, name='cours'),
    path('quiz/', quiz, name='quiz'),
    path('quiz_questions/', quiz_questions, name='quiz_questions'),
    path('save_quiz_score/', save_quiz_score, name='save_quiz_score'),
    path('get_total_score/', get_total_score, name='get_total_score'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('logout/', deconnexion, name='logout'),
    path('cours_detail/<int:cours_id>/', cours_details, name='cours-details'),
]

