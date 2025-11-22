#!/usr/bin/env python
"""
Pruebas automáticas para el Sistema de Detección de Objetos
Versión  
"""

import requests
import time
import io
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------
# Funciones auxiliares
# ---------------------------------------------
def log(tittle):
    print("\n🟪 " + tittle)
    print("─" * 45)


# ---------------------------------------------
# 1. Comprobación de página principal
# ---------------------------------------------
def check_homepage():
    log("Prueba: Página de inicio")
    try:
        r = requests.get(BASE_URL)
        if r.status_code == 200:
            print("✔ Página principal responde correctamente")
            return True
        print(f"✖ Error código: {r.status_code}")
        return False
    except Exception as e:
        print(f"✖ Error al conectar: {e}")
        return False


# ---------------------------------------------
# 2. Comprobación endpoint de detección
# ---------------------------------------------
def check_detection():
    log("Prueba: API de procesamiento")
    try:
        r = requests.get(f"{BASE_URL}/detect/")
        if r.status_code == 200:
            data = r.json()
            print("✔ API responde correctamente")
            print("   Objetos:", data.get("objects_detected"))
            return True
        print(f"✖ Código inesperado: {r.status_code}")
        return False
    except Exception as e:
        print("✖ Error en la API:", e)
        return False


# ---------------------------------------------
# 3. Verificar feed de video
# ---------------------------------------------
def check_video():
    log("Prueba: Flujo de video")
    try:
        r = requests.get(f"{BASE_URL}/video_feed/", stream=True, timeout=4)
        if r.status_code in [200, 500, 503]:
            print("✔ Endpoint del video responde (cámara disponible/no disponible)")
            return True
        print("✖ Código inesperado:", r.status_code)
        return False
    except Exception as e:
        print("✖ Error revisando feed:", e)
        return False


# ---------------------------------------------
# 4. Prueba subida de imagen
# ---------------------------------------------
def check_upload():
    log("Prueba: Subida de imágenes")
    try:
        # Crear una imagen roja temporal
        img = Image.new("RGB", (120, 120), "red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        files = {"image": ("temp.jpg", buffer, "image/jpeg")}
        r = requests.post(f"{BASE_URL}/upload/", files=files)

        if r.status_code == 200:
            data = r.json()
            print("✔ Imagen procesada correctamente")
            print("   Detectados:", data.get("objects"))
            return True

        print("✖ Error código:", r.status_code)
        return False

    except Exception as e:
        print("✖ Error enviando imagen:", e)
        return False


# ---------------------------------------------
# 5. Verificar panel admin
# ---------------------------------------------
def check_admin():
    log("Prueba: Panel Administrativo")
    try:
        r = requests.get(f"{BASE_URL}/admin/")
        if r.status_code == 200:
            print("✔ Panel admin accesible")
            return True
        print("✖ Código:", r.status_code)
        return False
    except Exception as e:
        print("✖ Error:", e)
        return False


# ---------------------------------------------
# EJECUCIÓN GENERAL
# ---------------------------------------------
def run_all():
    print("🟣 SISTEMA DE DETECCIÓN – PANEL DE PRUEBAS")
    print("=" * 55)
    time.sleep(1)

    tests = {
        "Inicio": check_homepage,
        "API": check_detection,
        "Video": check_video,
        "Upload": check_upload,
        "Admin": check_admin
    }

    passed = 0
    total = len(tests)

    for name, func in tests.items():
        result = func()
        if result:
            passed += 1
        time.sleep(0.8)

    print("\n" + "=" * 55)
    print("📊 **RESULTADO FINAL**")
    print(f"   {passed}/{total} pruebas correctas")

    if passed == total:
        print("🎉 Todo funcionando correctamente")
    else:
        print("⚠ Revisar pruebas fallidas")

    print("=" * 55)


if __name__ == "__main__":
    run_all()
