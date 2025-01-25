
FROM python:3.8-slim
#ENV PYTHONBUFFERED 1

# Install pip
#RUN apt-get install -y python3-pip
# Mettre à jour et installer les dépendances nécessaires
   
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
CMD python manage.py runserver 0.0.0.0:80