from django.urls import path, include
from . import views

urlpatterns = [
    path('project/', views.getAllProjects),
    path('project/<int:pk>/', views.getProject),
    path('', views.index, name='index'),
]
