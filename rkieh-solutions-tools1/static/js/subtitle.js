// Subtitle Downloader - JavaScript

let currentJobId = null;
let checkInterval = null;
let selectedFile = null;
let currentSource = 'youtube';

// DOM Elements
const subtitleForm = document.getElementById('subtitle-form');
const videoUrl = document.getElementById('video-url');
const videoFile = document.getElementById('video-file');
const downloadBtn = document.getElementById('download-btn');
const downloadBtnText = document.getElementById('download-btn-text');
const qualitySection = document.getElementById('quality-section');
const urlInputGroup = document.getElementById('url-input-group');
const fileInputGroup = document.getElementById('file-input-group');
const videoDropZone = document.getElementById('video-drop-zone');
const selectedFileInfo = document.getElementById('selected-file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');
const downloadTypeCard = document.getElementById('download-type-card');
const actionTypeCard = document.getElementById('action-type-card');
const langNote = document.getElementById('lang-note');
const subtitleFileUpload = document.getElementById('subtitle-file-upload');
const subtitleFilesInput = document.getElementById('subtitle-files');

const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressMessage = document.getElementById('progress-message');
const progressTitle = document.getElementById('progress-title');
const downloadInfo = document.getElementById('download-info');
const cancelBtn = document.getElementById('cancel-btn');

const resultSection = document.getElementById('result-section');
const resultMessage = document.getElementById('result-message');
const resultDetails = document.getElementById('result-details');
const downloadResultBtn = document.getElementById('download-result-btn');
const newDownloadBtn = document.getElementById('new-download-btn');

const errorSection = document.getElementById('error-section');
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');

// Source Selector
document.querySelectorAll('.source-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.source-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        currentSource = btn.getAttribute('data-source');
        
        if (currentSource === 'youtube') {
            urlInputGroup.style.display = 'block';
            fileInputGroup.style.display = 'none';
            downloadTypeCard.style.display = 'block';
            actionTypeCard.style.display = 'none';
            qualitySection.style.display = 'block';
            videoUrl.required = true;
            langNote.textContent = 'Hold Ctrl/Cmd to select multiple';
        } else {
            urlInputGroup.style.display = 'none';
            fileInputGroup.style.display = 'block';
            downloadTypeCard.style.display = 'none';
            actionTypeCard.style.display = 'block';
            qualitySection.style.display = 'none';
            videoUrl.required = false;
            langNote.textContent = 'For auto-translation (requires internet)';
        }
    });
});

// File Upload Handling
videoFile.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and Drop
videoDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    videoDropZone.classList.add('drag-over');
});

videoDropZone.addEventListener('dragleave', () => {
    videoDropZone.classList.remove('drag-over');
});

videoDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    videoDropZone.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
        handleFileSelect(file);
    } else {
        showError('Please select a valid video file');
    }
});

// Handle file selection
function handleFileSelect(file) {
    const maxSize = 500 * 1024 * 1024; // 500MB
    
    if (file.size > maxSize) {
        showError('File is too large. Maximum size is 500MB');
        return;
    }
    
    selectedFile = file;
    videoDropZone.style.display = 'none';
    selectedFileInfo.style.display = 'block';
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
}

// Remove selected file
removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    videoFile.value = '';
    videoDropZone.style.display = 'block';
    selectedFileInfo.style.display = 'none';
});

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Show/Hide subtitle file upload based on action type
document.querySelectorAll('input[name="action_type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'add') {
            subtitleFileUpload.style.display = 'block';
        } else {
            subtitleFileUpload.style.display = 'none';
        }
    });
});

// Show/Hide quality section based on download type
document.querySelectorAll('input[name="download_type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'subs_only') {
            qualitySection.style.display = 'none';
        } else {
            qualitySection.style.display = 'block';
        }
    });
});

// Form Submit
subtitleForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate based on source type
    if (currentSource === 'youtube') {
        const url = videoUrl.value.trim();
        if (!url) {
            showError('Please enter a valid YouTube URL');
            return;
        }
    } else {
        if (!selectedFile) {
            showError('Please select a video file');
            return;
        }
    }
    
    // Get selected languages
    const sourceLanguage = document.getElementById('source-language').value;
    const targetLanguage = document.getElementById('target-language').value;
    
    if (!sourceLanguage || !targetLanguage) {
        showError('Please select both video language and subtitle language');
        return;
    }
    
    // Get form data
    const subtitleFormat = document.getElementById('subtitle-format').value;
    
    try {
        showProgress('Initializing...');
        
        let response;
        
        if (currentSource === 'youtube') {
            // YouTube download
            const url = videoUrl.value.trim();
            const downloadType = document.querySelector('input[name="download_type"]:checked').value;
            const videoQuality = document.getElementById('video-quality').value;
            
            response = await fetch('/download-subtitles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url,
                    source_language: sourceLanguage,
                    target_language: targetLanguage,
                    download_type: downloadType,
                    subtitle_format: subtitleFormat,
                    auto_generated: true,
                    video_quality: videoQuality
                })
            });
        } else {
            // Video upload
            const actionType = document.querySelector('input[name="action_type"]:checked').value;
            const formData = new FormData();
            formData.append('video', selectedFile);
            formData.append('languages', JSON.stringify(selectedLanguages));
            formData.append('action_type', actionType);
            formData.append('subtitle_format', subtitleFormat);
            formData.append('translate', translate);
            
            // Add subtitle files if action is 'add'
            if (actionType === 'add' && subtitleFilesInput.files.length > 0) {
                for (let i = 0; i < subtitleFilesInput.files.length; i++) {
                    formData.append('subtitle_files', subtitleFilesInput.files[i]);
                }
            }
            
            response = await fetch('/process-video-subtitles', {
                method: 'POST',
                body: formData
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            cancelBtn.style.display = 'inline-flex';
            startProgressCheck();
        } else {
            showError(data.error || 'Failed to start download');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
});

// Start progress checking
function startProgressCheck() {
    checkInterval = setInterval(checkProgress, 1000);
}

// Check progress
async function checkProgress() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/status/${currentJobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            clearInterval(checkInterval);
            showResult(data);
        } else if (data.status === 'failed') {
            clearInterval(checkInterval);
            showError(data.message || 'Download failed');
        } else if (data.status === 'cancelled') {
            clearInterval(checkInterval);
            showError('Download cancelled');
        } else {
            updateProgress(data.progress, data.message, data.download_info);
        }
    } catch (error) {
        console.error('Progress check error:', error);
    }
}

// Update progress
function updateProgress(percent, message, info) {
    progressFill.style.width = percent + '%';
    progressText.textContent = Math.round(percent) + '%';
    progressMessage.textContent = message || 'Processing...';
    
    if (info) {
        downloadInfo.style.display = 'grid';
        document.getElementById('downloaded-size').textContent = info.downloaded || '0 MB';
        document.getElementById('total-size').textContent = info.total || '-- MB';
        document.getElementById('download-speed').textContent = info.speed || '-- MB/s';
        document.getElementById('download-eta').textContent = info.eta || '--:--';
    }
}

// Show progress section
function showProgress(message) {
    subtitleForm.style.display = 'none';
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    progressMessage.textContent = message;
    downloadInfo.style.display = 'none';
    cancelBtn.style.display = 'none';
}

// Show result section
function showResult(data) {
    subtitleForm.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    errorSection.style.display = 'none';
    
    resultMessage.textContent = 'Download Complete!';
    
    let details = `Successfully downloaded with subtitles`;
    if (data.subtitle_count) {
        details += ` (${data.subtitle_count} language${data.subtitle_count > 1 ? 's' : ''})`;
    }
    if (data.is_zip) {
        details += ` - ZIP file ready`;
    }
    resultDetails.textContent = details;
    
    // Use currentJobId which is already tracked
    downloadResultBtn.href = `/download/${currentJobId}`;
    downloadResultBtn.style.display = 'inline-flex';
    
    console.log('Download ready at:', downloadResultBtn.href);
}

// Show error section
function showError(message) {
    subtitleForm.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    
    errorMessage.textContent = message;
}

// Reset to initial state
function resetAll() {
    subtitleForm.style.display = 'block';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    videoUrl.value = '';
    currentJobId = null;
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
}

// Cancel download
cancelBtn.addEventListener('click', async () => {
    if (!currentJobId) return;
    
    if (!confirm('Are you sure you want to cancel this download?')) {
        return;
    }
    
    try {
        await fetch(`/cancel/${currentJobId}`, { method: 'POST' });
        clearInterval(checkInterval);
        showError('Download cancelled');
    } catch (error) {
        console.error('Cancel error:', error);
    }
});

// Retry button
retryBtn.addEventListener('click', resetAll);

// New download button
newDownloadBtn.addEventListener('click', resetAll);

