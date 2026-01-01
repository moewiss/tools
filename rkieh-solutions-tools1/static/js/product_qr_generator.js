// Product QR Generator - JavaScript

const generateBtn = document.getElementById('generate-product-qr-btn');
const downloadBtn = document.getElementById('download-product-qr-btn');
const previewSection = document.getElementById('qr-preview-section');
const errorSection = document.getElementById('error-section');
const qrPreviewContainer = document.getElementById('qr-preview-container');

let currentQRImage = null;

// Generate Product QR Code
generateBtn.addEventListener('click', async () => {
    const productName = document.getElementById('product-name').value.trim();
    const productSku = document.getElementById('product-sku').value.trim();
    
    if (!productName || !productSku) {
        showError('Product Name and SKU are required');
        return;
    }
    
    const productData = {
        type: 'product',
        name: productName,
        sku: productSku,
        price: document.getElementById('product-price').value || '',
        currency: document.getElementById('product-currency').value,
        manufacturer: document.getElementById('product-manufacturer').value.trim(),
        category: document.getElementById('product-category').value.trim(),
        description: document.getElementById('product-description').value.trim(),
        website: document.getElementById('product-website').value.trim(),
        image_url: document.getElementById('product-image-url').value.trim(),
        size: parseInt(document.getElementById('qr-size').value),
        error_correction: document.getElementById('qr-error-correction').value
    };
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        const response = await fetch('/generate-product-qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayQRCode(data.qr_code);
            currentQRImage = data.qr_code;
        } else {
            showError(data.error || 'Failed to generate QR code');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Product QR Code';
    }
});

function displayQRCode(qrCodeData) {
    errorSection.style.display = 'none';
    previewSection.style.display = 'block';
    
    qrPreviewContainer.innerHTML = `
        <div class="qr-image-wrapper">
            <img src="${qrCodeData}" alt="Product QR Code">
        </div>
    `;
}

function showError(message) {
    previewSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

function resetForm() {
    errorSection.style.display = 'none';
}

// Download QR Code
downloadBtn.addEventListener('click', () => {
    if (currentQRImage) {
        const link = document.createElement('a');
        link.href = currentQRImage;
        link.download = `product-qr-${document.getElementById('product-sku').value || 'code'}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

