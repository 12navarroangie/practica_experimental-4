#!/usr/bin/env python
"""
Script de Auditoría y Monitor de Datos de Detección
Este script permite gestionar y analizar los registros de la base de datos
simulando un panel de monitoreo de seguridad.
"""

import os
import sys
import django
from django.conf import settings
import json
from django.utils import timezone
from datetime import timedelta
from collections import Counter

# 🚨 IMPORTANTE: Reemplaza 'your_project_name' con el nombre de tu proyecto Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings') 
django.setup()

# Asumimos que el modelo de resultados de detección se llama 'DetectionResult'
# Asegúrate de que esta importación coincida con la estructura de tu app
from detection.models import DetectionResult 


# ---------------------------------------------
# Funciones de Generación de Datos de Auditoría
# ---------------------------------------------

def generate_audit_records():
    """Genera registros simulados de eventos de seguridad y auditoría."""
    print("🚀 Generando registros de auditoría y seguridad simulados...")
    
    # Eventos de Seguridad de Ejemplo
    security_events = [
        {
            'detected_labels': ['helmet', 'safety_vest', 'person'],
            'risk_level': 1,
            'location_zone': 'Zone A: Entry Point',
            'audit_summary': 'Acceso autorizado con EPP completo.'
        },
        {
            'detected_labels': ['no_helmet', 'person'],
            'risk_level': 3,
            'location_zone': 'Zone B: Restricted Area',
            'audit_summary': 'INCIDENTE: Acceso sin casco en área restringida.'
        },
        {
            'detected_labels': ['face', 'phone', 'person'],
            'risk_level': 2,
            'location_zone': 'Zone C: Assembly Line',
            'audit_summary': 'Uso de teléfono móvil detectado en línea de montaje.'
        },
        {
            'detected_labels': ['person', 'intruder_mask'],
            'risk_level': 4,
            'location_zone': 'Zone D: Storage Vault',
            'audit_summary': 'ALARMA CRÍTICA: Intruso detectado.'
        }
    ]
    
    # Mapeo de campos para guardar en el modelo DetectionResult
    for i, event in enumerate(security_events):
        record = DetectionResult()
        
        # Guardamos las etiquetas y el nivel de riesgo en los campos existentes
        record.objects_detected = json.dumps(event['detected_labels']) # Usado para almacenar las etiquetas
        record.confidence_scores = json.dumps([event['risk_level'] / 5.0]) # Guardamos el riesgo normalizado
        record.detection_count = len(event['detected_labels'])
        
        # Usamos el campo 'created_at' para simular eventos recientes
        record.created_at = timezone.now() - timedelta(minutes=i*30) 
        
        record.save()
        print(f"✅ Registro de Auditoría #{record.id} (Riesgo {event['risk_level']}): {event['audit_summary']}")
    
    print(f"\n🎉 Se han generado {len(security_events)} registros de auditoría simulados.")

# ---------------------------------------------
# Funciones de Reporte y Análisis
# ---------------------------------------------

def show_risk_analysis():
    """Analiza y reporta los niveles de riesgo detectados."""
    print("\n📈 ANÁLISIS DE RIESGO DETECTADO")
    print("="*50)
    
    total_records = DetectionResult.objects.count()
    print(f"Total de registros de auditoría: {total_records}")
    
    if total_records == 0:
        print("No hay datos para analizar. Genera registros (Opción 1).")
        return

    # Contar la frecuencia de cada etiqueta detectada
    all_labels = []
    for record in DetectionResult.objects.all():
        if record.objects_detected:
            try:
                labels = json.loads(record.objects_detected)
                all_labels.extend(labels)
            except:
                continue

    label_counts = Counter(all_labels)
    
    print("\nFrecuencia de Etiquetas de Riesgo/Seguridad:")
    if label_counts:
        for label, count in label_counts.most_common():
            print(f"  - {label.capitalize()}: {count} veces")
    else:
        print("No se pudieron parsear etiquetas de objetos.")

    # Calcular el riesgo promedio
    try:
        total_risk_sum = sum(json.loads(r.confidence_scores)[0] for r in DetectionResult.objects.all() if r.confidence_scores)
        average_risk = (total_risk_sum / total_records) * 5 # Desnormalizar a escala 1-5
        print(f"\nNivel de Riesgo Promedio (Escala 1-5): {average_risk:.2f}")
    except:
        print("\nAdvertencia: No se pudo calcular el riesgo promedio.")


def remove_all_records():
    """Elimina todos los registros de la base de datos."""
    count = DetectionResult.objects.count()
    if count > 0:
        DetectionResult.objects.all().delete()
        print(f"🧹 Se eliminaron {count} registros de la base de datos.")
    else:
        print("🧹 No hay registros para limpiar.")

# ---------------------------------------------
# Menú Principal
# ---------------------------------------------

def main():
    """Función principal del menú interactivo."""
    print("🔍 AUDITORÍA DEL SISTEMA DE SEGURIDAD VISUAL")
    print("="*50)
    
    while True:
        print("\nOpciones de Auditoría y Gestión:")
        print("1. Generar Registros de Auditoría (Datos de prueba)")
        print("2. Mostrar Análisis de Riesgo")
        print("3. Limpiar Base de Datos (Eliminar todos los registros)")
        print("4. Salir")
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        
        if choice == '1':
            generate_audit_records()
        elif choice == '2':
            show_risk_analysis()
        elif choice == '3':
            remove_all_records()
        elif choice == '4':
            print("👋 Finalizando auditoría.")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == '__main__':
    main()