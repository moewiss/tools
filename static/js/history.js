// Download History Management

let currentFilter = 'all';
let allDownloads = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentFilter = btn.getAttribute('data-filter');
            
            // Update active state
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            filterDownloads();
        });
    });
    
    // Clear history button
    document.getElementById('clear-history-btn').addEventListener('click', clearHistory);
}

async function loadHistory() {
    try {
        showLoading();
        
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (response.ok) {
            allDownloads = data.downloads;
            updateStatistics(data.statistics);
            displayDownloads(allDownloads);
        } else {
            showError('Failed to load history');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showError('Network error while loading history');
    }
}

function updateStatistics(stats) {
    document.getElementById('stat-total').textContent = stats.total_downloads;
    document.getElementById('stat-completed').textContent = stats.completed;
    document.getElementById('stat-failed').textContent = stats.failed;
    document.getElementById('stat-size').textContent = (stats.total_size_mb / 1024).toFixed(2) + ' GB';
}

function displayDownloads(downloads) {
    const list = document.getElementById('downloads-list');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    
    loadingState.style.display = 'none';
    
    if (!downloads || downloads.length === 0) {
        list.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    list.style.display = 'flex';
    emptyState.style.display = 'none';
    
    list.innerHTML = downloads.map(download => createDownloadCard(download)).join('');
    
    // Add event listeners to buttons
    addButtonListeners();
}

function createDownloadCard(download) {
    const statusIcon = getStatusIcon(download.status);
    const statusClass = download.status === 'completed' ? 'success' : download.status === 'failed' ? 'failed' : '';
    const date = new Date(download.downloaded_date).toLocaleString();
    const fileSize = download.file_size ? formatFileSize(download.file_size) : 'Unknown';
    
    return `
        <div class="download-item" data-id="${download.id}">
            <div class="download-header">
                <div class="download-icon ${statusClass}">
                    ${statusIcon}
                </div>
                <div class="download-info">
                    <div class="download-title">
                        ${download.is_playlist ? '📋 ' : ''}${download.title || 'Untitled Download'}
                    </div>
                    <div class="download-meta">
                        <span><i class="fas fa-clock"></i> ${date}</span>
                        <span><i class="fas fa-${download.format_type === 'audio' ? 'music' : 'video'}"></i> ${download.format_type.toUpperCase()}</span>
                        <span><i class="fas fa-signal"></i> ${download.quality}</span>
                        <span><i class="fas fa-hdd"></i> ${fileSize}</span>
                        ${download.video_count ? `<span><i class="fas fa-list"></i> ${download.video_count} videos</span>` : ''}
                    </div>
                    ${download.error_message ? `<div class="download-error"><i class="fas fa-exclamation-triangle"></i> ${download.error_message}</div>` : ''}
                </div>
            </div>
            <div class="download-actions">
                <button class="btn-action btn-redownload" data-id="${download.id}">
                    <i class="fas fa-redo"></i> Re-download
                </button>
                <button class="btn-action btn-delete" data-id="${download.id}">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `;
}

function getStatusIcon(status) {
    switch (status) {
        case 'completed':
            return '<i class="fas fa-check-circle"></i>';
        case 'failed':
            return '<i class="fas fa-times-circle"></i>';
        case 'in_progress':
            return '<i class="fas fa-spinner fa-spin"></i>';
        default:
            return '<i class="fas fa-clock"></i>';
    }
}

function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    const mb = bytes / (1024 * 1024);
    if (mb < 1024) {
        return mb.toFixed(2) + ' MB';
    }
    return (mb / 1024).toFixed(2) + ' GB';
}

function addButtonListeners() {
    // Re-download buttons
    document.querySelectorAll('.btn-redownload').forEach(btn => {
        btn.addEventListener('click', () => redownload(btn.getAttribute('data-id')));
    });
    
    // Delete buttons
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => deleteDownload(btn.getAttribute('data-id')));
    });
}

async function redownload(downloadId) {
    if (!confirm('Re-download this video with the same settings?')) return;
    
    try {
        const response = await fetch(`/api/history/redownload/${downloadId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Check if it's a subtitle download or regular download
            const formatType = data.format_type || '';
            
            if (formatType.includes('subs') || formatType.includes('subtitle')) {
                alert('Re-download started! Check the subtitle downloader page for progress.');
                window.location.href = '/tool/subtitle-downloader';
            } else {
                alert('Re-download started! Check the downloader page for progress.');
                window.location.href = '/tool/media-converter';
            }
        } else {
            alert('Failed to start re-download: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error re-downloading:', error);
        alert('Network error while starting re-download');
    }
}

async function deleteDownload(downloadId) {
    if (!confirm('Delete this download from history?')) return;
    
    try {
        const response = await fetch(`/api/history/${downloadId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Remove from list
            allDownloads = allDownloads.filter(d => d.id != downloadId);
            filterDownloads();
            
            // Reload to update statistics
            loadHistory();
        } else {
            alert('Failed to delete download');
        }
    } catch (error) {
        console.error('Error deleting:', error);
        alert('Network error while deleting');
    }
}

async function clearHistory() {
    if (!confirm('Clear all download history? This cannot be undone!')) return;
    
    try {
        const response = await fetch('/api/history/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            allDownloads = [];
            loadHistory();
        } else {
            alert('Failed to clear history');
        }
    } catch (error) {
        console.error('Error clearing history:', error);
        alert('Network error while clearing history');
    }
}

async function handleSearch(event) {
    const query = event.target.value.trim();
    
    if (!query) {
        filterDownloads();
        return;
    }
    
    try {
        const response = await fetch(`/api/history/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (response.ok) {
            displayDownloads(data.downloads);
        }
    } catch (error) {
        console.error('Error searching:', error);
    }
}

function filterDownloads() {
    let filtered = allDownloads;
    
    if (currentFilter !== 'all') {
        filtered = allDownloads.filter(d => d.status === currentFilter);
    }
    
    displayDownloads(filtered);
}

function showLoading() {
    document.getElementById('loading-state').style.display = 'block';
    document.getElementById('downloads-list').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';
}

function showError(message) {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('downloads-list').style.display = 'none';
    document.getElementById('empty-state').style.display = 'block';
    document.getElementById('empty-state').innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error</h3>
        <p>${message}</p>
        <button class="btn-primary" onclick="loadHistory()">
            <i class="fas fa-redo"></i> Retry
        </button>
    `;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

console.log('Download History page loaded');

