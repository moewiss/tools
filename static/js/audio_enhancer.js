/**
 * Audio Enhancer - Clean Voice & Reduce Noise
 * Frontend JavaScript for audio enhancement functionality
 */

let selectedFile = null;
let currentJobId = null;
let statusCheckInterval = null;

// DOM Elements
const audioFile = document.getElementById('audioFile');
const fileInfo = document.getElementById('fileInfo');
const enhanceBtn = document.getElementById('enhanceBtn');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressMessage = document.getElementById('progressMessage');
const resultSection = document.getElementById('resultSection');
const audioPlayer = document.getElementById('audioPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const enhanceAnotherBtn = document.getElementById('enhanceAnotherBtn');
const errorMessage = document.getElementById('errorMessage');

// Enhancement options
const noiseReduction = document.getElementById('noiseReduction');
const enhanceVoice = document.getElementById('enhanceVoice');
const normalizeAudio = document.getElementById('normalizeAudio');
const removeSilence = document.getElementById('removeSilence');

// File selection handler
audioFile.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        fileInfo.innerHTML = `
            ✅ Selected: <strong>${file.name}</strong> (${sizeMB} MB)
        `;
        fileInfo.style.color = '#4caf50';
        enhanceBtn.disabled = false;
        hideError();
    }
});

// Enhance button handler
enhanceBtn.addEventListener('click', async function() {
    if (!selectedFile) {
        showError('Please select an audio file first');
        return;
    }

    // Validate file size (max 100MB)
    if (selectedFile.size > 100 * 1024 * 1024) {
        showError('File size too large. Maximum size is 100MB');
        return;
    }

    // Disable button and show progress
    enhanceBtn.disabled = true;
    progressSection.classList.add('active');
    resultSection.classList.remove('active');
    hideError();

    // Prepare form data
    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('noise_reduction', noiseReduction.value);
    formData.append('enhance_voice', enhanceVoice.checked ? 'true' : 'false');
    formData.append('normalize_audio', normalizeAudio.checked ? 'true' : 'false');
    formData.append('remove_silence', removeSilence.checked ? 'true' : 'false');

    try {
        // Upload and start enhancement
        const response = await fetch('/api/enhance-audio', {
            method: 'POST',
            body: formData
        });

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            showError('Server returned invalid response. Please check server logs.');
            enhanceBtn.disabled = false;
            progressSection.classList.remove('active');
            return;
        }

        if (data.success) {
            currentJobId = data.job_id;
            startStatusCheck();
        } else {
            showError(data.error || 'Failed to start enhancement');
            enhanceBtn.disabled = false;
            progressSection.classList.remove('active');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
        enhanceBtn.disabled = false;
        progressSection.classList.remove('active');
    }
});

// Start checking job status
function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    // Check immediately first
    checkStatus();
    // Then check every 1 second (reduced from 500ms for better performance)
    statusCheckInterval = setInterval(checkStatus, 1000);
}

// Check job status
async function checkStatus() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/status/${currentJobId}`);
        const data = await response.json();

        // Update progress
        progressBar.style.width = data.progress + '%';
        progressBar.textContent = data.progress + '%';
        progressMessage.textContent = data.message || 'Processing...';

        // Check if completed
        if (data.status === 'completed') {
            clearInterval(statusCheckInterval);
            showResult(data);
        } else if (data.status === 'failed') {
            clearInterval(statusCheckInterval);
            showError(data.message || 'Enhancement failed');
            progressSection.classList.remove('active');
            enhanceBtn.disabled = false;
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

// Show result
function showResult(data) {
    progressSection.classList.remove('active');
    resultSection.classList.add('active');

    // Set audio player source
    const audioUrl = `/download/${currentJobId}`;
    audioPlayer.src = audioUrl;

    // Set download button
    downloadBtn.href = audioUrl;
    downloadBtn.download = data.output_filename;

    // Show file size
    const sizeMB = (data.file_size / (1024 * 1024)).toFixed(2);
    resultSection.querySelector('p').innerHTML = `
        Your audio has been cleaned and enhanced<br>
        <small style="color: #999;">File size: ${sizeMB} MB</small>
    `;
}

// Enhance another audio
enhanceAnotherBtn.addEventListener('click', function() {
    // Reset everything
    selectedFile = null;
    currentJobId = null;
    audioFile.value = '';
    fileInfo.innerHTML = 'Supported formats: MP3, WAV, M4A, OGG, WhatsApp Audio';
    fileInfo.style.color = 'white';
    enhanceBtn.disabled = true;
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    progressMessage.textContent = 'Starting...';
    resultSection.classList.remove('active');
    progressSection.classList.remove('active');
    hideError();

    // Reset options to defaults
    noiseReduction.value = 'medium';
    enhanceVoice.checked = true;
    normalizeAudio.checked = true;
    removeSilence.checked = false;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Show error message
function showError(message) {
    errorMessage.textContent = '❌ ' + message;
    errorMessage.classList.add('active');
}

// Hide error message
function hideError() {
    errorMessage.classList.remove('active');
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
});

console.log('🎙️ Audio Enhancer initialized');

