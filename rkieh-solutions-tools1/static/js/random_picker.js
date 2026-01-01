// Random Picker - JavaScript

let options = [];
let filteredOptions = [];
let pickMode = 'single';
let pickHistory = [];
let isSearching = false;

const optionInput = document.getElementById('option-input');
const addOptionBtn = document.getElementById('add-option-btn');
const optionsList = document.getElementById('options-list');
const pickBtn = document.getElementById('pick-btn');
const pickOptionBtns = document.querySelectorAll('.pick-option-btn');
const multipleCountGroup = document.getElementById('multiple-count-group');
const pickCountInput = document.getElementById('pick-count');
const resultSection = document.getElementById('result-section');
const resultDisplay = document.getElementById('result-display');
const resultLabel = document.getElementById('result-label');
const pickAgainBtn = document.getElementById('pick-again-btn');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history-btn');
const fileInput = document.getElementById('file-input');
const fileNameInput = document.getElementById('file-name');
const videoUrlInput = document.getElementById('video-url');
const loadCommentsBtn = document.getElementById('load-comments-btn');
const commentsLoading = document.getElementById('comments-loading');
const searchInput = document.getElementById('search-input');
const searchResultsCount = document.getElementById('search-results-count');
const clearSearchBtn = document.getElementById('clear-search-btn');

// File upload handler
fileInput.addEventListener('change', handleFileUpload);

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) {
        return;
    }
    
    fileNameInput.value = file.name;
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const content = e.target.result;
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        try {
            let fileOptions = [];
            
            if (fileExtension === 'txt') {
                // Text file - one option per line
                fileOptions = content.split('\n')
                    .map(line => line.trim())
                    .filter(line => line.length > 0);
            } else if (fileExtension === 'csv') {
                // CSV file - one option per row
                const lines = content.split('\n');
                fileOptions = lines
                    .map(line => {
                        // Handle CSV - take first column or whole line if no comma
                        const parts = line.split(',');
                        return parts[0].trim();
                    })
                    .filter(line => line.length > 0);
            } else if (fileExtension === 'json') {
                // JSON file - array of options
                const data = JSON.parse(content);
                if (Array.isArray(data)) {
                    fileOptions = data.map(item => String(item).trim()).filter(item => item.length > 0);
                } else if (typeof data === 'object') {
                    // If it's an object, try to find an array property
                    for (let key in data) {
                        if (Array.isArray(data[key])) {
                            fileOptions = data[key].map(item => String(item).trim()).filter(item => item.length > 0);
                            break;
                        }
                    }
                }
            }
            
            if (fileOptions.length === 0) {
                alert('No valid options found in the file. Make sure the file contains options (one per line for .txt, one per row for .csv, or an array for .json).');
                return;
            }
            
            // Add options (skip duplicates)
            let added = 0;
            let skipped = 0;
            fileOptions.forEach(option => {
                if (!options.includes(option)) {
                    options.push(option);
                    added++;
                } else {
                    skipped++;
                }
            });
            
            // Clear search when loading from file
            if (isSearching) {
                clearSearch();
            }
            updateOptionsDisplay();
            updatePickButton();
            
            // Show success message
            const message = `Loaded ${added} option${added !== 1 ? 's' : ''} from file${skipped > 0 ? ` (${skipped} duplicate${skipped !== 1 ? 's' : ''} skipped)` : ''}`;
            showNotification(message, 'success');
            
        } catch (error) {
            alert('Error reading file: ' + error.message);
            fileNameInput.value = 'No file selected';
        }
    };
    
    reader.onerror = function() {
        alert('Error reading file');
        fileNameInput.value = 'No file selected';
    };
    
    reader.readAsText(file);
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#55ff55' : '#ff3333'};
        color: #000;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Load comments from video
loadCommentsBtn.addEventListener('click', loadVideoComments);

// Global variable to store platform info
let currentPlatform = {
    name: 'unknown',
    baseUrl: ''
};

function loadVideoComments() {
    const videoUrl = videoUrlInput.value.trim();
    
    if (!videoUrl) {
        alert('Please enter a video URL');
        return;
    }
    
    // Validate URL
    try {
        new URL(videoUrl);
    } catch (e) {
        alert('Please enter a valid URL');
        return;
    }
    
    // Detect platform from URL
    if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
        currentPlatform = { name: 'youtube', baseUrl: 'https://www.youtube.com/' };
    } else if (videoUrl.includes('instagram.com')) {
        currentPlatform = { name: 'instagram', baseUrl: 'https://www.instagram.com/' };
    } else if (videoUrl.includes('tiktok.com')) {
        currentPlatform = { name: 'tiktok', baseUrl: 'https://www.tiktok.com/@' };
    } else if (videoUrl.includes('facebook.com')) {
        currentPlatform = { name: 'facebook', baseUrl: 'https://www.facebook.com/' };
    } else if (videoUrl.includes('twitter.com') || videoUrl.includes('x.com')) {
        currentPlatform = { name: 'twitter', baseUrl: 'https://twitter.com/' };
    } else {
        currentPlatform = { name: 'unknown', baseUrl: '' };
    }
    
    // Show loading
    loadCommentsBtn.disabled = true;
    commentsLoading.style.display = 'block';
    
    // Send to backend
    fetch('/extract-video-comments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: videoUrl
        })
    })
    .then(response => response.json())
    .then(data => {
        loadCommentsBtn.disabled = false;
        commentsLoading.style.display = 'none';
        
        if (data.success) {
            const comments = data.comments || [];
            
            if (comments.length === 0) {
                showNotification('No comments found in this video', 'error');
                return;
            }
            
            // Add comments as options (skip duplicates)
            let added = 0;
            let skipped = 0;
            comments.forEach(comment => {
                // Handle both object format (with author) and string format
                let commentObj;
                if (typeof comment === 'object' && comment.text) {
                    commentObj = {
                        text: comment.text,
                        author: comment.author || 'Unknown',
                        isComment: true
                    };
                } else {
                    // Fallback for string comments
                    commentObj = {
                        text: typeof comment === 'string' ? comment : String(comment),
                        author: 'Unknown',
                        isComment: true
                    };
                }
                
                // Check for duplicates (by text)
                const commentText = commentObj.text;
                const isDuplicate = options.some(opt => {
                    if (typeof opt === 'object' && opt.text) {
                        return opt.text === commentText;
                    }
                    return opt === commentText;
                });
                
                if (!isDuplicate) {
                    options.push(commentObj);
                    added++;
                } else {
                    skipped++;
                }
            });
            
            // Clear search when loading comments
            if (isSearching) {
                clearSearch();
            }
            updateOptionsDisplay();
            updatePickButton();
            
            const message = `Loaded ${added} comment${added !== 1 ? 's' : ''} from video${skipped > 0 ? ` (${skipped} duplicate${skipped !== 1 ? 's' : ''} skipped)` : ''}`;
            showNotification(message, 'success');
            
            // Clear URL input
            videoUrlInput.value = '';
        } else {
            showNotification(data.error || 'Failed to load comments', 'error');
        }
    })
    .catch(error => {
        loadCommentsBtn.disabled = false;
        commentsLoading.style.display = 'none';
        showNotification('Error loading comments: ' + error.message, 'error');
    });
}

// Load history from localStorage
function loadHistory() {
    const saved = localStorage.getItem('pickerHistory');
    if (saved) {
        pickHistory = JSON.parse(saved);
        updateHistoryDisplay();
    }
}

// Save history to localStorage
function saveHistory() {
    localStorage.setItem('pickerHistory', JSON.stringify(pickHistory));
}

// Add option
addOptionBtn.addEventListener('click', addOption);
optionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addOption();
    }
});

function addOption() {
    const option = optionInput.value.trim();
    if (!option) {
        return;
    }
    
    if (options.includes(option)) {
        alert('This option already exists!');
        return;
    }
    
    options.push(option);
    optionInput.value = '';
    // Clear search when adding new option
    if (isSearching) {
        clearSearch();
    }
    updateOptionsDisplay();
    updatePickButton();
}

// Remove option
function removeOption(option) {
    // Handle both object and string formats
    options = options.filter(o => {
        if (typeof option === 'object' && option.text) {
            if (typeof o === 'object' && o.text) {
                return o.text !== option.text;
            }
            return true;
        } else {
            if (typeof o === 'object' && o.text) {
                return o.text !== option;
            }
            return o !== option;
        }
    });
    updateOptionsDisplay();
    updatePickButton();
}

// Remove option by index (for display)
function removeOptionFromList(index) {
    const optionsToUse = isSearching ? filteredOptions : options;
    const optionToRemove = optionsToUse[index];
    
    if (typeof optionToRemove === 'object' && optionToRemove.text) {
        removeOption(optionToRemove);
    } else {
        removeOption(optionToRemove);
    }
}

// Search functionality
searchInput.addEventListener('input', handleSearch);
clearSearchBtn.addEventListener('click', clearSearch);

function handleSearch() {
    const searchTerm = searchInput.value.trim().toLowerCase();
    
    if (searchTerm === '') {
        clearSearch();
        return;
    }
    
    isSearching = true;
    clearSearchBtn.style.display = 'block';
    
    // Filter options (handle both object and string formats)
    filteredOptions = options.filter(option => {
        const searchText = typeof option === 'object' && option.text 
            ? option.text 
            : String(option);
        return searchText.toLowerCase().includes(searchTerm);
    });
    
    // Update display with filtered options
    displayOptions(filteredOptions);
    
    // Update search results count
    if (filteredOptions.length === 0) {
        searchResultsCount.innerHTML = '<span style="color: #ff5555;">No matches found</span>';
    } else {
        searchResultsCount.innerHTML = `<span style="color: #55ff55;">Found ${filteredOptions.length} of ${options.length} option${options.length !== 1 ? 's' : ''}</span>`;
    }
}

function clearSearch() {
    searchInput.value = '';
    isSearching = false;
    filteredOptions = [];
    clearSearchBtn.style.display = 'none';
    searchResultsCount.innerHTML = '';
    updateOptionsDisplay();
}

// Update options display
function updateOptionsDisplay() {
    if (isSearching && filteredOptions.length > 0) {
        displayOptions(filteredOptions);
        return;
    }
    
    if (options.length === 0) {
        optionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No options added yet. Add your choices above!</p>
            </div>
        `;
        return;
    }
    
    displayOptions(options);
}

function displayOptions(optionsToDisplay) {
    if (optionsToDisplay.length === 0) {
        optionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No options match your search</p>
            </div>
        `;
        return;
    }
    
    const searchTerm = searchInput.value.trim();
    optionsList.innerHTML = optionsToDisplay.map((option, index) => {
        // Handle both object format (comments with author) and string format
        let optionText, optionAuthor, optionValue;
        
        if (typeof option === 'object' && option.text) {
            // Comment object with author
            optionText = option.text;
            optionAuthor = option.author;
            optionValue = JSON.stringify(option); // Store as JSON for removal
        } else {
            // Regular string option
            optionText = String(option);
            optionAuthor = null;
            optionValue = optionText;
        }
        
        const displayText = highlightSearchTerm(escapeHtml(optionText), searchTerm);
        
        // Create clickable author link if we have platform info
        let authorDisplay = '';
        if (optionAuthor && optionAuthor !== 'Unknown') {
            const authorUsername = optionAuthor.replace(/^@/, ''); // Remove @ if present
            
            if (currentPlatform.baseUrl) {
                // Clickable author link
                const profileUrl = currentPlatform.baseUrl + authorUsername;
                authorDisplay = `<a href="${escapeHtml(profileUrl)}" target="_blank" style="display: inline-flex; align-items: center; gap: 5px; color: #ff3333; font-size: 14px; font-weight: 700; margin-top: 6px; text-decoration: none; padding: 5px 10px; background: rgba(255, 51, 51, 0.1); border: 1px solid #ff3333; border-radius: 15px; transition: all 0.2s; cursor: pointer;" onmouseover="this.style.background='#ff3333'; this.style.color='#fff';" onmouseout="this.style.background='rgba(255, 51, 51, 0.1)'; this.style.color='#ff3333';">
                    👤 @${escapeHtml(optionAuthor)}
                </a>`;
            } else {
                // Non-clickable author
                authorDisplay = `<div style="color: #ff3333; font-size: 14px; font-weight: 700; margin-top: 6px; opacity: 1;">👤 @${escapeHtml(optionAuthor)}</div>`;
            }
        }
        
        return `
            <div class="option-item">
                <span class="option-text" style="display: block;">
                    <div style="font-size: 16px; margin-bottom: 4px;">${displayText}</div>
                    ${authorDisplay}
                </span>
                <button type="button" class="option-remove" onclick="removeOptionFromList(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }).join('');
}

function highlightSearchTerm(text, searchTerm) {
    if (!searchTerm || searchTerm === '') {
        return text;
    }
    
    const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi');
    return text.replace(regex, '<mark style="background: #ff3333; color: #fff; padding: 2px 4px; border-radius: 3px;">$1</mark>');
}

function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Make removeOptionFromList available globally
window.removeOptionFromList = function(index) {
    const optionsToUse = isSearching ? filteredOptions : options;
    const optionToRemove = optionsToUse[index];
    
    if (typeof optionToRemove === 'object' && optionToRemove.text) {
        // Remove comment object
        options = options.filter(o => {
            if (typeof o === 'object' && o.text) {
                return o.text !== optionToRemove.text;
            }
            return true;
        });
    } else {
        // Remove string option
        options = options.filter(o => {
            if (typeof o === 'object' && o.text) {
                return o.text !== optionToRemove;
            }
            return o !== optionToRemove;
        });
    }
    
    // Clear search if active
    if (isSearching) {
        clearSearch();
    }
    
    updateOptionsDisplay();
    updatePickButton();
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update pick button state
function updatePickButton() {
    pickBtn.disabled = options.length === 0;
}

// Pick mode selection
pickOptionBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        pickOptionBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        pickMode = btn.dataset.pick;
        
        if (pickMode === 'multiple') {
            multipleCountGroup.style.display = 'block';
        } else {
            multipleCountGroup.style.display = 'none';
        }
    });
});

// Pick randomly
pickBtn.addEventListener('click', pickRandom);
pickAgainBtn.addEventListener('click', pickRandom);

function pickRandom() {
    // Use filtered options if searching, otherwise use all options
    const availableOptions = isSearching && filteredOptions.length > 0 
        ? [...filteredOptions] 
        : [...options];
    
    if (availableOptions.length === 0) {
        if (isSearching) {
            alert('No options match your search. Clear the search to pick from all options.');
        } else {
            alert('No options available');
        }
        return;
    }
    let results = [];
    
    if (pickMode === 'single') {
        // Pick one
        const randomIndex = Math.floor(Math.random() * availableOptions.length);
        results = [availableOptions[randomIndex]];
        resultLabel.textContent = 'The winner is...';
    } else if (pickMode === 'multiple') {
        // Pick multiple
        const count = Math.min(parseInt(pickCountInput.value) || 2, availableOptions.length);
        const shuffled = [...availableOptions].sort(() => Math.random() - 0.5);
        results = shuffled.slice(0, count);
        resultLabel.textContent = `Picked ${count} option${count > 1 ? 's' : ''}:`;
    } else if (pickMode === 'remove') {
        // Pick and remove
        const randomIndex = Math.floor(Math.random() * availableOptions.length);
        const picked = availableOptions[randomIndex];
        results = [picked];
        removeOption(picked);
        resultLabel.textContent = 'Picked and removed:';
    }
    
    // Animate result
    resultDisplay.classList.add('spinning');
    resultDisplay.textContent = '...';
    
    setTimeout(() => {
        resultDisplay.classList.remove('spinning');
        if (results.length === 1) {
            const result = results[0];
            if (typeof result === 'object' && result.text) {
                // Comment object - show text and author
                const authorDisplay = result.author && result.author !== 'Unknown' 
                    ? `<div style="color: #ff3333; font-size: 24px; margin-top: 15px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 10px;"><span style="font-size: 28px;">👤</span> @${escapeHtml(result.author)}</div>`
                    : '';
                resultDisplay.innerHTML = `
                    <div style="font-size: 36px; margin-bottom: 10px;">${escapeHtml(result.text)}</div>
                    ${authorDisplay}
                `;
            } else {
                resultDisplay.textContent = String(result);
            }
        } else {
            resultDisplay.innerHTML = results.map(r => {
                if (typeof r === 'object' && r.text) {
                    // Comment object
                    const authorDisplay = r.author && r.author !== 'Unknown'
                        ? `<div style="color: #ff3333; font-size: 18px; margin-top: 8px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px;"><span style="font-size: 20px;">👤</span> @${escapeHtml(r.author)}</div>`
                        : '';
                    return `<div style="margin: 15px 0; font-size: 32px; padding: 15px; background: rgba(255, 51, 51, 0.1); border-radius: 8px; border: 2px solid rgba(255, 51, 51, 0.3);">
                        <div>${escapeHtml(r.text)}</div>
                        ${authorDisplay}
                    </div>`;
                } else {
                    return `<div style="margin: 10px 0; font-size: 36px;">${escapeHtml(String(r))}</div>`;
                }
            }).join('');
        }
        
        resultSection.classList.add('show');
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Add to history
        const historyEntry = {
            mode: pickMode,
            results: results,
            timestamp: new Date().toLocaleString()
        };
        pickHistory.unshift(historyEntry);
        if (pickHistory.length > 20) {
            pickHistory = pickHistory.slice(0, 20);
        }
        saveHistory();
        updateHistoryDisplay();
    }, 1000);
}

// Update history display
function updateHistoryDisplay() {
    if (pickHistory.length === 0) {
        historyList.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No picks yet</p>';
        return;
    }
    
    historyList.innerHTML = pickHistory.map(entry => {
        const formatResult = (result) => {
            if (typeof result === 'object' && result.text) {
                // Comment object with author - make username clickable
                let authorDisplay = '';
                if (result.author && result.author !== 'Unknown') {
                    const authorUsername = result.author.replace(/^@/, ''); // Remove @ if present
                    
                    if (currentPlatform.baseUrl) {
                        // Clickable author link
                        const profileUrl = currentPlatform.baseUrl + authorUsername;
                        authorDisplay = ` <a href="${escapeHtml(profileUrl)}" target="_blank" style="display: inline-flex; align-items: center; gap: 3px; color: #ff3333; font-size: 13px; font-weight: 700; text-decoration: none; padding: 3px 8px; background: rgba(255, 51, 51, 0.1); border: 1px solid #ff3333; border-radius: 12px; transition: all 0.2s; cursor: pointer;" onmouseover="this.style.background='#ff3333'; this.style.color='#fff';" onmouseout="this.style.background='rgba(255, 51, 51, 0.1)'; this.style.color='#ff3333';">
                            👤 @${escapeHtml(result.author)}
                        </a>`;
                    } else {
                        // Non-clickable author
                        authorDisplay = ` <span style="color: #ff3333; font-size: 13px; font-weight: 700;">👤 @${escapeHtml(result.author)}</span>`;
                    }
                }
                return escapeHtml(result.text) + authorDisplay;
            }
            return escapeHtml(String(result));
        };
        
        const resultsText = entry.results.length === 1 
            ? formatResult(entry.results[0])
            : entry.results.map(formatResult).join(', ');
        return `
            <div class="history-item">
                <span>${resultsText}</span>
                <span style="color: #888; font-size: 12px;">${entry.timestamp}</span>
            </div>
        `;
    }).join('');
}

// Clear history
clearHistoryBtn.addEventListener('click', () => {
    if (confirm('Clear all pick history?')) {
        pickHistory = [];
        saveHistory();
        updateHistoryDisplay();
    }
});

// Initialize
loadHistory();
updateOptionsDisplay();
updatePickButton();

