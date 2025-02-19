from django.urls import path
from .views import *

urlpatterns = [
    path('connexion/', connexion, name='connexion'),
    path('register/', register, name='register'),

]

