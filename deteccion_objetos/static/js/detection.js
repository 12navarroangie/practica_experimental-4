// Object Detection JavaScript Functions

$(document).ready(function() {
    // Video controls
    let videoActive = false;
    let detectionInterval;
    
    // Initialize video controls
    $('#start-video').click(function() {
        startVideo();
    });
    
    $('#stop-video').click(function() {
        stopVideo();
    });
    
    $('#capture-frame').click(function() {
        captureFrame();
    });
    
    // Image upload form
    $('#upload-form').submit(function(e) {
        e.preventDefault();
        uploadImage();
    });
    
    // File input preview
    $('#image-input').change(function() {
        previewImage(this);
    });
    
    // Start video function
    function startVideo() {
        videoActive = true;
        $('#start-video').prop('disabled', true);
        $('#stop-video').prop('disabled', false);
        $('#video-stream').attr('src', '/video_feed/');
        
        // Start detection updates
        detectionInterval = setInterval(updateDetectionResults, 2000);
        
        showToast('Video iniciado', 'success');
    }
    
    // Stop video function
    function stopVideo() {
        videoActive = false;
        $('#start-video').prop('disabled', false);
        $('#stop-video').prop('disabled', true);
        
        // Stop detection updates
        clearInterval(detectionInterval);
        
        // Reset video source
        $('#video-stream').attr('src', '');
        
        showToast('Video detenido', 'warning');
    }
    
    // Capture frame function
    function captureFrame() {
        if (!videoActive) {
            showToast('Inicia el video primero', 'error');
            return;
        }
        
        // Create canvas to capture frame
        const video = document.getElementById('video-stream');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = video.width;
        canvas.height = video.height;
        ctx.drawImage(video, 0, 0);
        
        // Convert to blob and trigger download
        canvas.toBlob(function(blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `capture_${new Date().getTime()}.jpg`;
            a.click();
            URL.revokeObjectURL(url);
        });
        
        showToast('Frame capturado', 'success');
    }
    
    // Upload image function
    function uploadImage() {
        const formData = new FormData();
        const imageFile = $('#image-input')[0].files[0];
        
        if (!imageFile) {
            showToast('Selecciona una imagen primero', 'error');
            return;
        }
        
        formData.append('image', imageFile);
        
        // Show loading modal
        $('#loadingModal').modal('show');
        
        $.ajax({
            url: '/upload/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#loadingModal').modal('hide');
                
                if (response.success) {
                    displayUploadResults(response);
                    showToast(`${response.detection_count} objetos detectados`, 'success');
                } else {
                    showToast('Error en la detección', 'error');
                }
            },
            error: function(xhr) {
                $('#loadingModal').modal('hide');
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
                showToast(`Error: ${error}`, 'error');
            }
        });
    }
    
    // Preview uploaded image
    function previewImage(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                $('#original-image').attr('src', e.target.result);
                $('#image-preview').removeClass('d-none');
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    }
    
    // Display upload results
    function displayUploadResults(response) {
        // Show processed image
        $('#processed-image').attr('src', response.processed_image_url);
        
        // Show detection summary
        let summary = `<strong>Objetos detectados:</strong> ${response.detection_count}<br>`;
        summary += '<ul class="mb-0">';
        
        response.objects.forEach((obj, index) => {
            const confidence = response.confidence_scores ? 
                (response.confidence_scores[index] * 100).toFixed(1) : 'N/A';
            summary += `<li>${obj} (Confianza: ${confidence}%)</li>`;
        });
        
        summary += '</ul>';
        
        $('#detection-summary').html(summary);
        $('#upload-results').removeClass('d-none');
        
        // Scroll to results
        $('html, body').animate({
            scrollTop: $('#upload-results').offset().top - 100
        }, 500);
    }
    
    // Update detection results from video
    function updateDetectionResults() {
        if (!videoActive) return;
        
        $.ajax({
            url: '/detect/',
            type: 'GET',
            success: function(data) {
                if (data.objects_detected) {
                    updateCounters(data.objects_detected);
                }
            },
            error: function() {
                console.log('Error updating detection results');
            }
        });
    }
    
    // Update object counters
    function updateCounters(objects) {
        const facesCount = objects.filter(obj => obj === 'face').length;
        const helmetsCount = objects.filter(obj => obj === 'helmet').length;
        const phonesCount = objects.filter(obj => obj === 'phone').length;
        
        animateCounter('#face-count', facesCount);
        animateCounter('#helmet-count', helmetsCount);
        animateCounter('#phone-count', phonesCount);
    }
    
    // Animate counter updates
    function animateCounter(selector, newValue) {
        const $counter = $(selector);
        const currentValue = parseInt($counter.text()) || 0;
        
        if (currentValue !== newValue) {
            $counter.addClass('counter-animation');
            $counter.text(newValue);
            
            setTimeout(() => {
                $counter.removeClass('counter-animation');
            }, 500);
        }
    }
    
    // Show toast notifications
    function showToast(message, type = 'info') {
        const toastClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        const toast = $(`
            <div class="toast align-items-center text-white ${toastClass} border-0 position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999;" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        
        $('body').append(toast);
        
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // Drag and drop functionality for image upload
    const uploadArea = $('#upload-form');
    
    uploadArea.on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('drag-over');
    });
    
    uploadArea.on('dragleave', function(e) {
        e.preventDefault();
        $(this).removeClass('drag-over');
    });
    
    uploadArea.on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('drag-over');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            $('#image-input')[0].files = files;
            previewImage($('#image-input')[0]);
        }
    });
    
    // Smooth scrolling for navigation links
    $('a[href^="#"]').click(function(e) {
        e.preventDefault();
        
        const target = $($(this).attr('href'));
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 80
            }, 500);
        }
    });
    
    // Auto-refresh detection stats every 5 seconds
    setInterval(function() {
        if (videoActive) {
            updateDetectionResults();
        }
    }, 5000);
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Error handling for video stream
    $('#video-stream').on('error', function() {
        if (videoActive) {
            showToast('Error en el stream de video', 'error');
            stopVideo();
        }
    });
    
    // Keyboard shortcuts
    $(document).keydown(function(e) {
        // Space bar to start/stop video
        if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
            e.preventDefault();
            if (videoActive) {
                stopVideo();
            } else {
                startVideo();
            }
        }
        
        // C key to capture frame
        if (e.code === 'KeyC' && e.ctrlKey && videoActive) {
            e.preventDefault();
            captureFrame();
        }
    });
    
    // Show keyboard shortcuts help
    function showKeyboardHelp() {
        const helpModal = $(`
            <div class="modal fade" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Atajos de Teclado</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <ul class="list-unstyled">
                                <li><kbd>Espacio</kbd> - Iniciar/Detener video</li>
                                <li><kbd>Ctrl + C</kbd> - Capturar frame</li>
                                <li><kbd>?</kbd> - Mostrar esta ayuda</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        $('body').append(helpModal);
        helpModal.modal('show');
        
        helpModal.on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }
    
    // Show help with ? key
    $(document).keydown(function(e) {
        if (e.code === 'Slash' && e.shiftKey) {
            e.preventDefault();
            showKeyboardHelp();
        }
    });
    
    console.log('Object Detection App initialized successfully!');
});
