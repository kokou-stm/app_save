from rest_framework import serializers
from lessons.models import *

class Courseserializer(serializers.ModelSerializer):
    
    class Meta:
        model = Cours
        fields = '__all__'