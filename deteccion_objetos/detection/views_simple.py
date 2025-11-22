from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

def index(request):
    """Vista principal de la aplicación"""
    return render(request, 'detection/index.html', {})

def video_feed(request):
    """Vista para el feed de video en tiempo real"""
    return HttpResponse("Video feed placeholder", content_type="text/plain")

def upload_image(request):
    """Vista para subir y procesar imágenes"""
    return JsonResponse({'message': 'Upload functionality will be implemented'})

def detect_objects(request):
    """API endpoint para detección en tiempo real"""
    return JsonResponse({'message': 'Detection functionality will be implemented'})
