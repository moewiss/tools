// Duplicate File Finder - JavaScript

let currentJobId = null;
let checkInterval = null;
let selectedFiles = new Set();
let duplicateGroups = [];

// DOM Elements
const folderInput = document.getElementById('folder-input');
const scanDropZone = document.getElementById('scan-drop-zone');
const selectedFolder = document.getElementById('selected-folder');
const folderName = document.getElementById('folder-name');
const folderItemCount = document.getElementById('folder-item-count');
const startScanBtn = document.getElementById('start-scan-btn');
const progressSection = document.getElementById('progress-section');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');

let selectedFolderPath = null;
let selectedFolderFiles = [];

// Folder selection
folderInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFolderSelection(e.target.files);
    }
});

scanDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    scanDropZone.style.borderColor = '#ff3333';
});

scanDropZone.addEventListener('dragleave', () => {
    scanDropZone.style.borderColor = '#333';
});

scanDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    scanDropZone.style.borderColor = '#333';
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
        handleFolderSelection(files);
    }
});

function handleFolderSelection(files) {
    selectedFolderFiles = Array.from(files);
    const folderPath = files[0].webkitRelativePath ? files[0].webkitRelativePath.split('/')[0] : 'Selected Files';
    folderName.textContent = folderPath;
    folderItemCount.textContent = `${selectedFolderFiles.length} files selected`;
    selectedFolder.style.display = 'block';
    startScanBtn.disabled = false;
}

function removeFolder() {
    selectedFolderFiles = [];
    folderInput.value = '';
    selectedFolder.style.display = 'none';
    startScanBtn.disabled = true;
}

// Start scan
startScanBtn.addEventListener('click', async () => {
    if (selectedFolderFiles.length === 0) {
        showError('Please select a folder to scan');
        return;
    }
    
    const formData = new FormData();
    selectedFolderFiles.forEach(file => {
        formData.append('files[]', file);
    });
    formData.append('scan_method', document.getElementById('scan-method').value);
    formData.append('min_file_size', document.getElementById('min-file-size').value || '0');
    formData.append('file_types', document.getElementById('file-types').value || '');
    formData.append('include_subfolders', document.getElementById('include-subfolders').checked);
    
    try {
        showProgress('Starting scan...');
        
        const response = await fetch('/find-duplicates', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            startProgressCheck();
        } else {
            showError(data.error || 'Failed to start scan');
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
                    
                    // Check if this is a clean folder creation job
                    if (data.type === 'clean_folder') {
                        // Show download link
                        const downloadUrl = `/download/${currentJobId}`;
                        const message = `${data.message}\n\nClick OK to download the clean folder.`;
                        alert(message);
                        window.location.href = downloadUrl;
                    } else {
                        // Regular duplicate scan
                        showResults(data);
                    }
                } else if (data.status === 'failed') {
                    clearInterval(checkInterval);
                    showError(data.message || 'Operation failed');
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
    document.getElementById('progress-message').textContent = data.message || 'Scanning...';
}

function showProgress(message) {
    progressSection.style.display = 'block';
    resultsSection.classList.remove('active');
    errorSection.style.display = 'none';
    document.getElementById('progress-title').textContent = message;
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
}

function showResults(data) {
    progressSection.style.display = 'none';
    errorSection.style.display = 'none';
    resultsSection.classList.add('active');
    
    duplicateGroups = data.duplicate_groups || [];
    
    // Store job_id and unique_files for clean folder creation
    window.currentScanJobId = currentJobId;  // Use the current job ID
    window.uniqueFilesCount = data.unique_files ? data.unique_files.length : 0;
    
    // Update stats
    const totalDuplicates = duplicateGroups.reduce((sum, group) => sum + group.files.length - 1, 0);
    const wastedSpace = duplicateGroups.reduce((sum, group) => sum + (group.size * (group.files.length - 1)), 0);
    
    document.getElementById('duplicate-groups-count').textContent = duplicateGroups.length;
    document.getElementById('duplicate-files-count').textContent = totalDuplicates;
    document.getElementById('wasted-space').textContent = `${(wastedSpace / (1024 * 1024)).toFixed(2)} MB`;
    
    // Show create clean folder button if we have unique files
    const cleanFolderSection = document.getElementById('create-clean-folder-section');
    if (window.uniqueFilesCount > 0) {
        cleanFolderSection.style.display = 'block';
    } else {
        cleanFolderSection.style.display = 'none';
    }
    
    // Display duplicate groups
    displayDuplicateGroups();
}

function displayDuplicateGroups() {
    const container = document.getElementById('duplicate-groups-container');
    
    if (duplicateGroups.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #888;">
                <i class="fas fa-check-circle" style="font-size: 48px; color: #10b981; margin-bottom: 20px;"></i>
                <p style="font-size: 18px; color: #fff;">No duplicate files found!</p>
                <p style="font-size: 14px; margin-top: 10px;">Your files are all unique.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = duplicateGroups.map((group, groupIndex) => `
        <div class="duplicate-group">
            <div class="duplicate-group-header">
                <div class="duplicate-group-info">
                    <div class="duplicate-group-title">
                        ${group.files.length} duplicate files (${(group.size / (1024 * 1024)).toFixed(2)} MB each)
                    </div>
                    <div class="duplicate-group-meta">
                        Total wasted space: ${((group.size * (group.files.length - 1)) / (1024 * 1024)).toFixed(2)} MB
                    </div>
                </div>
                <div class="duplicate-group-actions">
                    <button type="button" class="btn btn-secondary" onclick="selectAllInGroup(${groupIndex})">
                        <i class="fas fa-check-square"></i> Select All
                    </button>
                </div>
            </div>
            ${group.files.map((file, fileIndex) => `
                <div class="file-item">
                    <div class="file-item-info">
                        <i class="fas fa-file file-item-icon"></i>
                        <div class="file-item-details">
                            <div class="file-item-name">${file.name}</div>
                            <div class="file-item-path">${file.path}</div>
                        </div>
                        <div class="file-item-size">${(file.size / (1024 * 1024)).toFixed(2)} MB</div>
                    </div>
                    <div class="file-item-actions">
                        <button type="button" class="btn-select ${selectedFiles.has(`${groupIndex}-${fileIndex}`) ? 'selected' : ''}" 
                                onclick="toggleFileSelection(${groupIndex}, ${fileIndex})">
                            <i class="fas fa-${selectedFiles.has(`${groupIndex}-${fileIndex}`) ? 'check' : 'plus'}"></i>
                            ${selectedFiles.has(`${groupIndex}-${fileIndex}`) ? 'Selected' : 'Select'}
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `).join('');
    
    updateBulkActions();
}

function toggleFileSelection(groupIndex, fileIndex) {
    const key = `${groupIndex}-${fileIndex}`;
    if (selectedFiles.has(key)) {
        selectedFiles.delete(key);
    } else {
        selectedFiles.add(key);
    }
    displayDuplicateGroups();
}

function selectAllInGroup(groupIndex) {
    const group = duplicateGroups[groupIndex];
    group.files.forEach((file, fileIndex) => {
        selectedFiles.add(`${groupIndex}-${fileIndex}`);
    });
    displayDuplicateGroups();
}

function clearSelection() {
    selectedFiles.clear();
    displayDuplicateGroups();
}

function updateBulkActions() {
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (selectedFiles.size > 0) {
        bulkActions.classList.add('active');
        selectedCount.textContent = selectedFiles.size;
    } else {
        bulkActions.classList.remove('active');
    }
}

async function deleteSelected() {
    if (selectedFiles.size === 0) {
        alert('Please select files to delete');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${selectedFiles.size} file(s)? This action cannot be undone.`)) {
        return;
    }
    
    const filesToDelete = Array.from(selectedFiles).map(key => {
        const [groupIndex, fileIndex] = key.split('-').map(Number);
        return duplicateGroups[groupIndex].files[fileIndex];
    });
    
    try {
        showProgress('Deleting files...');
        
        const response = await fetch('/delete-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files: filesToDelete })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove deleted files from display
            selectedFiles.forEach(key => {
                const [groupIndex, fileIndex] = key.split('-').map(Number);
                duplicateGroups[groupIndex].files.splice(fileIndex, 1);
            });
            
            // Remove empty groups
            duplicateGroups = duplicateGroups.filter(group => group.files.length > 1);
            
            selectedFiles.clear();
            showResults({ duplicate_groups: duplicateGroups });
            alert(`Successfully deleted ${filesToDelete.length} file(s)`);
        } else {
            showError(data.error || 'Failed to delete files');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function showError(message) {
    progressSection.style.display = 'none';
    resultsSection.classList.remove('active');
    errorSection.style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

// Retry button
document.getElementById('retry-btn').addEventListener('click', () => {
    errorSection.style.display = 'none';
    removeFolder();
});

// ========== Excel/CSV Duplicate Detection ==========

let currentExcelJobId = null;
let excelCheckInterval = null;
let excelColumns = [];
let excelFile = null;

// Tab switching
function switchTab(tab) {
    const fileTab = document.getElementById('file-duplicates-tab');
    const excelTab = document.getElementById('excel-duplicates-tab');
    const fileSection = document.getElementById('file-duplicates-section');
    const excelSection = document.getElementById('excel-duplicates-section');
    
    if (tab === 'files') {
        fileTab.classList.add('active');
        fileTab.style.background = '#2a2a2a';
        fileTab.style.color = '#fff';
        excelTab.classList.remove('active');
        excelTab.style.background = '#1a1a1a';
        excelTab.style.color = '#888';
        fileSection.style.display = 'block';
        excelSection.style.display = 'none';
    } else {
        excelTab.classList.add('active');
        excelTab.style.background = '#2a2a2a';
        excelTab.style.color = '#fff';
        fileTab.classList.remove('active');
        fileTab.style.background = '#1a1a1a';
        fileTab.style.color = '#888';
        fileSection.style.display = 'none';
        excelSection.style.display = 'block';
    }
}

// Excel file selection
const excelInput = document.getElementById('excel-input');
const excelDropZone = document.getElementById('excel-drop-zone');
const selectedExcelFile = document.getElementById('selected-excel-file');
const excelFileName = document.getElementById('excel-file-name');
const excelFileInfo = document.getElementById('excel-file-info');
const columnSelection = document.getElementById('column-selection');
const scanExcelBtn = document.getElementById('scan-excel-btn');

excelInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleExcelFile(e.target.files[0]);
    }
});

excelDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    excelDropZone.style.borderColor = '#ff3333';
});

excelDropZone.addEventListener('dragleave', () => {
    excelDropZone.style.borderColor = '#333';
});

excelDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    excelDropZone.style.borderColor = '#333';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleExcelFile(files[0]);
    }
});

function handleExcelFile(file) {
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExt)) {
        alert('Please select an Excel (.xlsx, .xls) or CSV file');
        return;
    }
    
    excelFile = file;
    excelFileName.textContent = file.name;
    excelFileInfo.textContent = `${(file.size / 1024).toFixed(2)} KB`;
    selectedExcelFile.style.display = 'block';
    
    // Get columns from file
    getExcelColumns(file);
}

function removeExcelFile() {
    excelFile = null;
    excelInput.value = '';
    selectedExcelFile.style.display = 'none';
    columnSelection.style.display = 'none';
    scanExcelBtn.disabled = true;
    excelColumns = [];
}

async function getExcelColumns(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/get-excel-columns', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            excelColumns = data.columns;
            displayColumnCheckboxes(data.columns, data.row_count);
            columnSelection.style.display = 'block';
            scanExcelBtn.disabled = false;
            excelFileInfo.textContent = `${(file.size / 1024).toFixed(2)} KB - ${data.row_count} rows, ${data.columns.length} columns`;
        } else {
            alert('Error loading file: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error loading file: ' + error.message);
    }
}

function displayColumnCheckboxes(columns, rowCount) {
    const container = document.getElementById('column-checkboxes');
    container.innerHTML = columns.map((col, index) => `
        <div class="checkbox-group" style="margin-bottom: 10px;">
            <input type="checkbox" id="col-${index}" value="${col}" checked>
            <label for="col-${index}" style="color: #fff; cursor: pointer;">${col}</label>
        </div>
    `).join('');
}

function selectAllColumns() {
    excelColumns.forEach((col, index) => {
        document.getElementById(`col-${index}`).checked = true;
    });
}

function deselectAllColumns() {
    excelColumns.forEach((col, index) => {
        document.getElementById(`col-${index}`).checked = false;
    });
}

// Scan Excel for duplicates
scanExcelBtn.addEventListener('click', async () => {
    if (!excelFile) {
        alert('Please select an Excel/CSV file');
        return;
    }
    
    // Get selected columns
    const selectedColumns = [];
    excelColumns.forEach((col, index) => {
        const checkbox = document.getElementById(`col-${index}`);
        if (checkbox.checked) {
            selectedColumns.push(col);
        }
    });
    
    if (selectedColumns.length === 0) {
        alert('Please select at least one column to check for duplicates');
        return;
    }
    
    const keepFirst = document.getElementById('keep-first-duplicate').checked;
    
    try {
        showExcelProgress('Starting scan...');
        
        const formData = new FormData();
        formData.append('file', excelFile);
        formData.append('columns', JSON.stringify(selectedColumns));
        formData.append('keep_first', keepFirst);
        
        const response = await fetch('/find-excel-duplicates', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentExcelJobId = data.job_id;
            startExcelProgressCheck();
        } else {
            showExcelError(data.error || 'Failed to start scan');
        }
    } catch (error) {
        showExcelError('Network error: ' + error.message);
    }
});

function startExcelProgressCheck() {
    if (excelCheckInterval) {
        clearInterval(excelCheckInterval);
    }
    
    excelCheckInterval = setInterval(async () => {
        if (!currentExcelJobId) return;
        
        try {
            const response = await fetch(`/status/${currentExcelJobId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateExcelProgress(data);
                
                if (data.status === 'completed') {
                    clearInterval(excelCheckInterval);
                    
                    // Check if this is an export job
                    if (data.type === 'excel_export') {
                        const downloadUrl = `/download/${currentExcelJobId}`;
                        alert(`${data.message}\n\nClick OK to download the file.`);
                        window.location.href = downloadUrl;
                    } else {
                        // Regular duplicate scan
                        showExcelResults(data);
                    }
                } else if (data.status === 'failed') {
                    clearInterval(excelCheckInterval);
                    showExcelError(data.message || 'Operation failed');
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 1000);
}

function updateExcelProgress(data) {
    const progress = data.progress || 0;
    document.getElementById('excel-progress-fill').style.width = `${progress}%`;
    document.getElementById('excel-progress-text').textContent = `${progress}%`;
    document.getElementById('excel-progress-message').textContent = data.message || 'Scanning...';
}

function showExcelProgress(message) {
    document.getElementById('excel-progress-section').style.display = 'block';
    document.getElementById('excel-results-section').style.display = 'none';
    document.getElementById('excel-error-section').style.display = 'none';
    document.getElementById('excel-progress-title').textContent = message;
    document.getElementById('excel-progress-fill').style.width = '0%';
    document.getElementById('excel-progress-text').textContent = '0%';
}

function showExcelResults(data) {
    document.getElementById('excel-progress-section').style.display = 'none';
    document.getElementById('excel-error-section').style.display = 'none';
    document.getElementById('excel-results-section').style.display = 'block';
    
    // Update stats
    document.getElementById('excel-duplicate-count').textContent = data.duplicate_records || 0;
    document.getElementById('excel-unique-count').textContent = data.unique_records || 0;
    document.getElementById('excel-total-count').textContent = data.total_records || 0;
    
    // Display duplicate groups
    displayExcelDuplicates(data.duplicate_groups || []);
    
    // Store job_id for exports
    window.currentExcelJobId = currentExcelJobId;
    
    // Automatically show download link for cleaned file if available
    if (data.output_path && data.output_filename) {
        const downloadUrl = `/download/${currentExcelJobId}`;
        const downloadSection = document.getElementById('excel-results-section');
        
        // Add automatic download section at the top
        const autoDownloadHtml = `
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 2px solid #10b981; text-align: center;">
                <h3 style="color: #fff; margin-bottom: 15px;">
                    <i class="fas fa-download"></i> Cleaned File Ready!
                </h3>
                <p style="color: #fff; font-size: 16px; margin-bottom: 20px;">
                    Your file without duplicates has been created automatically.<br>
                    <strong>${data.unique_records || 0} unique records</strong> (${data.duplicate_records || 0} duplicates removed)
                </p>
                <a href="${downloadUrl}" class="btn btn-success" style="padding: 15px 40px; font-size: 18px; text-decoration: none; display: inline-block;">
                    <i class="fas fa-download"></i> Download Cleaned File (${data.output_filename || 'cleaned_file'})
                </a>
            </div>
        `;
        
        // Insert at the beginning of results section
        const resultsHeader = document.querySelector('#excel-results-section .results-header');
        if (resultsHeader && !document.getElementById('auto-download-section')) {
            const autoDownloadDiv = document.createElement('div');
            autoDownloadDiv.id = 'auto-download-section';
            autoDownloadDiv.innerHTML = autoDownloadHtml;
            downloadSection.insertBefore(autoDownloadDiv, resultsHeader);
        }
    }
}

function displayExcelDuplicates(duplicateGroups) {
    const container = document.getElementById('excel-duplicate-records');
    
    if (duplicateGroups.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #888;">
                <i class="fas fa-check-circle" style="font-size: 48px; color: #10b981; margin-bottom: 20px;"></i>
                <p style="font-size: 18px; color: #fff;">No duplicate records found!</p>
                <p style="font-size: 14px; margin-top: 10px;">All records are unique.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = duplicateGroups.map((group, groupIndex) => `
        <div class="duplicate-group" style="margin-bottom: 20px;">
            <div class="duplicate-group-header">
                <div class="duplicate-group-info">
                    <div class="duplicate-group-title">
                        ${group.count} duplicate records found
                    </div>
                    <div class="duplicate-group-meta">
                        Matching values: ${Object.entries(group.key).map(([k, v]) => `${k}=${v}`).join(', ')}
                    </div>
                </div>
            </div>
            <div style="max-height: 300px; overflow-y: auto; margin-top: 15px;">
                ${group.rows.map((row, rowIndex) => `
                    <div class="file-item" style="margin-bottom: 10px;">
                        <div class="file-item-info">
                            <i class="fas fa-file-alt file-item-icon"></i>
                            <div class="file-item-details" style="flex: 1;">
                                <div class="file-item-name">Row ${group.indices[rowIndex] + 1}</div>
                                <div style="color: #888; font-size: 12px; margin-top: 5px;">
                                    ${Object.entries(row).map(([key, value]) => 
                                        `<strong>${key}:</strong> ${value !== null && value !== undefined ? value : '(empty)'}`
                                    ).join(' | ')}
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function showExcelError(message) {
    document.getElementById('excel-progress-section').style.display = 'none';
    document.getElementById('excel-results-section').style.display = 'none';
    document.getElementById('excel-error-section').style.display = 'block';
    document.getElementById('excel-error-message').textContent = message;
}

function resetExcelSection() {
    document.getElementById('excel-error-section').style.display = 'none';
    removeExcelFile();
}

// Export buttons
document.getElementById('export-unique-btn').addEventListener('click', () => exportExcel('unique'));
document.getElementById('export-duplicates-btn').addEventListener('click', () => exportExcel('duplicates'));
document.getElementById('export-cleaned-btn').addEventListener('click', () => exportExcel('cleaned'));

async function exportExcel(exportType) {
    if (!window.currentExcelJobId) {
        alert('No scan data available');
        return;
    }
    
    try {
        showExcelProgress('Creating export file...');
        
        const response = await fetch('/export-excel-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_id: window.currentExcelJobId,
                export_type: exportType
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Start checking progress for export
            const exportJobId = data.job_id;
            currentExcelJobId = exportJobId;
            startExcelProgressCheck();
        } else {
            showExcelError(data.error || 'Failed to create export');
        }
    } catch (error) {
        showExcelError('Network error: ' + error.message);
    }
}


// Create clean folder button
document.getElementById('create-clean-folder-btn').addEventListener('click', async () => {
    if (!window.currentScanJobId) {
        showError('No scan data available');
        return;
    }
    
    if (!confirm(`Create a new folder with ${window.uniqueFilesCount} unique files (no duplicates)?`)) {
        return;
    }
    
    try {
        showProgress('Creating clean folder...');
        
        const response = await fetch('/create-clean-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ job_id: window.currentScanJobId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Start checking progress for folder creation
            const folderJobId = data.job_id;
            currentJobId = folderJobId;
            startProgressCheck();
        } else {
            showError(data.error || 'Failed to create clean folder');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
});


