// QR Code Generator - JavaScript

let currentQRType = 'text';

// Tab Switching
document.querySelectorAll('.qr-type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const type = btn.getAttribute('data-type');
        switchQRType(type);
    });
});

function switchQRType(type) {
    currentQRType = type;
    
    // Update buttons
    document.querySelectorAll('.qr-type-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-type="${type}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.qr-type-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${type}-content`).classList.add('active');
    
    // Reset preview
    resetPreview();
}

// Form Submissions
document.getElementById('qr-text-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const text = document.getElementById('qr-text-input').value;
    const size = document.getElementById('qr-size').value;
    const errorCorrection = document.getElementById('qr-error-correction').value;
    generateQRCode('text', { text, size, error_correction: errorCorrection });
});

document.getElementById('qr-wifi-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const ssid = document.getElementById('wifi-ssid').value;
    const password = document.getElementById('wifi-password').value;
    const security = document.getElementById('wifi-security').value;
    const hidden = document.getElementById('wifi-hidden').value === 'true';
    generateQRCode('wifi', { ssid, password, security, hidden });
});

document.getElementById('qr-contact-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('contact-name').value;
    const phone = document.getElementById('contact-phone').value;
    const email = document.getElementById('contact-email').value;
    const url = document.getElementById('contact-url').value;
    const address = document.getElementById('contact-address').value;
    generateQRCode('contact', { name, phone, email, url, address });
});

document.getElementById('qr-email-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const to = document.getElementById('email-to').value;
    const subject = document.getElementById('email-subject').value;
    const body = document.getElementById('email-body').value;
    generateQRCode('email', { to, subject, body });
});

// Generate QR Code
async function generateQRCode(type, data) {
    const qrPreview = document.getElementById('qr-preview');
    
    try {
        // Show loading
        qrPreview.innerHTML = `
            <div class="qr-preview-placeholder">
                <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: #ff3333; margin-bottom: 20px;"></i>
                <p>Generating QR Code...</p>
            </div>
        `;
        
        const response = await fetch('/generate-qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, ...data })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Display QR code
            qrPreview.innerHTML = `
                <div class="qr-image-wrapper">
                    <img src="data:image/png;base64,${result.qr_code}" alt="QR Code" id="qr-image">
                </div>
                <button class="btn btn-success" onclick="downloadQRCode('${result.qr_code}')">
                    <i class="fas fa-download"></i> Download QR Code
                </button>
            `;
        } else {
            showError(result.error || 'Failed to generate QR code');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Download QR Code
function downloadQRCode(base64Data) {
    const link = document.createElement('a');
    link.href = 'data:image/png;base64,' + base64Data;
    link.download = `qrcode-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Reset Preview
function resetPreview() {
    const qrPreview = document.getElementById('qr-preview');
    qrPreview.innerHTML = `
        <div class="qr-preview-placeholder">
            <i class="fas fa-qrcode" style="font-size: 64px; color: #333; margin-bottom: 20px;"></i>
            <p>Your QR code will appear here</p>
            <p style="font-size: 12px; color: #555; margin-top: 10px;">Fill in the form above and click "Generate QR Code"</p>
        </div>
    `;
}

// Show Error
function showError(message) {
    const qrPreview = document.getElementById('qr-preview');
    qrPreview.innerHTML = `
        <div class="qr-preview-placeholder" style="color: #ff6666;">
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i>
            <p>${message}</p>
            <button class="btn btn-secondary" onclick="resetPreview()" style="margin-top: 20px;">
                <i class="fas fa-redo"></i> Try Again
            </button>
        </div>
    `;
}

