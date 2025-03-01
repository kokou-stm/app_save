from rest_framework import serializers
from lessons.models import *


class ProfesseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professeur
        fields = '__all__'

class Courseserializer(serializers.ModelSerializer):

    professeur = ProfesseurSerializer()
    class Meta:
        model = Cours
        fields = ['id', 'title', 'description', 'file', 'professeur']



class Quizserializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'