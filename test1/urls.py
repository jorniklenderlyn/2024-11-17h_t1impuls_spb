from django.urls import path, include
from . import views


urlpatterns = [
    # path('project/', views.getAllProjects),
    path('', views.getProject),
    path('api/sprint-bar/<int:day>/<sprint>/', views.get_sprint_bar_data),
    path('api/sprint-change/', views.update_sprint),
    path('api/burn/', views.get_burn),
    # path('', views.index, name='index'),
    # path('t/', views.test, name='test'),
]
