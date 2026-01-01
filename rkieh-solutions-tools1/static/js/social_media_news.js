// Social Media News Search - JavaScript

const searchInput = document.getElementById('search-name');
const searchBtn = document.getElementById('search-btn');
const statsSection = document.getElementById('stats-section');
const resultsSection = document.getElementById('results-section');
const repeatedNewsSection = document.getElementById('repeated-news-section');
const emptySection = document.getElementById('empty-section');
const summaryStats = document.getElementById('summary-stats');
const resultsContainer = document.getElementById('results-container');
const repeatedNewsContainer = document.getElementById('repeated-news-container');

let allNewsData = null;
let currentFilter = 'all';

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
        alert('Please enter a name to search for news');
        return;
    }
    
    // Show loading
    emptySection.style.display = 'none';
    statsSection.style.display = 'none';
    repeatedNewsSection.style.display = 'none';
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner"></i>
            <p>Searching for news about "${searchTerm}" across all platforms...</p>
        </div>
    `;
    
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
    
    // Send to backend
    fetch('/search-social-media-news', {
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
            allNewsData = data.news; // Store all news data
            displayResults(data);
        } else {
            showError(data.error || 'Failed to search for news');
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
                <div class="stat-value">${data.stats.total_articles || 0}</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.platforms_found || 0}</div>
                <div class="stat-label">Platforms Found</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.total_engagement || '0'}</div>
                <div class="stat-label">Total Engagement</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.trending_count || 0}</div>
                <div class="stat-label">Trending News</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${data.stats.most_repeated_count || 0}</div>
                <div class="stat-label">Most Repeated</div>
            </div>
        `;
    }
    
    // Define platform icons and colors (needed for both sections)
    const platformConfig = {
        'twitter': { icon: 'fab fa-twitter', color: '#1DA1F2', name: 'Twitter/X' },
        'instagram': { icon: 'fab fa-instagram', color: '#E4405F', name: 'Instagram' },
        'tiktok': { icon: 'fab fa-tiktok', color: '#000000', name: 'TikTok' },
        'youtube': { icon: 'fab fa-youtube', color: '#FF0000', name: 'YouTube' },
        'facebook': { icon: 'fab fa-facebook', color: '#1877F2', name: 'Facebook' },
        'reddit': { icon: 'fab fa-reddit', color: '#FF4500', name: 'Reddit' },
        'linkedin': { icon: 'fab fa-linkedin', color: '#0077B5', name: 'LinkedIn' },
        'cnn': { icon: 'fas fa-tv', color: '#CC0000', name: 'CNN' },
        'bbc': { icon: 'fas fa-broadcast-tower', color: '#BB1919', name: 'BBC News' },
        'reuters': { icon: 'fas fa-newspaper', color: '#FF8000', name: 'Reuters' },
        'guardian': { icon: 'fas fa-newspaper', color: '#052962', name: 'The Guardian' },
        'forbes': { icon: 'fas fa-chart-line', color: '#000000', name: 'Forbes' },
        'techcrunch': { icon: 'fas fa-laptop-code', color: '#00A562', name: 'TechCrunch' },
        'nytimes': { icon: 'fas fa-newspaper', color: '#000000', name: 'The New York Times' },
        'washingtonpost': { icon: 'fas fa-newspaper', color: '#231F20', name: 'The Washington Post' },
        'ap': { icon: 'fas fa-newspaper', color: '#000000', name: 'Associated Press' },
        'bloomberg': { icon: 'fas fa-chart-bar', color: '#000000', name: 'Bloomberg' },
        'espn': { icon: 'fas fa-football-ball', color: '#000000', name: 'ESPN' }
    };
    
    // Display repeated news in dedicated section
    if (data.trending_repeated && data.trending_repeated.length > 0) {
        repeatedNewsSection.style.display = 'block';
        displayRepeatedNews(data.trending_repeated, platformConfig);
    } else {
        repeatedNewsSection.style.display = 'none';
    }
    
    // Display trending repeated news section first
    if (data.trending_repeated && data.trending_repeated.length > 0) {
        let trendingHTML = `
            <div class="trending-repeated-section" style="background: linear-gradient(135deg, #2a1a1a 0%, #1a1a2a 100%); border-radius: 16px; padding: 30px; margin-bottom: 30px; border: 3px solid #ff3333; box-shadow: 0 8px 32px rgba(255, 51, 51, 0.3);">
                <div style="display: flex; align-items: center; margin-bottom: 25px;">
                    <i class="fas fa-fire" style="font-size: 32px; color: #ff3333; margin-right: 15px;"></i>
                    <h2 style="color: #fff; margin: 0; font-size: 28px;">🔥 Trending News Across Multiple Platforms</h2>
                </div>
                <p style="color: #aaa; margin-bottom: 20px; font-size: 14px;">These trending news articles appear on multiple platforms:</p>
        `;
        
        data.trending_repeated.forEach((article, index) => {
            const platformNames = article.platforms.map(p => {
                // Handle both object format {name: "platform"} and string format "platform"
                let platformName = '';
                if (typeof p === 'object' && p !== null) {
                    platformName = p.name ? String(p.name) : '';
                } else if (p) {
                    platformName = String(p);
                }
                
                if (!platformName) return ''; // Skip empty platforms
                
                const platformKey = platformName.toLowerCase();
                const config = platformConfig[platformKey] || { name: platformName, icon: 'fas fa-globe', color: '#ff3333' };
                return `<span style="display: inline-block; padding: 4px 12px; margin: 4px; background: ${config.color}22; color: ${config.color}; border-radius: 8px; font-size: 12px; font-weight: 600;"><i class="${config.icon}" style="margin-right: 5px;"></i>${config.name}</span>`;
            }).filter(html => html).join(''); // Filter out empty strings
            
            trendingHTML += `
                <div class="trending-repeated-item" style="background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%); border-radius: 12px; padding: 20px; margin-bottom: 15px; border: 2px solid #ff3333; transition: all 0.3s;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                        <div style="flex: 1;">
                            <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 20px;">
                                ${escapeHtml(article.title || article.headline)}
                                ${article.is_breaking ? '<span style="background: #ff0000; color: #fff; padding: 4px 10px; border-radius: 8px; font-size: 11px; margin-left: 10px; font-weight: 600;">⚡ Breaking</span>' : ''}
                                <span style="background: #00ff00; color: #000; padding: 4px 10px; border-radius: 8px; font-size: 11px; margin-left: 10px; font-weight: bold;">⭐ Appears on ${article.repetition_count} Platform${article.repetition_count !== 1 ? 's' : ''}</span>
                            </h3>
                            <p style="color: #aaa; margin: 0; font-size: 14px; line-height: 1.6;">${escapeHtml(article.content || article.headline || '')}</p>
                        </div>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <div style="color: #fff; font-size: 12px; margin-bottom: 8px; font-weight: 600;">📰 Appears on:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${platformNames}
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #aaa; font-size: 12px;">
                            <i class="fas fa-chart-line" style="color: #ff3333; margin-right: 5px;"></i>
                            Total Engagement: ${formatNumber(article.total_engagement)}
                        </div>
                        ${article.url ? `<a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer" class="news-link" style="padding: 8px 16px; font-size: 13px;"><i class="fas fa-external-link-alt"></i> Read Full Article</a>` : ''}
                    </div>
                </div>
            `;
        });
        
        trendingHTML += '</div>';
        resultsContainer.innerHTML = trendingHTML;
    }
    
    // Display news results by platform
    if (data.news && Object.keys(data.news).length > 0) {
        let resultsHTML = resultsContainer.innerHTML || '';
        
        for (const [platform, articles] of Object.entries(data.news)) {
            if (articles && articles.length > 0) {
                // Ensure platform is a string
                const platformKey = String(platform || '').toLowerCase();
                const platformName = String(platform || '');
                const config = platformConfig[platformKey] || { icon: 'fas fa-globe', color: '#ff3333', name: platformName };
                
                resultsHTML += `
                    <div class="platform-news">
                        <div class="platform-header" style="background: linear-gradient(135deg, ${config.color}22 0%, ${config.color}11 100%); border-color: ${config.color}44;">
                            <div class="platform-icon" style="background: linear-gradient(135deg, ${config.color} 0%, ${config.color}dd 100%);">
                                <i class="${config.icon}" style="color: #fff;"></i>
                            </div>
                            <div class="platform-info">
                                <div class="platform-name">${config.name}</div>
                                <div class="platform-count">${articles.length} article${articles.length !== 1 ? 's' : ''} found</div>
                            </div>
                        </div>
                        ${articles.map(article => `
                            <div class="news-item" style="${article.is_most_repeated ? 'border: 3px solid #00ff00; box-shadow: 0 0 20px rgba(0, 255, 0, 0.3); background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%);' : article.is_repeated ? 'border: 2px solid #ffaa00; background: linear-gradient(135deg, #2a2a1a 0%, #3a3a2a 100%);' : ''}">
                                <div class="news-source">
                                    <div class="source-avatar">${getInitials(article.source_name || article.author || 'News')}</div>
                                    <div class="source-info">
                                        <div class="source-name">
                                            ${escapeHtml(article.source_name || article.author || 'Unknown Source')}
                                            ${article.verified ? '<i class="fas fa-check-circle" style="color: #1DA1F2; font-size: 16px; margin-left: 8px;"></i>' : ''}
                                        </div>
                                        <div class="source-handle">@${escapeHtml(article.source_handle || article.author_handle || 'unknown')}</div>
                                    </div>
                                    <div class="news-time">${article.time_ago || 'Recently'}</div>
                                </div>
                                <div class="news-title">
                                    ${escapeHtml(article.title || article.headline || 'News Article')}
                                    ${article.trending ? '<span class="news-badge">🔥 Trending</span>' : ''}
                                    ${article.breaking ? '<span class="news-badge" style="background: #ff0000;">⚡ Breaking</span>' : ''}
                                    ${article.is_most_repeated ? '<span class="news-badge" style="background: #00ff00; color: #000; font-weight: bold;">⭐ Most Repeated (${article.repetition_count}x)</span>' : ''}
                                    ${article.is_repeated && !article.is_most_repeated ? `<span class="news-badge" style="background: #ffaa00; color: #000;">📰 Repeated (${article.repetition_count}x)</span>` : ''}
                                </div>
                                <div class="news-content">${escapeHtml(article.content || article.description || article.summary || '')}</div>
                                <div class="news-stats">
                                    ${article.likes ? `<div class="stat-item"><i class="fas fa-heart"></i> ${formatNumber(article.likes)}</div>` : ''}
                                    ${article.shares ? `<div class="stat-item"><i class="fas fa-share"></i> ${formatNumber(article.shares)}</div>` : ''}
                                    ${article.comments ? `<div class="stat-item"><i class="fas fa-comments"></i> ${formatNumber(article.comments)}</div>` : ''}
                                    ${article.views ? `<div class="stat-item"><i class="fas fa-eye"></i> ${formatNumber(article.views)}</div>` : ''}
                                </div>
                                ${article.url ? `<a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer" class="news-link"><i class="fas fa-external-link-alt"></i> Read Full Article</a>` : ''}
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        }
        
        if (data.trending_repeated && data.trending_repeated.length > 0) {
            resultsContainer.innerHTML = resultsContainer.innerHTML + resultsHTML;
        } else {
            resultsContainer.innerHTML = resultsHTML;
        }
    } else {
        resultsContainer.innerHTML = `
            <div class="empty-results">
                <i class="fas fa-newspaper"></i>
                <h3 style="color: #fff;">No news found</h3>
                <p>Try a different search term or check the spelling</p>
            </div>
        `;
    }
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Setup filter buttons
    setupFilters();
}

function setupFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            filterButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            // Update current filter
            currentFilter = btn.dataset.filter;
            // Apply filter
            applyFilter();
        });
    });
}

function applyFilter() {
    if (!allNewsData) return;
    
    let filteredNews = {};
    
    for (const [platform, articles] of Object.entries(allNewsData)) {
        let filteredArticles = articles;
        
        if (currentFilter === 'verified') {
            filteredArticles = articles.filter(article => article.verified === true);
        } else if (currentFilter === 'non-verified') {
            filteredArticles = articles.filter(article => article.verified === false || !article.verified);
        }
        // If filter is 'all', keep all articles
        
        if (filteredArticles.length > 0) {
            filteredNews[platform] = filteredArticles;
        }
    }
    
    // Re-display with filtered data
    displayResults({
        success: true,
        news: filteredNews,
        stats: calculate_news_stats(filteredNews)
    });
}

function calculate_news_stats(news_results) {
    let total_articles = 0;
    let platforms_found = 0;
    let total_engagement = 0;
    let trending_count = 0;
    
    for (const articles of Object.values(news_results)) {
        if (articles && articles.length > 0) {
            total_articles += articles.length;
            platforms_found++;
            for (const article of articles) {
                total_engagement += (article.likes || 0) + (article.shares || 0) + (article.comments || 0);
                if (article.trending) {
                    trending_count++;
                }
            }
        }
    }
    
    // Format engagement number
    let formatted_engagement = total_engagement;
    if (total_engagement >= 1000000) {
        formatted_engagement = (total_engagement / 1000000).toFixed(1) + 'M';
    } else if (total_engagement >= 1000) {
        formatted_engagement = (total_engagement / 1000).toFixed(1) + 'K';
    } else {
        formatted_engagement = total_engagement.toString();
    }
    
    return {
        total_articles: total_articles,
        platforms_found: platforms_found,
        total_engagement: formatted_engagement,
        trending_count: trending_count
    };
}

function displayRepeatedNews(repeatedNews, platformConfig) {
    if (!repeatedNews || repeatedNews.length === 0) {
        repeatedNewsContainer.innerHTML = '<p style="color: #888; text-align: center;">No repeated news found.</p>';
        return;
    }
    
    let html = `
        <table class="repeated-news-table">
            <thead>
                <tr>
                    <th style="width: 50px; text-align: center;">#</th>
                    <th style="width: 40%;">News Title</th>
                    <th style="width: 100px; text-align: center;">Sources</th>
                    <th style="width: 30%;">Reported By</th>
                    <th style="width: 150px; text-align: center;">Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    repeatedNews.forEach((item, index) => {
        const platforms = item.platforms || [];
        const repeatCount = item.repeat_count || platforms.length;
        
        // Build sources badges
        const sourceBadges = platforms.map(platform => {
            let platformName = '';
            if (typeof platform === 'object' && platform !== null) {
                platformName = platform.name ? String(platform.name) : '';
            } else if (platform) {
                platformName = String(platform);
            }
            
            if (!platformName) return '';
            
            const platformKey = platformName.toLowerCase();
            const config = platformConfig[platformKey] || { name: platformName, icon: 'fas fa-newspaper', color: '#888' };
            return `<span class="source-badge">
                <i class="${config.icon}" style="color: ${config.color};"></i> ${config.name}
            </span>`;
        }).filter(html => html).join('');
        
        html += `
            <tr>
                <td style="text-align: center; color: #ff3333; font-weight: 700; font-size: 18px;">
                    ${index + 1}
                </td>
                <td>
                    <div class="table-title">
                        ${item.breaking ? '🔴 ' : ''}${item.trending ? '🔥 ' : ''}
                        ${escapeHtml(item.title)}
                    </div>
                    <div class="table-content">
                        ${escapeHtml((item.content || item.headline || '').substring(0, 150))}${(item.content || '').length > 150 ? '...' : ''}
                    </div>
                    ${item.time_ago ? `<div style="margin-top: 8px; color: #888; font-size: 12px;">
                        <i class="fas fa-clock"></i> ${escapeHtml(item.time_ago)}
                    </div>` : ''}
                </td>
                <td style="text-align: center;">
                    <span class="table-count-badge">
                        ${repeatCount}
                    </span>
                </td>
                <td>
                    <div class="table-sources-list">
                        ${sourceBadges}
                    </div>
                </td>
                <td style="text-align: center;">
                    ${item.url ? `<a href="${item.url}" target="_blank" class="news-link" style="display: inline-block; padding: 8px 16px; font-size: 13px;">
                        <i class="fas fa-external-link-alt"></i> Read
                    </a>` : '<span style="color: #666;">No link</span>'}
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    repeatedNewsContainer.innerHTML = html;
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

