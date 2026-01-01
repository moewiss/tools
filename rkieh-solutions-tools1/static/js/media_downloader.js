// Media Downloader - JavaScript

let currentJobId = null;
let checkInterval = null;
let currentPlatform = 'youtube';

// DOM Elements
const platformTabs = document.querySelectorAll('.platform-tab');
const platformContents = document.querySelectorAll('.platform-content');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressMessage = document.getElementById('progress-message');
const progressTitle = document.getElementById('progress-title');
const resultMessage = document.getElementById('result-message');
const resultFilename = document.getElementById('result-filename');
const resultNote = document.getElementById('result-note');
const downloadResultBtn = document.getElementById('download-result-btn');
const newDownloadBtn = document.getElementById('new-download-btn');
const retryBtn = document.getElementById('retry-btn');
const cancelDownloadBtn = document.getElementById('cancel-download-btn');
const errorMessage = document.getElementById('error-message');

// Platform Tab Switching
platformTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const platform = tab.getAttribute('data-platform');
        switchPlatform(platform);
    });
});

function switchPlatform(platform) {
    currentPlatform = platform;
    
    // Update tabs
    platformTabs.forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-platform="${platform}"]`).classList.add('active');
    
    // Update content
    platformContents.forEach(c => c.classList.remove('active'));
    document.getElementById(`${platform}-content`).classList.add('active');
    
    // Reset forms
    resetAll();
}

// Form Submissions
document.getElementById('youtube-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('youtube-url').value;
    const format = document.getElementById('youtube-format').value;
    const quality = document.getElementById('youtube-quality').value;
    downloadFromPlatform('youtube', url, format, quality);
});

document.getElementById('instagram-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('instagram-url').value;
    const format = document.getElementById('instagram-format').value;
    downloadFromPlatform('instagram', url, format);
});

document.getElementById('facebook-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('facebook-url').value;
    const format = document.getElementById('facebook-format').value;
    downloadFromPlatform('facebook', url, format);
});

document.getElementById('tiktok-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const url = document.getElementById('tiktok-url').value;
    const format = document.getElementById('tiktok-format').value;
    downloadFromPlatform('tiktok', url, format);
});

// Download Function
async function downloadFromPlatform(platform, url, format, quality = 'best') {
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    try {
        showProgress(`Starting ${platform} download...`);
        
        const endpoint = `/download-${platform}`;
        const body = { url, format };
        if (platform === 'youtube' && quality) {
            body.quality = quality;
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            startProgressCheck();
        } else {
            showError(data.error || `Failed to start ${platform} download`);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Progress Checking
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
                    showError(data.message || 'Download failed');
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 1000);
}

function updateProgress(data) {
    const progress = data.progress || 0;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    progressMessage.textContent = data.message || 'Processing...';
    
    if (data.downloaded_mb && data.total_mb) {
        progressMessage.textContent = `${data.message || 'Downloading...'} (${data.downloaded_mb} MB / ${data.total_mb} MB)`;
    }
    
    // Show cancel button if download is in progress
    if (data.status === 'processing' && data.can_cancel) {
        cancelDownloadBtn.style.display = 'block';
    } else {
        cancelDownloadBtn.style.display = 'none';
    }
}

function showProgress(message) {
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    progressTitle.textContent = message;
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    progressMessage.textContent = 'Please wait...';
}

function showResult(data) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    errorSection.style.display = 'none';
    
    resultMessage.textContent = data.message || 'Your file is ready for download';
    resultFilename.textContent = data.output_filename || 'Downloaded file';
    
    if (data.is_zip) {
        resultNote.textContent = 'Multiple files packaged in ZIP archive';
    } else {
        resultNote.textContent = '';
    }
}

function showError(message) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
}

function resetAll() {
    currentJobId = null;
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
    
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Reset forms
    document.querySelectorAll('form').forEach(form => form.reset());
}

// Download Result Button
downloadResultBtn.addEventListener('click', () => {
    if (currentJobId) {
        window.location.href = `/download/${currentJobId}`;
    }
});

// New Download Button
newDownloadBtn.addEventListener('click', () => {
    resetAll();
});

// Retry Button
retryBtn.addEventListener('click', () => {
    resetAll();
});

// Cancel Download Button
cancelDownloadBtn.addEventListener('click', async () => {
    if (!currentJobId) return;
    
    if (confirm('Are you sure you want to cancel this download? Any partial downloads will be deleted.')) {
        try {
            const response = await fetch(`/cancel/${currentJobId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showError('Download cancelled by user');
                cancelDownloadBtn.style.display = 'none';
                resetAll();
            } else {
                alert('Failed to cancel: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error while cancelling: ' + error.message);
        }
    }
});

