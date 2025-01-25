from django.db import models

# Create your models here.


'''
class Student(models.Model):
    username = models.CharField(max_length=255)
    student_id = models.IntegerField()
    email = models.EmailField()

class User_courses(models.Model):
    id_user = models.ForeignKey()
    id_courses = models.ForeignKey()


'''


import os
import unicodedata
from django.utils.text import slugify
from django.contrib.auth.models import User, AbstractBaseUser
# Create your views here.
import uuid



def clean_filename(instance, filename):
    """
    Nettoie le nom du fichier pour éviter les caractères problématiques.
    - Remplace les accents par leurs équivalents non accentués.
    - Transforme en slug.
    """
    name, ext = os.path.splitext(filename)  # Séparer le nom et l'extension
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')  # Supprimer accents
    name = slugify(name)  # Convertir en slug (remplace espaces et caractères spéciaux par des tirets)
    return f"uploads/{name}{ext}"  # Ajouter le chemin et l'extension


# Create your models here.
class VerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(max_length=6, unique=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_code(self):
        self.code = str(uuid.uuid4().int)[:6]
        self.save()


class Etudiant(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_de_carte = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Numéro de carte étudiant
    phone = models.CharField(max_length=15, blank=True, null=True)  # Téléphone
    nom = models.CharField(max_length=100, null = False, blank= False)
    email = models.EmailField(max_length=100, null = False, blank= False)
    scores = models.JSONField(blank=True, null=True) 
   
    def calculate_progress(self):
        """
        Calcule le pourcentage de progression basé sur les scores des quizzes.
        """
        total_score = sum(score['score'] for score in self.scores)
        max_score = sum(score['max_score'] for score in self.scores)
        return (total_score / max_score) * 100 if max_score > 0 else 0
    def __str__(self):
        return f"{self.username.username}"


class Professeur(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_de_carte = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Numéro de carte étudiant
    phone = models.CharField(max_length=15, blank=True, null=True)  # Téléphone
    nom = models.CharField(max_length=100, null = False, blank= False)
    email = models.EmailField(max_length=100, null = False, blank= False)
   

    def __str__(self):
        return f"{self.username.username}"

import os

def upload_to_quiz_directory(instance, filename):
    """
    Génère un chemin dynamique pour sauvegarder les fichiers en fonction du titre du quiz.
    """
    # Remplace les espaces par des underscores et utilise le titre du quiz comme dossier
    folder_name = instance.title.replace(' ', '_')
    return os.path.join('vector_dbs', folder_name, filename)


class Cours(models.Model):
    title = models.CharField(max_length=255)
    description  = models.CharField(max_length=255)
    file = models.FileField(upload_to=clean_filename)
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE)
    etudiant = models.ManyToManyField(Etudiant)
    #vector_db_file = models.FileField(upload_to=upload_to_quiz_directory, blank=True, null=True)
    
    
    def __str__(self):
        return self.title
    

class Quiz(models.Model):
    quiz_title = models.CharField(max_length=255)
    quiz_description = models.CharField(max_length=255)
    course = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="quizzes")
    total_score = models.IntegerField(null=True, blank=True )
    max_score = models.IntegerField(null=True, blank=True )
    
   

    def __str__(self):
        return self.quiz_title


class QuestionAnswers(models.Model):
    # Correction : Ajoutez la clé étrangère pour lier la question au quiz
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    numero = models.IntegerField(default=True, blank=True)
    question_text = models.CharField(max_length=1000)
    options = models.JSONField(null=True, blank=True)
    required_time = models.FloatField(default=60)  # Temps requis en secondes
    user_answer = models.CharField(max_length=500, null=True, blank=True)  # Autorisez le champ vide
    great_answer = models.CharField(max_length=500)  # Réponse détaillée ou explication
    score = models.FloatField(null=True, blank=True)  # Score associé à la question
    def __str__(self):
        return self.quiz.quiz_title
