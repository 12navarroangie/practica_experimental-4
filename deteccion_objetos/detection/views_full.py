try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # Mock cv2 for demonstration
    class MockCV2:
        def VideoCapture(self, *args): 
            return None
        def CascadeClassifier(self, *args): 
            return None
        def imread(self, *args): 
            return None
        def imencode(self, *args): 
            return True, b'fake_image'
        def imdecode(self, *args): 
            return None
    cv2 = MockCV2()
    np = None

import json
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import threading
import time
import os
from .models import DetectionResult
from PIL import Image
import io
import base64

# Variables globales para el streaming de video
camera = None
detection_active = False

class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Cargar el clasificador Haar Cascade para detección de rostros
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Cargar YOLO para detección de objetos (simulado con detección básica)
        self.detection_enabled = True
        
    def __del__(self):
        self.video.release()
        
    def get_frame(self):
        success, image = self.video.read()
        if not success:
            return None
            
        if self.detection_enabled:
            image = self.detect_objects(image)
            
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
        # ...código existente...
    
    def detect_objects(request):
        """API endpoint para detección en tiempo real"""
        global camera
        if request.method == 'GET':
            try:
                # Si la cámara está activa y tiene método para obtener los últimos objetos detectados
                if camera and hasattr(camera, 'last_detected_objects'):
                    detected = camera.last_detected_objects
                else:
                    # Simulación para pruebas: incluye mask y phone
                    detected = ['face', 'helmet', 'phone', 'mask']
                detection_data = {
                    'timestamp': int(time.time()),
                    'objects_detected': detected,
                    'coordinates': [],
                    'confidence': []
                }
                return JsonResponse(detection_data)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'Método no permitido'}, status=405)        # ...código existente...
        
        def detect_objects(request):
            """API endpoint para detección en tiempo real"""
            global camera
            if request.method == 'GET':
                try:
                    # Si la cámara está activa y tiene método para obtener los últimos objetos detectados
                    if camera and hasattr(camera, 'last_detected_objects'):
                        detected = camera.last_detected_objects
                    else:
                        # Simulación para pruebas: incluye mask y phone
                        detected = ['face', 'helmet', 'phone', 'mask']
                    detection_data = {
                        'timestamp': int(time.time()),
                        'objects_detected': detected,
                        'coordinates': [],
                        'confidence': []
                    }
                    return JsonResponse(detection_data)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)
            return JsonResponse({'error': 'Método no permitido'}, status=405)
    def detect_objects(self, frame):
        # Detección de rostros usando Haar Cascades
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Dibujar rectángulos alrededor de los rostros detectados
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        # Detección simple de movimiento/objetos usando contornos
        # Convertir a HSV para mejor detección de colores
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detectar objetos de colores específicos (ejemplo: objetos rojos)
        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red, upper_red)
        
        lower_red = np.array([170, 50, 50])
        upper_red = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red, upper_red)
        
        mask = mask1 + mask2
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Dibujar contornos para objetos detectados
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filtrar objetos pequeños
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return frame

def index(request):
    """Vista principal de la aplicación"""
    recent_detections = DetectionResult.objects.all()[:5]
    return render(request, 'detection/index.html', {
        'recent_detections': recent_detections
    })

def gen(camera):
    """Generador para el streaming de video"""
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.1)

def video_feed(request):
    """Vista para el feed de video en tiempo real"""
    global camera
    
    if camera is None:
        try:
            camera = VideoCamera()
        except Exception as e:
            return HttpResponse(f"Error al acceder a la cámara: {str(e)}", status=500)
    
    return StreamingHttpResponse(gen(camera),
                               content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def upload_image(request):
    """Vista para subir y procesar imágenes"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            
            # Leer la imagen
            image_data = image_file.read()
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return JsonResponse({'error': 'Imagen no válida'}, status=400)
            
            # Procesar la imagen para detectar objetos
            processed_img, detection_data = process_image_for_detection(img)
            
            # Guardar la imagen original y procesada
            detection_result = DetectionResult()
            
            # Guardar imagen original
            original_path = default_storage.save(
                f'detections/original_{int(time.time())}.jpg',
                ContentFile(image_data)
            )
            detection_result.image = original_path
            
            # Guardar imagen procesada
            _, buffer = cv2.imencode('.jpg', processed_img)
            processed_path = default_storage.save(
                f'processed/processed_{int(time.time())}.jpg',
                ContentFile(buffer.tobytes())
            )
            detection_result.processed_image = processed_path
            
            # Guardar datos de detección
            detection_result.objects_detected = json.dumps(detection_data['objects'])
            detection_result.confidence_scores = json.dumps(detection_data['scores'])
            detection_result.detection_count = len(detection_data['objects'])
            
            detection_result.save()
            
            return JsonResponse({
                'success': True,
                'detection_count': detection_result.detection_count,
                'objects': detection_data['objects'],
                'processed_image_url': settings.MEDIA_URL + processed_path,
                'id': detection_result.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def detect_objects(request):
    """API endpoint para detección en tiempo real"""
    if request.method == 'GET':
        try:
            # Simular datos de detección en tiempo real
            detection_data = {
                'timestamp': int(time.time()),
                'objects_detected': ['face', 'person', 'phone'],
                'coordinates': [[100, 100, 200, 200], [300, 150, 400, 350], [500, 200, 550, 280]],
                'confidence': [0.95, 0.87, 0.72]
            }
            
            return JsonResponse(detection_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def process_image_for_detection(image):
    """Procesa una imagen para detectar objetos"""
    # Hacer una copia de la imagen para procesar
    processed_img = image.copy()
    
    detection_data = {
        'objects': [],
        'scores': [],
        'coordinates': []
    }
    
    # Cargar el clasificador Haar Cascade para detección de rostros
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detectar rostros
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    # Procesar rostros detectados
    for (x, y, w, h) in faces:
        cv2.rectangle(processed_img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(processed_img, f'Face (0.95)', (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        detection_data['objects'].append('face')
        detection_data['scores'].append(0.95)
        detection_data['coordinates'].append([x, y, x+w, y+h])
    
    # Detección de objetos por color (ejemplo: celulares como objetos rectangulares oscuros)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Detectar objetos oscuros (posibles celulares)
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 50])
    mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)
    
    # Aplicar operaciones morfológicas para limpiar la máscara
    kernel = np.ones((3,3), np.uint8)
    mask_dark = cv2.morphologyEx(mask_dark, cv2.MORPH_CLOSE, kernel)
    mask_dark = cv2.morphologyEx(mask_dark, cv2.MORPH_OPEN, kernel)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if 1000 < area < 10000:  # Filtrar por tamaño apropiado para celulares
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w)/h
            
            # Los celulares tienen una proporción específica
            if 0.4 < aspect_ratio < 0.8:
                cv2.rectangle(processed_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(processed_img, f'Phone (0.78)', (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                detection_data['objects'].append('phone')
                detection_data['scores'].append(0.78)
                detection_data['coordinates'].append([x, y, x+w, y+h])
    
    # Detección de cascos (objetos circulares en la parte superior)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                              param1=50, param2=30, minRadius=20, maxRadius=80)
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            # Verificar si está en la parte superior de la imagen (posible casco)
            if y < image.shape[0] * 0.4:  # En el 40% superior de la imagen
                cv2.circle(processed_img, (x, y), r, (0, 0, 255), 2)
                cv2.putText(processed_img, f'Helmet (0.82)', (x-r, y-r-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                detection_data['objects'].append('helmet')
                detection_data['scores'].append(0.82)
                detection_data['coordinates'].append([x-r, y-r, x+r, y+r])
    
    return processed_img, detection_data
