// File Encryptor - JavaScript

let currentMode = 'encrypt';
let selectedFile = null;
let processedFileUrl = null;

// Mode selector
const modeButtons = document.querySelectorAll('.mode-btn');
const sectionTitle = document.getElementById('section-title');
const processBtn = document.getElementById('process-btn');
const fileUploadArea = document.getElementById('file-upload-area');
const fileInput = document.getElementById('file-input');
const selectedFileDiv = document.getElementById('selected-file');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file-btn');
const passwordInput = document.getElementById('password-input');
const passwordToggle = document.getElementById('password-toggle');
const passwordStrength = document.getElementById('password-strength');
const infoTitle = document.getElementById('info-title');
const infoText = document.getElementById('info-text');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');
const downloadBtn = document.getElementById('download-btn');
const resetBtn = document.getElementById('reset-btn');

// Mode switching
modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        switchMode(mode);
    });
});

function switchMode(mode) {
    currentMode = mode;
    
    // Update active button
    modeButtons.forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
    
    // Update UI text
    if (mode === 'encrypt') {
        sectionTitle.innerHTML = '<i class="fas fa-lock"></i> Encrypt File';
        processBtn.innerHTML = '<i class="fas fa-lock"></i> Encrypt File';
        infoTitle.textContent = 'About Encryption';
        infoText.innerHTML = `
            <p><strong>Military-Grade AES-256 Encryption:</strong> Your files are encrypted using industry-standard AES-256 encryption with enhanced security features.</p>
            <ul>
                <li><strong>Random Salt:</strong> Each file uses a unique random salt for maximum security</li>
                <li><strong>HMAC Verification:</strong> Built-in integrity checking prevents tampering</li>
                <li><strong>High Iterations:</strong> 600,000 PBKDF2 iterations (OWASP recommended) for key derivation</li>
                <li><strong>Secure:</strong> Your password is never stored or transmitted in plain text</li>
                <li><strong>Private:</strong> Files are processed securely and deleted after processing</li>
                <li><strong>Compatible:</strong> Encrypted files can be decrypted on any device with this tool</li>
                <li><strong>Important:</strong> Remember your password! Without it, your files cannot be recovered</li>
            </ul>
        `;
        document.getElementById('download-action').textContent = 'Encrypted';
    } else {
        sectionTitle.innerHTML = '<i class="fas fa-unlock"></i> Decrypt File';
        processBtn.innerHTML = '<i class="fas fa-unlock"></i> Decrypt File';
        infoTitle.textContent = 'About Decryption';
        infoText.innerHTML = `
            <p><strong>Secure Decryption:</strong> Decrypt files that were encrypted with this tool using the same password.</p>
            <ul>
                <li><strong>Password Required:</strong> You must enter the exact password used during encryption</li>
                <li><strong>Integrity Check:</strong> HMAC verification ensures the file hasn't been tampered with</li>
                <li><strong>File Format:</strong> Files encrypted with this tool typically have a <code>.encrypted</code> extension, but you can decrypt any file</li>
                <li><strong>Backward Compatible:</strong> Can decrypt files encrypted with older versions of this tool</li>
                <li><strong>Security:</strong> If the password is incorrect or the file wasn't encrypted with this tool, decryption will fail</li>
                <li><strong>Original File:</strong> The decrypted file will have the original filename and format</li>
            </ul>
        `;
        document.getElementById('download-action').textContent = 'Decrypted';
    }
    
    // Reset form
    resetForm();
}

// File upload handling
fileUploadArea.addEventListener('click', () => fileInput.click());
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});
fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});
fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    selectedFileDiv.style.display = 'flex';
    checkFormValidity();
}

removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    selectedFileDiv.style.display = 'none';
    checkFormValidity();
});

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Password visibility toggle
passwordToggle.addEventListener('click', () => {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    passwordToggle.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
});

// Password strength checker
passwordInput.addEventListener('input', () => {
    checkPasswordStrength();
    checkFormValidity();
});

function checkPasswordStrength() {
    const password = passwordInput.value;
    if (!password) {
        passwordStrength.textContent = '';
        passwordStrength.className = 'password-strength';
        return;
    }
    
    let strength = 0;
    let feedback = [];
    
    if (password.length >= 8) strength++;
    else feedback.push('At least 8 characters');
    
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    if (strength <= 2) {
        passwordStrength.textContent = 'Weak password' + (feedback.length ? ` - ${feedback[0]}` : '');
        passwordStrength.className = 'password-strength weak';
    } else if (strength <= 4) {
        passwordStrength.textContent = 'Medium password';
        passwordStrength.className = 'password-strength medium';
    } else {
        passwordStrength.textContent = 'Strong password';
        passwordStrength.className = 'password-strength strong';
    }
}

function checkFormValidity() {
    const isValid = selectedFile && passwordInput.value.length >= 4;
    processBtn.disabled = !isValid;
}

// Process file (encrypt/decrypt)
processBtn.addEventListener('click', async () => {
    if (!selectedFile || !passwordInput.value) {
        showError('Please select a file and enter a password');
        return;
    }
    
    if (passwordInput.value.length < 4) {
        showError('Password must be at least 4 characters long');
        return;
    }
    
    try {
        processBtn.disabled = true;
        processBtn.innerHTML = currentMode === 'encrypt' 
            ? '<i class="fas fa-spinner fa-spin"></i> Encrypting...'
            : '<i class="fas fa-spinner fa-spin"></i> Decrypting...';
        
        errorSection.style.display = 'none';
        resultSection.classList.remove('show');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('password', passwordInput.value);
        formData.append('mode', currentMode);
        
        const response = await fetch(currentMode === 'encrypt' ? '/encrypt-file' : '/decrypt-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            processedFileUrl = data.download_url;
            document.getElementById('result-file-name').textContent = data.filename;
            document.getElementById('result-file-size').textContent = formatFileSize(data.file_size || 0);
            document.getElementById('result-message').textContent = 
                currentMode === 'encrypt' ? 'File encrypted successfully!' : 'File decrypted successfully!';
            resultSection.classList.add('show');
        } else {
            showError(data.error || 'Processing failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        processBtn.disabled = false;
        processBtn.innerHTML = currentMode === 'encrypt' 
            ? '<i class="fas fa-lock"></i> Encrypt File'
            : '<i class="fas fa-unlock"></i> Decrypt File';
    }
});

// Download processed file
downloadBtn.addEventListener('click', () => {
    if (processedFileUrl) {
        window.location.href = processedFileUrl;
    }
});

// Reset form
resetBtn.addEventListener('click', resetForm);

function resetForm() {
    selectedFile = null;
    fileInput.value = '';
    selectedFileDiv.style.display = 'none';
    passwordInput.value = '';
    passwordInput.type = 'password';
    passwordToggle.innerHTML = '<i class="fas fa-eye"></i>';
    passwordStrength.textContent = '';
    passwordStrength.className = 'password-strength';
    processedFileUrl = null;
    resultSection.classList.remove('show');
    errorSection.style.display = 'none';
    checkFormValidity();
}

function showError(message) {
    errorSection.style.display = 'block';
    document.getElementById('error-message').textContent = message;
    resultSection.classList.remove('show');
}

// Initialize
checkFormValidity();

