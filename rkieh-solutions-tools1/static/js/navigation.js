// Navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Display network info banner (optional, non-blocking)
    try {
        displayNetworkInfo();
    } catch (e) {
        console.log('Network banner disabled:', e);
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only handle if it's a valid anchor (starts with # and has more than just #)
            if (href && href.startsWith('#') && href.length > 1) {
                try {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                } catch (err) {
                    // Invalid selector, ignore
                }
            }
        });
    });
    
    // Add scroll effect to navbar
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
});

// Display Network Info Banner
async function displayNetworkInfo() {
    try {
        const response = await fetch('/api/server-info');
        const data = await response.json();
        
        if (data.success) {
            // Check if IP changed from localStorage
            const savedIP = localStorage.getItem('server_ip');
            const currentIP = data.local_ip;
            
            // Create or update network banner
            let banner = document.getElementById('network-info-banner');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'network-info-banner';
                banner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    font-size: 14px;
                    font-weight: 500;
                    z-index: 999999;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 20px;
                    flex-wrap: wrap;
                `;
                document.body.insertBefore(banner, document.body.firstChild);
                
                // Adjust body padding to prevent content from being hidden
                document.body.style.paddingTop = '50px';
            }
            
            // Show IP change notification if changed
            if (savedIP && savedIP !== currentIP) {
                banner.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 18px; animation: pulse 1.5s infinite;"></i>
                        <span><strong>⚠️ Network IP Changed!</strong></span>
                    </div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
                        <span><strong>Old:</strong> ${savedIP}</span>
                        <span style="font-size: 20px;">→</span>
                        <span><strong>New:</strong> ${currentIP}</span>
                    </div>
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <span><strong>🌐 Access:</strong> <a href="${data.network_url}" style="color: #fff; text-decoration: underline;">${data.network_url}</a></span>
                        <button onclick="acknowledgeIPChange('${currentIP}')" style="background: rgba(255,255,255,0.2); border: 1px solid white; padding: 5px 15px; border-radius: 5px; color: white; cursor: pointer; font-weight: bold;">Got it!</button>
                    </div>
                `;
                
                // Add pulse animation
                const style = document.createElement('style');
                style.innerHTML = `
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.5; }
                    }
                `;
                document.head.appendChild(style);
            } else {
                // Normal display
                banner.innerHTML = `
                    <div style="display: flex; gap: 30px; align-items: center; flex-wrap: wrap; justify-content: center;">
                        <span><i class="fas fa-server"></i> <strong>Server Running</strong></span>
                        <span><i class="fas fa-network-wired"></i> <strong>Network:</strong> ${currentIP}:5001</span>
                        <span><i class="fas fa-link"></i> <strong>Local:</strong> localhost:5001</span>
                        <button onclick="closeNetworkBanner()" style="background: rgba(255,255,255,0.2); border: none; padding: 5px 10px; border-radius: 5px; color: white; cursor: pointer;">✕</button>
                    </div>
                `;
            }
            
            // Save current IP
            localStorage.setItem('server_ip', currentIP);
        }
    } catch (error) {
        console.log('Could not fetch network info:', error);
    }
}

// Acknowledge IP change
function acknowledgeIPChange(newIP) {
    localStorage.setItem('server_ip', newIP);
    displayNetworkInfo(); // Refresh to show normal view
}

// Close network banner
function closeNetworkBanner() {
    const banner = document.getElementById('network-info-banner');
    if (banner) {
        banner.style.display = 'none';
        document.body.style.paddingTop = '0';
    }
}

