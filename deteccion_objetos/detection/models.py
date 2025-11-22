from django.db import models
from django.utils import timezone

class DetectionResult(models.Model):
    image = models.ImageField(upload_to='detections/')
    processed_image = models.ImageField(upload_to='processed/', blank=True, null=True)
    objects_detected = models.TextField(blank=True)
    confidence_scores = models.TextField(blank=True)
    detection_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Detection {self.id} - {self.detection_count} objects found"
