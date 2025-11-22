# Sistema de Detección de Objetos con Django y OpenCV

Este proyecto implementa un sistema web para detección de objetos en tiempo real utilizando Django y OpenCV.

## Características

- **Detección en tiempo real**: Stream de video desde la cámara web con detección de rostros
- **Análisis de imágenes**: Subida y procesamiento de imágenes estáticas
- **Interfaz moderna**: UI responsiva con Bootstrap 5
- **Base de datos**: Almacenamiento de resultados de detección
- **API REST**: Endpoints para integración con otras aplicaciones

## Tecnologías Utilizadas

- **Backend**: Django 5.2.7
- **Computer Vision**: OpenCV 4.12.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de datos**: SQLite (Django ORM)
- **Procesamiento de imágenes**: Pillow, NumPy

## Estructura del Proyecto

```
object_detection_app/
├── manage.py
├── requirements.txt
├── object_detection_app/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── detection/
│   ├── models.py          # Modelo para resultados de detección
│   ├── views.py           # Lógica de vistas y detección
│   ├── urls.py            # Rutas de la aplicación
│   ├── templates/
│   │   └── detection/
│   │       ├── base.html
│   │       └── index.html
│   └── migrations/
├── static/
│   ├── css/
│   │   └── style.css      # Estilos personalizados
│   └── js/
│       └── detection.js   # JavaScript para funcionalidad dinámica
└── media/
    ├── detections/        # Imágenes originales
    └── processed/         # Imágenes procesadas
```

## Instalación y Configuración

### Prerequisitos

- Python 3.8 o superior
- Cámara web (para detección en tiempo real)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd practica-3
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   # Windows
   venv\\Scripts\\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar migraciones**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear superusuario (opcional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

7. **Acceder a la aplicación**
   - Abrir navegador en: `http://127.0.0.1:8000`

## Funcionalidades

### 1. Detección en Tiempo Real
- Acceso a la cámara web del dispositivo
- Detección de rostros usando Haar Cascades
- Visualización en tiempo real con marcadores
- Contadores dinámicos de objetos detectados

### 2. Análisis de Imágenes
- Subida de imágenes (JPG, PNG, GIF)
- Procesamiento automático
- Detección de múltiples tipos de objetos:
  - Rostros humanos
  - Cascos de seguridad
  - Dispositivos móviles
- Resultados con coordenadas y confianza

### 3. Historial de Detecciones
- Almacenamiento en base de datos
- Visualización de detecciones recientes
- Estadísticas de objetos detectados

## API Endpoints

### GET `/`
Página principal de la aplicación

### GET `/video_feed/`
Stream de video en tiempo real con detección

### POST `/upload/`
Subida y procesamiento de imágenes
- **Parámetros**: `image` (archivo de imagen)
- **Respuesta**: JSON con resultados de detección

### GET `/detect/`
Obtener datos de detección en tiempo real
- **Respuesta**: JSON con objetos detectados y coordenadas

## Configuración Avanzada

### Personalizar Detección

En `detection/views.py`, puedes modificar los parámetros de detección:

```python
# Parámetros de Haar Cascade
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # Factor de escala
    minNeighbors=5,       # Vecinos mínimos
    minSize=(30, 30)      # Tamaño mínimo
)
```

### Agregar Nuevos Tipos de Detección

1. Descargar clasificadores adicionales de OpenCV
2. Cargar en la clase `VideoCamera`
3. Implementar lógica de detección en `detect_objects()`

## Solución de Problemas

### Error: "No se puede acceder a la cámara"
- Verificar que la cámara no esté siendo usada por otra aplicación
- Comprobar permisos de cámara en el sistema operativo
- Probar con diferentes índices de cámara (0, 1, 2, etc.)

### Error: "OpenCV no está disponible"
```bash
pip uninstall opencv-python
pip install opencv-python==4.12.0.88
```

### Error: "ModuleNotFoundError: No module named 'cv2'"
```bash
pip install opencv-python numpy
```

## Desarrollo y Extensiones

### Agregar Nuevos Modelos de Detección

1. **YOLO (You Only Look Once)**
   - Descargar pesos de YOLO
   - Modificar `process_image_for_detection()`
   
2. **TensorFlow/Keras**
   - Integrar modelos pre-entrenados
   - Agregar dependencias a `requirements.txt`

3. **MediaPipe**
   - Para detección de poses y gestos
   - Instalar: `pip install mediapipe`

### Mejoras de UI

- Agregar gráficos en tiempo real con Chart.js
- Implementar notificaciones push
- Añadir modo oscuro
- Responsive design para móviles

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## Contacto

- **Proyecto**: Sistema de Detección de Objetos
- **Tecnologías**: Django + OpenCV
- **Año**: 2024

---

## Notas Técnicas

### Algoritmos de Detección Implementados

1. **Haar Cascades**
   - Método clásico y rápido
   - Ideal para detección de rostros
   - Incluido en OpenCV

2. **Detección por Color**
   - Segmentación HSV
   - Filtrado por área y forma
   - Para objetos con colores distintivos

3. **Detección de Círculos (Hough)**
   - Para objetos circulares como cascos
   - Transformada de Hough
   - Parámetros ajustables

### Rendimiento

- **FPS**: 15-30 según hardware
- **Resolución**: 640x480 (configurable)
- **Latencia**: <100ms en procesamiento local

### Seguridad

- Validación de archivos subidos
- Límites de tamaño de imagen
- Sanitización de datos de entrada
- CSRF protection habilitado
