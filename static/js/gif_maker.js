// GIF Maker - JavaScript

let currentJobId = null;
let checkInterval = null;
let videoFile = null;

// DOM Elements
const videoFileInput = document.getElementById('video-file-input');
const videoDropZone = document.getElementById('video-drop-zone');
const videoSelected = document.getElementById('video-selected');
const videoName = document.getElementById('video-name');
const videoSize = document.getElementById('video-size');
const gifSettings = document.getElementById('gif-settings');
const captionSection = document.getElementById('caption-section');
const generateSection = document.getElementById('generate-section');
const generateGifBtn = document.getElementById('generate-gif-btn');
const captionText = document.getElementById('caption-text');
const captionPreview = document.getElementById('caption-preview');

// File input handling
videoFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleVideoFile(e.target.files[0]);
    }
});

// Drag and drop
videoDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    videoDropZone.style.borderColor = '#ff3333';
});

videoDropZone.addEventListener('dragleave', () => {
    videoDropZone.style.borderColor = '#333';
});

videoDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    videoDropZone.style.borderColor = '#333';
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('video/'));
    if (files.length > 0) {
        handleVideoFile(files[0]);
    }
});

function handleVideoFile(file) {
    if (file.size > 500 * 1024 * 1024) {
        showError(`File "${file.name}" is too large (max 500MB)`);
        return;
    }
    
    videoFile = file;
    videoName.textContent = file.name;
    videoSize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    videoSelected.style.display = 'block';
    gifSettings.style.display = 'block';
    captionSection.style.display = 'block';
    generateSection.style.display = 'block';
    
    document.getElementById('upload-text').textContent = 'Video selected: ' + file.name;
}

function removeVideo() {
    videoFile = null;
    videoFileInput.value = '';
    videoSelected.style.display = 'none';
    gifSettings.style.display = 'none';
    captionSection.style.display = 'none';
    generateSection.style.display = 'none';
    document.getElementById('upload-text').textContent = 'Drag & Drop your video file here';
    resetPreview();
}

// Caption preview
captionText.addEventListener('input', () => {
    updateCaptionPreview();
});

function updateCaptionPreview() {
    const text = captionText.value;
    if (text) {
        const position = document.getElementById('caption-position').value;
        const size = document.getElementById('caption-size').value;
        const color = document.getElementById('caption-color').value;
        const bg = document.getElementById('caption-bg').value;
        
        captionPreview.textContent = text;
        captionPreview.classList.add('has-text');
        captionPreview.style.fontSize = size + 'px';
        captionPreview.style.color = color;
        captionPreview.style.justifyContent = position === 'top' ? 'flex-start' : 
                                               position === 'bottom' ? 'flex-end' : 'center';
        
        if (bg === 'black') {
            captionPreview.style.background = 'rgba(0, 0, 0, 0.8)';
        } else if (bg === 'white') {
            captionPreview.style.background = 'rgba(255, 255, 255, 0.8)';
            captionPreview.style.color = '#000';
        } else if (bg === 'semi') {
            captionPreview.style.background = 'rgba(0, 0, 0, 0.5)';
        } else {
            captionPreview.style.background = 'transparent';
        }
    } else {
        captionPreview.textContent = 'Caption preview will appear here';
        captionPreview.classList.remove('has-text');
        captionPreview.style.background = '#2a2a2a';
        captionPreview.style.color = '#888';
    }
}

// Update caption preview when settings change
['caption-position', 'caption-size', 'caption-color', 'caption-bg'].forEach(id => {
    document.getElementById(id).addEventListener('change', updateCaptionPreview);
});

// Generate GIF
generateGifBtn.addEventListener('click', async () => {
    if (!videoFile) {
        showError('Please select a video file');
        return;
    }
    
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('start_time', document.getElementById('gif-start-time').value || '0');
    formData.append('duration', document.getElementById('gif-duration').value || '5');
    formData.append('width', document.getElementById('gif-width').value || '640');
    formData.append('fps', document.getElementById('gif-fps').value || '15');
    formData.append('quality', document.getElementById('gif-quality').value || 'medium');
    formData.append('loop', document.getElementById('gif-loop').value || '0');
    
    // Caption settings
    const caption = captionText.value;
    if (caption) {
        formData.append('caption_text', caption);
        formData.append('caption_position', document.getElementById('caption-position').value);
        formData.append('caption_size', document.getElementById('caption-size').value);
        formData.append('caption_color', document.getElementById('caption-color').value);
        formData.append('caption_bg', document.getElementById('caption-bg').value);
    }
    
    try {
        showProgress('Generating GIF...');
        
        const response = await fetch('/create-gif', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            startProgressCheck();
        } else {
            showError(data.error || 'Failed to start GIF generation');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
});

// Progress checking
function startProgressCheck() {
    if (checkInterval) {
        clearInterval(checkInterval);
    }
    
    checkInterval = setInterval(async () => {
        if (!currentJobId) return;
        
        try {
            const response = await fetch(`/status/${currentJobId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateProgress(data);
                
                if (data.status === 'completed') {
                    clearInterval(checkInterval);
                    showResult(data);
                } else if (data.status === 'failed') {
                    clearInterval(checkInterval);
                    showError(data.message || 'GIF generation failed');
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 1000);
}

function updateProgress(data) {
    const progress = data.progress || 0;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('progress-text').textContent = `${progress}%`;
    document.getElementById('progress-message').textContent = data.message || 'Processing...';
}

function showProgress(message) {
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    document.getElementById('progress-title').textContent = message;
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
}

function showResult(data) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'block';
    document.getElementById('error-section').style.display = 'none';
    document.getElementById('result-message').textContent = data.message || 'Your GIF is ready';
    document.getElementById('result-filename').textContent = data.output_filename || 'animated.gif';
}

function showError(message) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

function resetPreview() {
    const preview = document.getElementById('gif-preview');
    preview.innerHTML = `
        <div class="gif-preview-placeholder">
            <i class="fas fa-film"></i>
            <p>Your GIF will appear here</p>
            <p style="font-size: 12px; color: #555; margin-top: 10px;">Upload a video and configure settings to generate your GIF</p>
        </div>
    `;
}

function resetAll() {
    currentJobId = null;
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
}

// Download result
document.getElementById('download-result-btn').addEventListener('click', () => {
    if (currentJobId) {
        window.location.href = `/download/${currentJobId}`;
    }
});

// New GIF button
document.getElementById('new-gif-btn').addEventListener('click', () => {
    resetAll();
    removeVideo();
    captionText.value = '';
    updateCaptionPreview();
});

// Retry button
document.getElementById('retry-btn').addEventListener('click', () => {
    resetAll();
});

// WhatsApp Optimized Preset
function applyWhatsAppPreset() {
    // Optimize for WhatsApp: smaller file size, good quality
    document.getElementById('gif-duration').value = '3';  // 3 seconds max
    document.getElementById('gif-width').value = '480';  // 480px width
    document.getElementById('gif-fps').value = '12';     // 12 FPS
    document.getElementById('gif-quality').value = 'medium'; // Medium quality
    document.getElementById('gif-loop').value = '0';      // Infinite loop
    
    alert('WhatsApp optimized settings applied!\n- Duration: 3 seconds\n- Width: 480px\n- FPS: 12\n- Quality: Medium\n\nThese settings ensure your GIF works perfectly on WhatsApp.');
}

