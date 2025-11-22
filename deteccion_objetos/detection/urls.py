from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('upload/', views.upload_image, name='upload_image'),
    path('detect/', views.detect_objects, name='detect_objects'),
]
