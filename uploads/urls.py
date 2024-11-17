from django.urls import path
from .views import upload_files, success

app_name = 'uploads'

urlpatterns = [
    path('', upload_files, name='upload_files'),
    path('success/', success, name='success'),
]
