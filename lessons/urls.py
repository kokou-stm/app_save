from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('upload_cours/', views.upload_cours, name='upload_cours'),
    path('quiz_creator/<int:course_id>/', views.quiz, name='quiz_creator'),
    path('quiz/', views.quiz, name='quiz'),
    path('profile/', views.profile, name='profile'),
    path('code/', views.code, name='code'),
    path('cours/', views.listecours, name='lescours'),
    path('faquestion/', views.faquestion, name='faquestion'),
    path('ask_ai/<int:course_id>', views.ask_ia, name='ask_ai'),
    path('login/', views.connection, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.deconnexion, name='logout'),
    path('forgotpassword/', views.forgotpassword, name='forgotpassword'),
    path('updatepassword/<str:token>/<str:uid>/', views.updatepassword, name='updatepassword'),  
    path('course/<int:course_id>/', views.course_details, name='course_details'),
    path('quiz_details/<int:quiz_id>/', views.quiz_details, name='quiz_details'),
    path('quiz_details/<int:quiz_id>/', views.quiz_details, name='display_quiz'),
    path('quiz_score/<int:quiz_id>/', views.quiz_score, name='quiz_score'),
    path('update_quiz/<int:quiz_id>/', views.update_quiz, name='update_quiz'),
    
    path('contact/', views.contact, name='contact'),
    path('boat/', views.boat, name='boat'),
    path('graph/', views.dash, name='dash'),
    path('popupquiz/<str:add_val>/', views.popupquiz, name='popupquiz'),
    path('search/', views.search_courses, name='search_courses'),
      
] 
urlpatterns+= [re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),]
