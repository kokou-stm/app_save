from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(QuestionAnswers)
admin.site.register(Quiz)
admin.site.register(Professeur)
admin.site.register(Etudiant)
admin.site.register(Cours)
