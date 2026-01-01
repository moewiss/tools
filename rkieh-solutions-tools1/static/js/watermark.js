// Watermark Removal Tool - JavaScript

// Global variables
let originalImage = null;
let imageCanvas = null;
let maskCanvas = null;
let imageCtx = null;
let maskCtx = null;
let isDrawing = false;
let brushEnabled = true;
let brushSize = 25;
let resultImage = null;

// DOM Elements
const imageInput = document.getElementById('image-input');
const uploadZone = document.getElementById('upload-zone');
const uploadSection = document.getElementById('upload-section');
const canvasSection = document.getElementById('canvas-section');
const settingsSection = document.getElementById('settings-section');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const brushToggle = document.getElementById('brush-toggle');
const brushStatus = document.getElementById('brush-status');
const clearSelectionBtn = document.getElementById('clear-selection');
const brushSizeInput = document.getElementById('brush-size');
const brushSizeValue = document.getElementById('brush-size-value');
const removeBtn = document.getElementById('remove-btn');
const inpaintMethod = document.getElementById('inpaint-method');
const downloadBtn = document.getElementById('download-btn');
const newImageBtn = document.getElementById('new-image-btn');
const originalPreview = document.getElementById('original-preview');
const resultPreview = document.getElementById('result-preview');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    imageCanvas = document.getElementById('image-canvas');
    maskCanvas = document.getElementById('mask-canvas');
    imageCtx = imageCanvas.getContext('2d');
    maskCtx = maskCanvas.getContext('2d');
    
    setupEventListeners();
});

function setupEventListeners() {
    // File input
    imageInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            loadImage(file);
        }
    });
    
    // Canvas drawing - make sure events work
    maskCanvas.addEventListener('mousedown', startDrawing, false);
    maskCanvas.addEventListener('mousemove', draw, false);
    maskCanvas.addEventListener('mouseup', stopDrawing, false);
    maskCanvas.addEventListener('mouseleave', stopDrawing, false);
    
    // Also add to document for better tracking
    document.addEventListener('mouseup', stopDrawing, false);
    
    // Touch support
    maskCanvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        maskCanvas.dispatchEvent(mouseEvent);
    });
    
    maskCanvas.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        maskCanvas.dispatchEvent(mouseEvent);
    });
    
    maskCanvas.addEventListener('touchend', (e) => {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        maskCanvas.dispatchEvent(mouseEvent);
    });
    
    // Brush toggle
    brushToggle.addEventListener('click', () => {
        brushEnabled = !brushEnabled;
        brushToggle.classList.toggle('active');
        if (brushEnabled) {
            brushStatus.textContent = 'Brush: ON';
            maskCanvas.style.cursor = 'crosshair';
        } else {
            brushStatus.textContent = 'Brush: OFF';
            maskCanvas.style.cursor = 'default';
        }
    });
    
    // Controls
    clearSelectionBtn.addEventListener('click', clearMask);
    brushSizeInput.addEventListener('input', (e) => {
        brushSize = parseInt(e.target.value);
        brushSizeValue.textContent = `${brushSize}px`;
    });
    
    // Process button
    removeBtn.addEventListener('click', processImage);
    
    // Result buttons
    downloadBtn.addEventListener('click', downloadResult);
    newImageBtn.addEventListener('click', resetTool);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        loadImage(file);
    }
}

function loadImage(file) {
    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size exceeds 10MB limit. Please choose a smaller image.');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            originalImage = img;
            setupCanvases(img);
            showSection('canvas');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function setupCanvases(img) {
    // Store original image
    originalImage = img;
    
    // Use original image size for better quality
    let width = img.width;
    let height = img.height;
    
    // Scale down only if extremely large
    const maxWidth = 1800;
    
    if (width > maxWidth) {
        const ratio = maxWidth / width;
        width = Math.floor(maxWidth);
        height = Math.floor(height * ratio);
    }
    
    // Set canvas sizes - both must be exactly the same
    imageCanvas.width = width;
    imageCanvas.height = height;
    maskCanvas.width = width;
    maskCanvas.height = height;
    
    // Draw original image with high quality
    imageCtx.imageSmoothingEnabled = true;
    imageCtx.imageSmoothingQuality = 'high';
    imageCtx.drawImage(img, 0, 0, width, height);
    
    // Set mask canvas CSS size to match image canvas
    maskCanvas.style.width = width + 'px';
    maskCanvas.style.height = height + 'px';
    
    // Clear mask
    clearMask();
    
    console.log('Canvas setup:', {
        width: width,
        height: height,
        imageCanvasSize: `${imageCanvas.width}x${imageCanvas.height}`,
        maskCanvasSize: `${maskCanvas.width}x${maskCanvas.height}`
    });
}

function startDrawing(e) {
    if (!brushEnabled) return;
    e.preventDefault();
    isDrawing = true;
    console.log('Start drawing');
    draw(e);
}

function draw(e) {
    if (!isDrawing || !brushEnabled) return;
    
    // Get accurate mouse position relative to canvas
    const rect = maskCanvas.getBoundingClientRect();
    const scaleX = maskCanvas.width / rect.width;
    const scaleY = maskCanvas.height / rect.height;
    
    const canvasX = (e.clientX - rect.left) * scaleX;
    const canvasY = (e.clientY - rect.top) * scaleY;
    
    console.log('Drawing at:', canvasX, canvasY);
    
    // Draw on mask canvas
    maskCtx.globalCompositeOperation = 'source-over';
    maskCtx.fillStyle = 'rgba(255, 0, 0, 0.7)';
    maskCtx.beginPath();
    maskCtx.arc(canvasX, canvasY, brushSize / 2, 0, Math.PI * 2);
    maskCtx.fill();
    
    // Update cursor
    maskCanvas.style.cursor = 'crosshair';
}

function stopDrawing(e) {
    if (e) e.preventDefault();
    isDrawing = false;
    console.log('Stop drawing');
}

function clearMask() {
    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
}

function showSection(section) {
    uploadSection.style.display = 'none';
    canvasSection.style.display = 'none';
    settingsSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    
    switch(section) {
        case 'canvas':
            canvasSection.style.display = 'block';
            settingsSection.style.display = 'block';
            // Make sure canvas is interactive
            setTimeout(() => {
                maskCanvas.style.pointerEvents = 'auto';
                console.log('Canvas ready for drawing');
            }, 100);
            break;
        case 'progress':
            progressSection.style.display = 'block';
            break;
        case 'result':
            resultSection.style.display = 'block';
            break;
    }
}

async function processImage() {
    // Check if mask is empty
    const maskData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
    const hasSelection = maskData.data.some(value => value > 0);
    
    if (!hasSelection) {
        alert('Please select watermark areas by drawing on the image.');
        return;
    }
    
    showSection('progress');
    
    try {
        // Get image as high-quality PNG
        const imageDataURL = imageCanvas.toDataURL('image/png', 1.0);
        
        // Create pure white/black mask with dilation for better coverage
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = maskCanvas.width;
        tempCanvas.height = maskCanvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Convert red overlay to white mask on black background
        tempCtx.drawImage(maskCanvas, 0, 0);
        const maskImageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        
        // Create clean binary mask (no dilation in JS, let OpenCV handle it)
        for (let i = 0; i < maskImageData.data.length; i += 4) {
            if (maskImageData.data[i + 3] > 0) {
                // White for watermark area
                maskImageData.data[i] = 255;
                maskImageData.data[i + 1] = 255;
                maskImageData.data[i + 2] = 255;
                maskImageData.data[i + 3] = 255;
            } else {
                // Black for background to keep
                maskImageData.data[i] = 0;
                maskImageData.data[i + 1] = 0;
                maskImageData.data[i + 2] = 0;
                maskImageData.data[i + 3] = 255;
            }
        }
        
        tempCtx.putImageData(maskImageData, 0, 0);
        const maskDataURL = tempCanvas.toDataURL('image/png', 1.0);
        
        // Send to server
        console.log('Sending watermark removal request...');
        const response = await fetch('/watermark/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageDataURL,
                mask: maskDataURL,
                method: inpaintMethod.value
            })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error:', errorText);
            throw new Error(`Server error (${response.status}): ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data.success ? 'Success' : 'Failed');
        
        if (data.success) {
            resultImage = data.result;
            showResult();
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    } catch (error) {
        console.error('Error processing image:', error);
        
        // Provide detailed error message
        let errorMessage = 'Error processing image: ' + error.message;
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage += '\n\nPossible solutions:\n' +
                '✓ Check if the server is running\n' +
                '✓ Ensure you\'re accessing the correct URL\n' +
                '✓ Check browser console for CORS errors\n' +
                '✓ Try refreshing the page';
        } else if (error.message.includes('OpenCV')) {
            errorMessage += '\n\nOpenCV is required but not installed.\n' +
                'Install with: pip install opencv-python';
        }
        
        alert(errorMessage);
        showSection('canvas');
    }
}

function showResult() {
    originalPreview.src = imageCanvas.toDataURL('image/png');
    resultPreview.src = resultImage;
    showSection('result');
}

function downloadResult() {
    const link = document.createElement('a');
    link.download = 'cleaned_image.png';
    link.href = resultImage;
    link.click();
}

function resetTool() {
    originalImage = null;
    resultImage = null;
    clearMask();
    imageInput.value = '';
    uploadSection.style.display = 'block';
    canvasSection.style.display = 'none';
    settingsSection.style.display = 'none';
    resultSection.style.display = 'none';
}

console.log('Watermark Removal Tool Loaded');

