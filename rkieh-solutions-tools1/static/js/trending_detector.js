// Trending Detector - JavaScript

let selectedPlatform = 'twitter';

const platformCards = document.querySelectorAll('.platform-card');
const trendingSearch = document.getElementById('trending-search');
const detectTrendsBtn = document.getElementById('detect-trends-btn');
const statsSection = document.getElementById('stats-section');
const resultsSection = document.getElementById('results-section');
const emptySection = document.getElementById('empty-section');
const trendingStats = document.getElementById('trending-stats');
const trendingResultsContainer = document.getElementById('trending-results-container');

// Platform selection
platformCards.forEach(card => {
    card.addEventListener('click', () => {
        platformCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        selectedPlatform = card.dataset.platform;
    });
});

// Search on Enter key
trendingSearch.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        detectTrends();
    }
});

// Detect trends
detectTrendsBtn.addEventListener('click', detectTrends);

function detectTrends() {
    const keyword = trendingSearch.value.trim();
    
    if (!keyword) {
        alert('Please enter a keyword, hashtag, or topic to analyze');
        return;
    }
    
    // Show loading
    emptySection.style.display = 'none';
    statsSection.style.display = 'none';
    resultsSection.style.display = 'block';
    trendingResultsContainer.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner"></i>
            <p>Analyzing trends for "${keyword}" on ${selectedPlatform}...</p>
        </div>
    `;
    
    detectTrendsBtn.disabled = true;
    detectTrendsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
    
    // Send to backend
    fetch('/detect-trends', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            keyword: keyword,
            platform: selectedPlatform
        })
    })
    .then(response => response.json())
    .then(data => {
        detectTrendsBtn.disabled = false;
        detectTrendsBtn.innerHTML = '<i class="fas fa-fire"></i> Detect Trends';
        
        if (data.success) {
            displayTrendingResults(data);
        } else {
            showError(data.error || 'Failed to detect trends');
        }
    })
    .catch(error => {
        detectTrendsBtn.disabled = false;
        detectTrendsBtn.innerHTML = '<i class="fas fa-fire"></i> Detect Trends';
        showError('Error: ' + error.message);
    });
}

function displayTrendingResults(data) {
    // Display statistics
    if (data.stats) {
        statsSection.style.display = 'block';
        trendingStats.innerHTML = `
            <div class="stat-box">
                <div class="stat-value">${data.stats.total_trends || 0}</div>
                <div class="stat-label">Total Trends</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.avg_engagement || 0}</div>
                <div class="stat-label">Avg Engagement</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.growth_rate || 0}%</div>
                <div class="stat-label">Growth Rate</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.peak_time || 'N/A'}</div>
                <div class="stat-label">Peak Time</div>
            </div>
        `;
    }
    
    // Display trending items
    if (data.trends && data.trends.length > 0) {
        let resultsHTML = '<div class="trending-results">';
        
        data.trends.forEach((trend, index) => {
            const rank = index + 1;
            const rankClass = rank <= 3 ? 'top' : '';
            
            // Enhanced styling for video content
            const isVideo = trend.is_video || trend.platform;
            const borderColor = isVideo ? '#FF0050' : (trend.is_real_link ? '#4CAF50' : '#333');
            const badgeColor = isVideo ? 'linear-gradient(135deg, #FF0050, #FF4081)' : '#4CAF50';
            const badgeText = isVideo ? '🎬 TRENDING VIDEO' : '✓ REAL CONTENT';
            
            resultsHTML += `
                <div class="trend-item" style="border: 2px solid ${borderColor}; ${isVideo ? 'background: linear-gradient(135deg, #1a1a2e 0%, #16162b 100%);' : ''}">
                    <div class="trend-rank ${rankClass}">${rank}</div>
                    <div class="trend-content">
                        ${trend.thumbnail ? `
                            <div style="margin-bottom: 15px; border-radius: 12px; overflow: hidden;">
                                <img src="${escapeHtml(trend.thumbnail)}" alt="Video thumbnail" 
                                     style="width: 100%; height: auto; display: block; max-height: 180px; object-fit: cover;" 
                                     onerror="this.style.display='none'">
                            </div>
                        ` : ''}
                        <div class="trend-title">
                            ${escapeHtml(trend.title || trend.text || trend.hashtag || 'Trending Topic')}
                            ${trend.is_real_link ? `<span style="display: inline-block; margin-left: 10px; padding: 5px 12px; background: ${badgeColor}; color: #fff; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">${badgeText}</span>` : ''}
                            ${trend.platform ? `<span style="display: inline-block; margin-left: 5px; padding: 4px 10px; background: #555; color: #fff; border-radius: 15px; font-size: 10px; font-weight: 600;">${escapeHtml(trend.platform)}</span>` : ''}
                        </div>
                        ${trend.channel ? `<p style="color: #888; font-size: 13px; margin: 5px 0;"><i class="fas fa-user"></i> ${escapeHtml(trend.channel)}</p>` : ''}
                        ${trend.description ? `<p style="color: #aaa; font-size: 14px; line-height: 1.6; margin: 10px 0;">${escapeHtml(trend.description)}</p>` : ''}
                        <div class="trend-meta">
                            ${trend.engagement && !trend.is_real_link ? `<span><i class="fas fa-heart"></i> ${formatNumber(trend.engagement)}</span>` : ''}
                            ${trend.mentions && !trend.is_real_link ? `<span><i class="fas fa-comments"></i> ${trend.mentions}</span>` : ''}
                            ${trend.mentions && trend.is_real_link ? `<span><i class="fas fa-tag"></i> ${trend.mentions}</span>` : ''}
                            ${trend.growth && !trend.is_real_link && trend.growth > 0 ? `<span><i class="fas fa-arrow-up"></i> +${trend.growth}%</span>` : ''}
                        </div>
                        ${trend.tags && trend.tags.length > 0 ? `
                            <div class="trend-tags">
                                ${trend.tags.map(tag => `<span class="trend-tag">#${escapeHtml(tag)}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${trend.url && trend.is_real_link ? `
                            <a href="${escapeHtml(trend.url)}" target="_blank" style="display: inline-flex; align-items: center; gap: 10px; background: ${isVideo ? 'linear-gradient(135deg, #FF0050, #FF4081)' : 'linear-gradient(135deg, #4CAF50, #45a049)'}; color: #fff; padding: 14px 28px; border-radius: 30px; text-decoration: none; font-weight: 700; font-size: 14px; margin-top: 15px; transition: all 0.3s; box-shadow: 0 6px 20px ${isVideo ? 'rgba(255, 0, 80, 0.4)' : 'rgba(76, 175, 80, 0.3)'};">
                                <i class="fas ${isVideo ? 'fa-play-circle' : 'fa-external-link-alt'}"></i>
                                <span>${isVideo ? 'Watch Video Now' : 'View Content'}</span>
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        resultsHTML += '</div>';
        trendingResultsContainer.innerHTML = resultsHTML;
    } else {
        trendingResultsContainer.innerHTML = `
            <div class="empty-results">
                <i class="fas fa-search"></i>
                <h3 style="color: #fff;">No trends found</h3>
                <p>Try a different keyword or platform</p>
            </div>
        `;
    }
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(message) {
    trendingResultsContainer.innerHTML = `
        <div class="empty-results">
            <i class="fas fa-exclamation-triangle" style="color: #ff3333;"></i>
            <h3 style="color: #fff;">Error</h3>
            <p style="color: #ff5555;">${escapeHtml(message)}</p>
        </div>
    `;
    resultsSection.style.display = 'block';
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

