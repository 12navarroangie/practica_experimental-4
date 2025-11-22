import json
import time
import io
import base64
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .models import DetectionResult
from PIL import Image

# Intentar importar OpenCV y numpy
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

# Variables globales para el streaming de video
camera = None
detection_active = False

class VideoCamera:
    def __init__(self):
        if not OPENCV_AVAILABLE:
            raise Exception("OpenCV no está disponible")
        
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            # Si la cámara principal no está disponible, intentar con índice 1
            self.video = cv2.VideoCapture(1)
        
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Cargar el clasificador Haar Cascade para detección de rostros
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except:
            self.face_cascade = None
        
        self.detection_enabled = True
        
    def __del__(self):
        if hasattr(self, 'video') and self.video:
            self.video.release()
        
    def get_frame(self):
        if not self.video or not self.video.isOpened():
            return None
            
        success, image = self.video.read()
        if not success:
            return None
            
        if self.detection_enabled and self.face_cascade is not None:
            image = self.detect_objects(image)
            
        ret, jpeg = cv2.imencode('.jpg', image)
        if ret:
            return jpeg.tobytes()
        return None
    
    def detect_objects(self, frame):
        try:
            detected_objects = []
            
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
                detected_objects.append('face')
            
            # Detección de cascos (basada en color amarillo/naranja)
            helmets = self.detect_helmets(frame)
            for (x, y, w, h) in helmets:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(frame, 'Helmet', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                detected_objects.append('helmet')
            
            # Detección de teléfonos (basada en forma rectangular)
            phones = self.detect_phones(frame)
            for (x, y, w, h) in phones:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
                cv2.putText(frame, 'Phone', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                detected_objects.append('phone')
            
            # Detección de mascarillas (basada en región facial inferior)
            masks = self.detect_masks(frame, faces)
            for (x, y, w, h) in masks:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'Mask', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected_objects.append('mask')
            
            # Almacenar detección si hay objetos encontrados
            if detected_objects:
                self.save_detection(detected_objects)
                
        except Exception as e:
            print(f"Error en detección: {e}")
        
        return frame
    
    def detect_helmets(self, frame):
        """Detectar cascos basado en color amarillo/naranja"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Rango de colores para cascos (amarillo/naranja)
        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        helmets = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Filtrar por área mínima
                x, y, w, h = cv2.boundingRect(contour)
                # Verificar proporciones típicas de un casco
                if 0.7 <= w/h <= 1.5 and y < frame.shape[0] * 0.6:  # En la parte superior
                    helmets.append((x, y, w, h))
        
        return helmets
    
    def detect_phones(self, frame):
        """Detectar teléfonos basado en forma rectangular"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        phones = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 5000:  # Área típica de un teléfono
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                # Verificar proporciones típicas de un teléfono (vertical u horizontal)
                if (0.4 <= aspect_ratio <= 0.8) or (1.2 <= aspect_ratio <= 2.5):
                    phones.append((x, y, w, h))
        
        return phones
    
    def detect_masks(self, frame, faces):
        """Detectar mascarillas en la región facial inferior"""
        masks = []
        
        for (fx, fy, fw, fh) in faces:
            # Región inferior del rostro donde estaría la mascarilla
            mask_y = fy + int(fh * 0.5)
            mask_h = int(fh * 0.4)
            
            if mask_y + mask_h < frame.shape[0]:
                roi = frame[mask_y:mask_y+mask_h, fx:fx+fw]
                
                # Detectar colores típicos de mascarillas (azul, blanco, negro)
                hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                
                # Máscara para colores típicos de mascarillas
                lower_blue = np.array([100, 50, 50])
                upper_blue = np.array([130, 255, 255])
                mask_blue = cv2.inRange(hsv_roi, lower_blue, upper_blue)
                
                lower_white = np.array([0, 0, 200])
                upper_white = np.array([180, 30, 255])
                mask_white = cv2.inRange(hsv_roi, lower_white, upper_white)
                
                combined_mask = cv2.bitwise_or(mask_blue, mask_white)
                
                # Si hay suficientes píxeles de color de mascarilla
                if np.sum(combined_mask) > roi.shape[0] * roi.shape[1] * 0.3:
                    masks.append((fx, mask_y, fw, mask_h))
        
        return masks
    
    def save_detection(self, detected_objects):
        """Guardar detección en la base de datos"""
        try:
            detection = DetectionResult()
            detection.objects_detected = json.dumps(detected_objects)
            detection.confidence_scores = json.dumps([0.8] * len(detected_objects))
            detection.detection_count = len(detected_objects)
            detection.save()
        except Exception as e:
            print(f"Error guardando detección: {e}")

def index(request):
    """Vista principal de la aplicación"""
    recent_detections = DetectionResult.objects.all()[:5] if DetectionResult else []
    context = {
        'recent_detections': recent_detections,
        'opencv_available': OPENCV_AVAILABLE,
    }
    return render(request, 'detection/index.html', context)

def gen(camera):
    """Generador para el streaming de video"""
    while True:
        if camera:
            frame = camera.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.1)

def video_feed(request):
    """Vista para el feed de video en tiempo real"""
    global camera
    
    if not OPENCV_AVAILABLE:
        return HttpResponse("OpenCV no está disponible. Por favor instale opencv-python.", 
                          content_type="text/plain", status=503)
    
    if camera is None:
        try:
            camera = VideoCamera()
        except Exception as e:
            return HttpResponse(f"Error al acceder a la cámara: {str(e)}", 
                              content_type="text/plain", status=500)
    
    return StreamingHttpResponse(gen(camera),
                               content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def upload_image(request):
    """Vista para subir y procesar imágenes"""
    if not OPENCV_AVAILABLE:
        return JsonResponse({'error': 'OpenCV no está disponible'}, status=503)
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            
            # Leer y procesar la imagen
            image_data = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            # Convertir a formato OpenCV
            nparr = np.frombuffer(image_data, np.uint8)
            cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if cv_image is None:
                return JsonResponse({'error': 'Imagen inválida'}, status=400)
            
            # Realizar detección de objetos
            detected_objects = []
            
            # Detección de rostros
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # Procesar detecciones
            for (x, y, w, h) in faces:
                cv2.rectangle(cv_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(cv_image, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                detected_objects.append('face')
            
            # Detectar cascos usando método auxiliar
            helmets = detect_helmets_static(cv_image)
            for (x, y, w, h) in helmets:
                cv2.rectangle(cv_image, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(cv_image, 'Helmet', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                detected_objects.append('helmet')
            
            # Detectar teléfonos
            phones = detect_phones_static(cv_image)
            for (x, y, w, h) in phones:
                cv2.rectangle(cv_image, (x, y), (x+w, y+h), (255, 255, 0), 2)
                cv2.putText(cv_image, 'Phone', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                detected_objects.append('phone')
            
            # Detectar mascarillas
            masks = detect_masks_static(cv_image, faces)
            for (x, y, w, h) in masks:
                cv2.rectangle(cv_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(cv_image, 'Mask', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                detected_objects.append('mask')
            
            # Guardar imagen procesada
            ret, buffer = cv2.imencode('.jpg', cv_image)
            if not ret:
                return JsonResponse({'error': 'Error al procesar imagen'}, status=500)
            
            processed_image_data = buffer.tobytes()
            
            # Crear registro de detección
            detection_result = DetectionResult()
            
            # Guardar imagen original
            original_path = default_storage.save(
                f'detections/original_{int(time.time())}.jpg',
                ContentFile(image_file.read())
            )
            detection_result.image = original_path
            
            # Guardar imagen procesada
            processed_path = default_storage.save(
                f'processed/processed_{int(time.time())}.jpg',
                ContentFile(processed_image_data)
            )
            
            # Guardar datos de detección
            detection_result.objects_detected = json.dumps(detected_objects)
            detection_result.confidence_scores = json.dumps([0.85] * len(detected_objects))
            detection_result.detection_count = len(detected_objects)
            
            detection_result.save()
            
            return JsonResponse({
                'success': True,
                'detection_count': detection_result.detection_count,
                'objects': detected_objects,
                'original_image_url': settings.MEDIA_URL + original_path,
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
                'objects_detected': ['face', 'person'],
                'coordinates': [[100, 100, 200, 200], [300, 150, 400, 350]],
                'confidence': [0.95, 0.87]
            }
            
            return JsonResponse(detection_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# Funciones auxiliares para detección estática en imágenes subidas

def detect_helmets_static(frame):
    """Detectar cascos basado en color amarillo/naranja en imagen estática"""
    if not OPENCV_AVAILABLE:
        return []
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Rango de colores para cascos (amarillo/naranja)
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    helmets = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:  # Filtrar por área mínima
            x, y, w, h = cv2.boundingRect(contour)
            # Verificar proporciones típicas de un casco
            if 0.7 <= w/h <= 1.5 and y < frame.shape[0] * 0.6:  # En la parte superior
                helmets.append((x, y, w, h))
    
    return helmets

def detect_phones_static(frame):
    """Detectar teléfonos basado en forma rectangular en imagen estática"""
    if not OPENCV_AVAILABLE:
        return []
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    phones = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 500 < area < 5000:  # Área típica de un teléfono
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            # Verificar proporciones típicas de un teléfono (vertical u horizontal)
            if (0.4 <= aspect_ratio <= 0.8) or (1.2 <= aspect_ratio <= 2.5):
                phones.append((x, y, w, h))
    
    return phones

def detect_masks_static(frame, faces):
    """Detectar mascarillas en la región facial inferior en imagen estática"""
    if not OPENCV_AVAILABLE:
        return []
    
    masks = []
    
    for (fx, fy, fw, fh) in faces:
        # Región inferior del rostro donde estaría la mascarilla
        mask_y = fy + int(fh * 0.5)
        mask_h = int(fh * 0.4)
        
        if mask_y + mask_h < frame.shape[0]:
            roi = frame[mask_y:mask_y+mask_h, fx:fx+fw]
            
            # Detectar colores típicos de mascarillas (azul, blanco, negro)
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Máscara para colores típicos de mascarillas
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask_blue = cv2.inRange(hsv_roi, lower_blue, upper_blue)
            
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            mask_white = cv2.inRange(hsv_roi, lower_white, upper_white)
            
            combined_mask = cv2.bitwise_or(mask_blue, mask_white)
            
            # Si hay suficientes píxeles de color de mascarilla
            if np.sum(combined_mask) > roi.shape[0] * roi.shape[1] * 0.3:
                masks.append((fx, mask_y, fw, mask_h))
    
    return masks