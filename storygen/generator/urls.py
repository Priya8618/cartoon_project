from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('generate/', views.generate_story, name='generate_story'),
    path('result/<int:pk>/', views.result, name='result'),
]
