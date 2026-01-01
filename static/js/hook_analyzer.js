// Hook Analyzer - JavaScript

let selectedPlatform = 'tiktok';

const platformOptions = document.querySelectorAll('.platform-option');
const hookInput = document.getElementById('hook-input');
const charCount = document.getElementById('char-count');
const analyzeBtn = document.getElementById('analyze-btn');
const resultsSection = document.getElementById('results-section');
const scoreCircle = document.getElementById('score-circle');
const scoreValue = document.getElementById('score-value');
const scoreLabel = document.getElementById('score-label');
const scoreDescription = document.getElementById('score-description');
const analysisDetails = document.getElementById('analysis-details');
const suggestionsSection = document.getElementById('suggestions-section');
const examplesSection = document.getElementById('examples-section');

// Platform selection
platformOptions.forEach(option => {
    option.addEventListener('click', () => {
        platformOptions.forEach(o => o.classList.remove('active'));
        option.classList.add('active');
        selectedPlatform = option.dataset.platform;
    });
});

// Character count
hookInput.addEventListener('input', () => {
    charCount.textContent = hookInput.value.length;
});

// Analyze hook
analyzeBtn.addEventListener('click', () => {
    const hook = hookInput.value.trim();
    
    if (!hook) {
        alert('Please enter your hook/opening line');
        return;
    }
    
    analyzeHook(hook, selectedPlatform);
});

function analyzeHook(hook, platform) {
    // Show loading
    resultsSection.classList.add('show');
    scoreCircle.className = 'score-circle';
    scoreValue.textContent = '...';
    scoreLabel.textContent = 'Analyzing...';
    scoreDescription.textContent = 'Please wait';
    analysisDetails.innerHTML = '';
    suggestionsSection.innerHTML = '';
    examplesSection.innerHTML = '';
    
    // Send to backend for analysis
    fetch('/analyze-hook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            hook: hook,
            platform: platform
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayResults(data);
        } else {
            alert('Analysis failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}

function displayResults(data) {
    const score = data.overall_score;
    const category = getScoreCategory(score);
    
    // Update score display
    scoreValue.textContent = score;
    scoreCircle.className = `score-circle ${category}`;
    scoreLabel.textContent = data.overall_label;
    scoreDescription.textContent = data.overall_description;
    
    // Display analysis details
    let detailsHTML = '';
    data.details.forEach(detail => {
        const detailCategory = getScoreCategory(detail.score);
        detailsHTML += `
            <div class="detail-card">
                <h3>
                    <i class="${detail.icon}"></i>
                    ${detail.name}
                </h3>
                <div class="score" style="color: ${getScoreColor(detail.score)}">
                    ${detail.score}/100
                </div>
                <div class="description">
                    ${detail.description}
                </div>
            </div>
        `;
    });
    analysisDetails.innerHTML = detailsHTML;
    
    // Display suggestions
    if (data.suggestions && data.suggestions.length > 0) {
        let suggestionsHTML = `
            <h3>
                <i class="fas fa-lightbulb"></i>
                Suggestions to Improve Your Hook
            </h3>
            <ul>
        `;
        data.suggestions.forEach(suggestion => {
            suggestionsHTML += `<li>${suggestion}</li>`;
        });
        suggestionsHTML += '</ul>';
        suggestionsSection.innerHTML = suggestionsHTML;
    }
    
    // Display examples
    if (data.examples && data.examples.length > 0) {
        let examplesHTML = `
            <h3>
                <i class="fas fa-star"></i>
                Strong Hook Examples for ${data.platform.charAt(0).toUpperCase() + data.platform.slice(1)}
            </h3>
        `;
        data.examples.forEach(example => {
            examplesHTML += `
                <div class="example-item">
                    <strong>${example.title}</strong>
                    <span>${example.text}</span>
                </div>
            `;
        });
        examplesSection.innerHTML = examplesHTML;
    }
    
    // Display alternatives (NEW!)
    if (data.alternatives && data.alternatives.length > 0) {
        let alternativesHTML = `
            <div style="background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05)); border: 2px solid #4CAF50; border-radius: 16px; padding: 25px; margin-top: 30px;">
                <h3 style="color: #4CAF50; font-size: 22px; margin-bottom: 20px;">
                    <i class="fas fa-magic"></i>
                    ✨ Improved Versions of Your Hook
                </h3>
        `;
        data.alternatives.forEach((alt, index) => {
            alternativesHTML += `
                <div style="background: rgba(0, 0, 0, 0.3); border-left: 4px solid #4CAF50; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                    <div style="color: #4CAF50; font-weight: 700; margin-bottom: 8px;">
                        ${index + 1}. ${alt.title}
                    </div>
                    <div style="color: #fff; font-size: 16px; margin-bottom: 8px; padding: 10px; background: rgba(76, 175, 80, 0.1); border-radius: 6px;">
                        "${alt.hook}"
                    </div>
                    <div style="color: #aaa; font-size: 13px;">
                        💡 ${alt.why}
                    </div>
                </div>
            `;
        });
        alternativesHTML += '</div>';
        examplesSection.innerHTML += alternativesHTML;
    }
    
    // Display viral templates (NEW!)
    if (data.viral_templates && data.viral_templates.length > 0) {
        let templatesHTML = `
            <div style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(255, 152, 0, 0.05)); border: 2px solid #FF9800; border-radius: 16px; padding: 25px; margin-top: 30px;">
                <h3 style="color: #FF9800; font-size: 22px; margin-bottom: 20px;">
                    <i class="fas fa-fire"></i>
                    🔥 Viral Hook Templates (Copy & Customize)
                </h3>
        `;
        data.viral_templates.forEach((template, index) => {
            templatesHTML += `
                <div style="background: rgba(0, 0, 0, 0.3); border-left: 4px solid #FF9800; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #FF9800; font-weight: 700;">
                            Template ${index + 1}
                        </div>
                        <div style="padding: 3px 12px; background: #FF9800; color: #000; border-radius: 12px; font-size: 11px; font-weight: 700;">
                            ${template.viral_score} Viral Score
                        </div>
                    </div>
                    <div style="color: #fff; font-size: 14px; margin-bottom: 8px; font-family: monospace; background: rgba(0, 0, 0, 0.4); padding: 10px; border-radius: 6px;">
                        ${template.template}
                    </div>
                    <div style="color: #aaa; font-size: 13px;">
                        📝 Example: "${template.example}"
                    </div>
                </div>
            `;
        });
        templatesHTML += '</div>';
        examplesSection.innerHTML += templatesHTML;
    }
    
    // Display A/B test ideas (NEW!)
    if (data.ab_tests && data.ab_tests.length > 0) {
        let abTestsHTML = `
            <div style="background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(156, 39, 176, 0.05)); border: 2px solid #9C27B0; border-radius: 16px; padding: 25px; margin-top: 30px;">
                <h3 style="color: #9C27B0; font-size: 22px; margin-bottom: 20px;">
                    <i class="fas fa-flask"></i>
                    🧪 A/B Testing Ideas
                </h3>
                <p style="color: #aaa; font-size: 14px; margin-bottom: 20px;">
                    Test these variations to find what works best with your audience
                </p>
        `;
        data.ab_tests.forEach((test, index) => {
            abTestsHTML += `
                <div style="background: rgba(0, 0, 0, 0.3); border-left: 4px solid #9C27B0; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                    <div style="color: #9C27B0; font-weight: 700; margin-bottom: 12px;">
                        Test ${index + 1}: ${test.test_name}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="color: #888; font-size: 12px; margin-bottom: 4px;">Version A:</div>
                        <div style="color: #fff; font-size: 14px; padding: 8px; background: rgba(156, 39, 176, 0.1); border-radius: 6px;">
                            "${test.version_a}"
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="color: #888; font-size: 12px; margin-bottom: 4px;">Version B:</div>
                        <div style="color: #fff; font-size: 14px; padding: 8px; background: rgba(156, 39, 176, 0.1); border-radius: 6px;">
                            "${test.version_b}"
                        </div>
                    </div>
                    <div style="color: #aaa; font-size: 13px;">
                        📊 Measure: ${test.what_to_measure}
                    </div>
                </div>
            `;
        });
        abTestsHTML += '</div>';
        examplesSection.innerHTML += abTestsHTML;
    }
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function getScoreCategory(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
}

function getScoreColor(score) {
    if (score >= 80) return '#55ff55';
    if (score >= 60) return '#ffaa00';
    if (score >= 40) return '#ffaa00';
    return '#ff5555';
}

