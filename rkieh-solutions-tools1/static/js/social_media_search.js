// Social Media Search - JavaScript

const searchInput = document.getElementById('search-name');
const searchBtn = document.getElementById('search-btn');
const statsSection = document.getElementById('stats-section');
const resultsSection = document.getElementById('results-section');
const emptySection = document.getElementById('empty-section');
const summaryStats = document.getElementById('summary-stats');
const resultsContainer = document.getElementById('results-container');

// Search on Enter key
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Search button click
searchBtn.addEventListener('click', performSearch);

function performSearch() {
    const searchTerm = searchInput.value.trim();
    
    if (!searchTerm) {
        alert('Please enter a name, username, or keyword to search');
        return;
    }
    
    // Show loading
    emptySection.style.display = 'none';
    statsSection.style.display = 'none';
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner"></i>
            <p>Searching for "${searchTerm}" across all platforms...</p>
        </div>
    `;
    
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
    
    // Send to backend
    fetch('/search-social-media', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: searchTerm
        })
    })
    .then(response => response.json())
    .then(data => {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fas fa-search"></i> Search All Platforms';
        
        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'Failed to search social media');
        }
    })
    .catch(error => {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fas fa-search"></i> Search All Platforms';
        showError('Error: ' + error.message);
    });
}

function displayResults(data) {
    // Display summary statistics
    if (data.stats) {
        statsSection.style.display = 'block';
        summaryStats.innerHTML = `
            <div class="stat-box">
                <div class="stat-value">${data.stats.total_profiles || 0}</div>
                <div class="stat-label">Total Profiles</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.platforms_found || 0}</div>
                <div class="stat-label">Platforms Found</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.total_followers || '0'}</div>
                <div class="stat-label">Total Followers</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.verified_count || 0}</div>
                <div class="stat-label">Verified Accounts</div>
            </div>
        `;
    }
    
    // Display platform results
    if (data.results && Object.keys(data.results).length > 0) {
        let resultsHTML = '';
        
        // ⭐ FIRST: Show all verified profiles at the top in a special section
        const allVerifiedProfiles = [];
        for (const [platform, profiles] of Object.entries(data.results)) {
            if (profiles && profiles.length > 0) {
                profiles.forEach(profile => {
                    if (profile.verified) {
                        allVerifiedProfiles.push({ ...profile, platform: platform });
                    }
                });
            }
        }
        
        // If we have verified profiles, show them in a highlighted section
        if (allVerifiedProfiles.length > 0) {
            resultsHTML += `
                <div class="verified-profiles-section" style="background: linear-gradient(135deg, rgba(29, 161, 242, 0.15), rgba(29, 161, 242, 0.05)); border: 3px solid #1DA1F2; border-radius: 20px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(29, 161, 242, 0.3);">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <i class="fas fa-certificate" style="font-size: 48px; color: #1DA1F2; margin-bottom: 15px; animation: pulse 2s ease-in-out infinite;"></i>
                        <h2 style="color: #1DA1F2; font-size: 28px; font-weight: 800; margin-bottom: 8px;">
                            <i class="fas fa-check-circle"></i> Potential Verified Profiles
                        </h2>
                        <p style="color: #fff; opacity: 0.9; font-size: 16px;">
                            These profiles may be verified - Click to visit and confirm verification status
                        </p>
                        <div style="background: rgba(255, 193, 7, 0.15); border-left: 4px solid #FFC107; padding: 12px 16px; border-radius: 8px; margin-top: 15px; font-size: 13px; color: #FFC107;">
                            <i class="fas fa-info-circle"></i> <strong>Note:</strong> We show likely profiles. Visit each profile to confirm if it's actually verified.
                        </div>
                    </div>
                    <div class="verified-profiles-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        ${allVerifiedProfiles.map(profile => `
                            <div style="background: rgba(0, 0, 0, 0.4); border: 2px solid #1DA1F2; border-radius: 15px; padding: 20px; transition: all 0.3s;">
                                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                                    <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #1DA1F2, #0d8bd9); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 20px;">${getInitials(profile.name || profile.handle)}</div>
                                    <div style="flex: 1;">
                                        <div style="color: #fff; font-size: 18px; font-weight: 700; margin-bottom: 4px;">
                                            ${escapeHtml(profile.name || profile.handle || 'Unknown')}
                                            <i class="fas fa-check-circle" style="color: #1DA1F2; margin-left: 6px;"></i>
                                        </div>
                                        <div style="color: #aaa; font-size: 14px;">@${escapeHtml(profile.handle || profile.username || 'unknown')}</div>
                                    </div>
                                    <div style="padding: 6px 12px; background: #1DA1F2; color: #fff; border-radius: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase;">${profile.platform}</div>
                                </div>
                                ${profile.description ? `<div style="color: #ccc; font-size: 14px; margin-bottom: 15px; line-height: 1.5;">${escapeHtml(profile.description)}</div>` : ''}
                                <div style="display: flex; gap: 15px; margin-bottom: 15px; font-size: 13px;">
                                    ${profile.followers ? `<div style="color: #aaa;"><i class="fas fa-users" style="color: #1DA1F2;"></i> ${formatNumber(profile.followers)}</div>` : ''}
                                    ${profile.posts ? `<div style="color: #aaa;"><i class="fas fa-images" style="color: #1DA1F2;"></i> ${formatNumber(profile.posts)}</div>` : ''}
                                </div>
                                ${profile.url ? `<a href="${escapeHtml(profile.url)}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #1DA1F2, #0d8bd9); color: #fff; padding: 10px 20px; border-radius: 25px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all 0.3s;"><i class="fas fa-external-link-alt"></i> View Verified Profile</a>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        resultsHTML += '<div class="platform-results">';
        
        // Define platform icons and colors
        const platformConfig = {
            'twitter': { icon: 'fab fa-twitter', color: '#1DA1F2', name: 'Twitter/X' },
            'instagram': { icon: 'fab fa-instagram', color: '#E4405F', name: 'Instagram' },
            'tiktok': { icon: 'fab fa-tiktok', color: '#000000', name: 'TikTok' },
            'youtube': { icon: 'fab fa-youtube', color: '#FF0000', name: 'YouTube' },
            'facebook': { icon: 'fab fa-facebook', color: '#1877F2', name: 'Facebook' },
            'linkedin': { icon: 'fab fa-linkedin', color: '#0077B5', name: 'LinkedIn' },
            'reddit': { icon: 'fab fa-reddit', color: '#FF4500', name: 'Reddit' },
            'snapchat': { icon: 'fab fa-snapchat', color: '#FFFC00', name: 'Snapchat' }
        };
        
        for (const [platform, profiles] of Object.entries(data.results)) {
            if (profiles && profiles.length > 0) {
                const config = platformConfig[platform] || { icon: 'fas fa-globe', color: '#ff3333', name: platform };
                
                // ⭐ SORT PROFILES: Verified first, then by type (Search first, then Profiles)
                const sortedProfiles = profiles.sort((a, b) => {
                    // First priority: Verified profiles come first
                    if (a.verified && !b.verified) return -1;
                    if (!a.verified && b.verified) return 1;
                    
                    // Second priority: Search options come before profiles
                    if (a.type === 'Search' && b.type !== 'Search') return -1;
                    if (a.type !== 'Search' && b.type === 'Search') return 1;
                    
                    // Otherwise maintain original order
                    return 0;
                });
                
                // Check if this platform has verified profiles
                const hasVerified = sortedProfiles.some(p => p.verified);
                
                resultsHTML += `
                    <div class="platform-card">
                        <div class="platform-header">
                            <div class="platform-icon" style="background: linear-gradient(135deg, ${config.color} 0%, ${config.color}dd 100%);">
                                <i class="${config.icon}" style="color: #fff;"></i>
                            </div>
                            <div class="platform-name">${config.name}</div>
                            <div class="result-count">
                                ${profiles.length} result${profiles.length !== 1 ? 's' : ''}
                                ${hasVerified ? ' <i class="fas fa-check-circle" style="color: #1DA1F2; margin-left: 5px;" title="Has verified profiles"></i>' : ''}
                            </div>
                        </div>
                        ${sortedProfiles.map(profile => `
                            <div class="profile-item">
                                <div class="profile-header" style="${profile.verified ? 'background: linear-gradient(135deg, rgba(29, 161, 242, 0.1), rgba(29, 161, 242, 0.05)); border: 2px solid rgba(29, 161, 242, 0.3); border-radius: 12px; padding: 10px;' : ''}">
                                    <div class="profile-avatar">${getInitials(profile.name || profile.handle)}</div>
                                    <div class="profile-info">
                                        <div class="profile-name">
                                            ${escapeHtml(profile.name || profile.handle || 'Unknown')}
                                            ${profile.verified ? `<span style="display: inline-block; margin-left: 8px; padding: 4px 12px; background: linear-gradient(135deg, #1DA1F2, #0d8bd9); color: #fff; border-radius: 12px; font-size: 11px; font-weight: 700; box-shadow: 0 2px 8px rgba(29, 161, 242, 0.4);"><i class="fas fa-check-circle"></i> VERIFIED</span>` : ''}
                                            ${profile.type && !profile.verified ? `<span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background: #333; color: #ff3333; border-radius: 10px; font-size: 11px; font-weight: 600;">${escapeHtml(profile.type)}</span>` : ''}
                                        </div>
                                        <div class="profile-handle">@${escapeHtml(profile.handle || profile.username || 'unknown')}</div>
                                    </div>
                                    ${profile.verified ? '<i class="fas fa-certificate" style="color: #1DA1F2; font-size: 28px; text-shadow: 0 0 10px rgba(29, 161, 242, 0.5);"></i>' : ''}
                                </div>
                                ${profile.description ? `<div class="profile-description">${escapeHtml(profile.description)}</div>` : ''}
                                <div class="profile-stats">
                                    ${profile.followers ? `<div class="stat-item"><i class="fas fa-users"></i> ${formatNumber(profile.followers)}</div>` : ''}
                                    ${profile.following ? `<div class="stat-item"><i class="fas fa-user-plus"></i> ${formatNumber(profile.following)}</div>` : ''}
                                    ${profile.posts ? `<div class="stat-item"><i class="fas fa-images"></i> ${formatNumber(profile.posts)}</div>` : ''}
                                    ${profile.views ? `<div class="stat-item"><i class="fas fa-eye"></i> ${formatNumber(profile.views)}</div>` : ''}
                                </div>
                                ${profile.url ? `<a href="${escapeHtml(profile.url)}" target="_blank" class="profile-link"><i class="fas fa-external-link-alt"></i> View Profile</a>` : ''}
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        }
        
        resultsHTML += '</div>';
        resultsContainer.innerHTML = resultsHTML;
    } else {
        resultsContainer.innerHTML = `
            <div class="empty-results">
                <i class="fas fa-search"></i>
                <h3 style="color: #fff;">No results found</h3>
                <p>Try a different search term or check the spelling</p>
            </div>
        `;
    }
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(message) {
    resultsContainer.innerHTML = `
        <div class="empty-results">
            <i class="fas fa-exclamation-triangle" style="color: #ff3333;"></i>
            <h3 style="color: #fff;">Error</h3>
            <p style="color: #ff5555;">${escapeHtml(message)}</p>
        </div>
    `;
    resultsSection.style.display = 'block';
}

function getInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

