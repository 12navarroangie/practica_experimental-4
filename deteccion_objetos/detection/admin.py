from django.contrib import admin
from .models import DetectionResult

@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'detection_count', 'created_at', 'get_objects_preview')
    list_filter = ('created_at', 'detection_count')
    search_fields = ('objects_detected',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_objects_preview(self, obj):
        """Muestra una preview de los objetos detectados"""
        try:
            import json
            objects = json.loads(obj.objects_detected) if obj.objects_detected else []
            return ', '.join(objects[:3]) + ('...' if len(objects) > 3 else '')
        except:
            return 'Error parsing objects'
    
    get_objects_preview.short_description = 'Objects Detected'
    
    fieldsets = (
        ('Detection Information', {
            'fields': ('detection_count', 'objects_detected', 'confidence_scores')
        }),
        ('Images', {
            'fields': ('image', 'processed_image')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
