// Media Tool Web Interface - JavaScript (Multi-file Support)

// Global variables
let currentJobId = null;
let selectedFiles = [];
let checkInterval = null;
let conversionType = 'mp4_to_mp3';

// DOM Elements
let convertForm, downloadForm, fileInput, folderInput, dropZone;
let selectedFilesDiv, filesList, fileCount, clearFilesBtn;
let convertBtn, convertBtnText, uploadText, fileInfo;
let progressSection, resultSection, errorSection;
let progressFill, progressText, progressMessage, progressTitle;
let resultMessage, resultFilename, resultNote, resultIcon, downloadBtnText;
let errorMessage, downloadResultBtn, newConversionBtn, retryBtn, cancelDownloadBtn;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[INIT] Starting initialization...');
    
    // Get all DOM elements
    convertForm = document.getElementById('convert-form');
    downloadForm = document.getElementById('download-form');
    fileInput = document.getElementById('file-input');
    folderInput = document.getElementById('folder-input');
    dropZone = document.getElementById('drop-zone');
    selectedFilesDiv = document.getElementById('selected-files');
    filesList = document.getElementById('files-list');
    fileCount = document.getElementById('file-count');
    clearFilesBtn = document.getElementById('clear-files');
    convertBtn = document.getElementById('convert-btn');
    convertBtnText = document.getElementById('convert-btn-text');
    uploadText = document.getElementById('upload-text');
    fileInfo = document.getElementById('file-info');
    
    progressSection = document.getElementById('progress-section');
    resultSection = document.getElementById('result-section');
    errorSection = document.getElementById('error-section');
    progressFill = document.getElementById('progress-fill');
    progressText = document.getElementById('progress-text');
    progressMessage = document.getElementById('progress-message');
    progressTitle = document.getElementById('progress-title');
    
    resultMessage = document.getElementById('result-message');
    resultFilename = document.getElementById('result-filename');
    resultNote = document.getElementById('result-note');
    resultIcon = document.getElementById('result-icon');
    downloadBtnText = document.getElementById('download-btn-text');
    errorMessage = document.getElementById('error-message');
    
    downloadResultBtn = document.getElementById('download-result-btn');
    newConversionBtn = document.getElementById('new-conversion-btn');
    retryBtn = document.getElementById('retry-btn');
    cancelDownloadBtn = document.getElementById('cancel-download-btn');
    
    console.log('[INIT] Elements loaded:', {
        fileInput: !!fileInput,
        folderInput: !!folderInput,
        convertBtn: !!convertBtn
    });
    
    // Setup event listeners
    setupEventListeners();
    
    console.log('[INIT] Initialization complete!');
});

function setupEventListeners() {
    console.log('[SETUP] Setting up event listeners...');
    
    // Conversion type buttons
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            conversionType = this.getAttribute('data-type');
            updateUIForConversionType();
        });
    });
    
    // File input
    fileInput.addEventListener('change', function(e) {
        console.log('[FILE INPUT] Changed, files:', e.target.files.length);
        handleFileSelection(Array.from(e.target.files));
    });
    
    // Folder input
    folderInput.addEventListener('change', function(e) {
        console.log('[FOLDER INPUT] Changed, files:', e.target.files.length);
        handleFileSelection(Array.from(e.target.files));
    });
    
    // Drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        console.log('[DROP] Files dropped:', e.dataTransfer.files.length);
        handleFileSelection(Array.from(e.dataTransfer.files));
    });
    
    // Clear files button
    clearFilesBtn.addEventListener('click', function() {
        console.log('[CLEAR] Clearing all files');
        clearSelectedFiles();
    });
    
    // Convert form
    convertForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('[CONVERT] Starting conversion...');
        
        if (selectedFiles.length === 0) {
            showError('Please select files to convert');
            return;
        }
        
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files[]', file);
        });
        
        const bitrate = document.getElementById('bitrate').value;
        formData.append('bitrate', bitrate);
        formData.append('conversion_type', conversionType);
        
        console.log('[CONVERT] FormData prepared:', {
            files: selectedFiles.length,
            bitrate: bitrate,
            conversion_type: conversionType
        });
        
        try {
            showProgress('Uploading files...');
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                currentJobId = data.job_id;
                console.log('[CONVERT] Job started:', currentJobId);
                startProgressCheck();
            } else {
                showError(data.error || 'Failed to start conversion');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        }
    });
    
    // Download button
    if (downloadResultBtn) {
        downloadResultBtn.addEventListener('click', function() {
            console.log('[DOWNLOAD] Downloading:', currentJobId);
            if (currentJobId) {
                window.location.href = '/download/' + currentJobId;
            }
        });
    }
    
    // New conversion button
    if (newConversionBtn) {
        newConversionBtn.addEventListener('click', function() {
            console.log('[NEW] Starting new conversion');
            resetAll();
        });
    }
    
    // Retry button
    if (retryBtn) {
        retryBtn.addEventListener('click', function() {
            console.log('[RETRY] Retrying');
            resetAll();
        });
    }
    
    console.log('[SETUP] Event listeners ready!');
}

function handleFileSelection(files) {
    console.log('[HANDLE] Processing', files.length, 'files');
    
    if (!files || files.length === 0) {
        return;
    }
    
    // Check file sizes
    const validFiles = Array.from(files).filter(file => {
        const maxSize = 500 * 1024 * 1024; // 500MB
        if (file.size > maxSize) {
            alert(`File "${file.name}" is too large (max 500MB)`);
            return false;
        }
        return true;
    });
    
    if (validFiles.length === 0) {
        return;
    }
    
    // Add to selected files
    validFiles.forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
            console.log('[HANDLE] Added:', file.name);
        }
    });
    
    console.log('[HANDLE] Total files:', selectedFiles.length);
    updateFilesList();
    updateConvertButton();
}

function updateFilesList() {
    console.log('[UPDATE LIST] Updating with', selectedFiles.length, 'files');
    
    if (selectedFiles.length === 0) {
        selectedFilesDiv.style.display = 'none';
        dropZone.style.display = 'block';
        return;
    }
    
    dropZone.style.display = 'none';
    selectedFilesDiv.style.display = 'block';
    fileCount.textContent = selectedFiles.length;
    
    filesList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-icon">
                <i class="fas ${getFileIcon(file)}"></i>
            </div>
            <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button type="button" class="file-remove" onclick="removeFileByIndex(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        filesList.appendChild(fileItem);
    });
    
    console.log('[UPDATE LIST] List updated!');
}

function removeFileByIndex(index) {
    console.log('[REMOVE] Removing file at index:', index);
    selectedFiles.splice(index, 1);
    updateFilesList();
    updateConvertButton();
}

function clearSelectedFiles() {
    selectedFiles = [];
    updateFilesList();
    updateConvertButton();
}

function updateConvertButton() {
    if (selectedFiles.length === 0) {
        convertBtn.disabled = true;
        convertBtnText.textContent = 'Select Files to Convert';
    } else {
        convertBtn.disabled = false;
        const outputFormat = conversionType === 'mp4_to_mp3' ? 'MP3' : 'MP4';
        convertBtnText.textContent = `Convert ${selectedFiles.length} File(s) to ${outputFormat}`;
    }
}

function updateUIForConversionType() {
    if (conversionType === 'mp4_to_mp3') {
        uploadText.textContent = 'Drag & Drop your video files here';
        fileInfo.textContent = 'Supports: MP4, MKV, AVI, MOV, WebM (Max 500MB per file)';
    } else {
        uploadText.textContent = 'Drag & Drop your audio files here';
        fileInfo.textContent = 'Supports: MP3, WAV, OGG, M4A (Max 500MB per file)';
    }
    updateConvertButton();
}

function getFileIcon(file) {
    if (file.type.startsWith('video/')) return 'fa-file-video';
    if (file.type.startsWith('audio/')) return 'fa-file-audio';
    return 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showProgress(message) {
    console.log('[PROGRESS] Showing:', message);
    convertForm.parentElement.parentElement.style.display = 'none';
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    progressMessage.textContent = message;
    progressTitle.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
}

function updateProgress(percent, message) {
    progressFill.style.width = percent + '%';
    progressText.textContent = percent + '%';
    if (message) {
        progressMessage.textContent = message;
    }
}

function showResult(filename, message, isZip) {
    console.log('[RESULT] Success:', filename);
    progressSection.style.display = 'none';
    errorSection.style.display = 'none';
    resultSection.style.display = 'block';
    
    resultFilename.textContent = filename;
    resultMessage.textContent = message || 'Your files are ready for download!';
    
    if (isZip) {
        resultIcon.className = 'fas fa-file-archive';
        resultNote.textContent = 'Multiple files have been packaged into a ZIP file';
        downloadBtnText.textContent = 'Download ZIP File';
    } else {
        resultIcon.className = 'fas fa-file-audio';
        resultNote.textContent = '';
        downloadBtnText.textContent = 'Download File';
    }
}

function showError(message) {
    console.error('[ERROR]', message);
    convertForm.parentElement.parentElement.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    
    errorMessage.textContent = message;
    
    if (checkInterval) {
        clearInterval(checkInterval);
    }
}

function resetAll() {
    console.log('[RESET] Resetting all');
    currentJobId = null;
    clearSelectedFiles();
    
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
    
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    convertForm.parentElement.parentElement.style.display = 'block';
}

function startProgressCheck() {
    console.log('[PROGRESS CHECK] Starting for job:', currentJobId);
    
    checkInterval = setInterval(async () => {
        try {
            const response = await fetch('/status/' + currentJobId);
            const data = await response.json();
            
            if (data.status === 'processing') {
                updateProgress(data.progress || 0, data.message || 'Processing...');
            } else if (data.status === 'completed') {
                clearInterval(checkInterval);
                updateProgress(100, 'Complete!');
                setTimeout(() => {
                    showResult(data.filename, data.message, data.is_zip);
                }, 500);
            } else if (data.status === 'failed') {
                clearInterval(checkInterval);
                showError(data.error || 'Conversion failed');
            }
        } catch (error) {
            console.error('[PROGRESS CHECK] Error:', error);
        }
    }, 500);
}

console.log('[SCRIPT] main.js loaded');
