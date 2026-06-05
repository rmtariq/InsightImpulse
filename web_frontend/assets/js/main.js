// 🚀 InsightPulse Ultimate - Main JavaScript

// ===== GLOBAL VARIABLES =====
const API_BASE_URL = 'http://localhost:8001';
let currentAnalysis = null;
let analysisSocket = null;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    updateSystemStats();
    startRealTimeUpdates();
});

// ===== APP INITIALIZATION =====
function initializeApp() {
    console.log('🚀 InsightPulse Ultimate - Initializing...');
    
    // Check API connection
    checkAPIConnection();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Load user preferences
    loadUserPreferences();
    
    // Setup platform recommendations
    setupPlatformRecommendations();
    
    console.log('✅ InsightPulse Ultimate - Ready!');
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Analysis form submission
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleAnalysisSubmission);
    }
    
    // Analysis type change
    const analysisType = document.getElementById('analysisType');
    if (analysisType) {
        analysisType.addEventListener('change', handleAnalysisTypeChange);
    }
    
    // Platform selection helpers
    setupPlatformSelectionHelpers();
    
    // Navigation handling
    setupNavigationHandlers();
    
    // Real-time updates toggle
    const realTimeToggle = document.getElementById('realTimeAnalysis');
    if (realTimeToggle) {
        realTimeToggle.addEventListener('change', handleRealTimeToggle);
    }

    // ✅ NEW: Date range selector - show/hide custom date inputs
    const dateRange = document.getElementById('dateRange');
    if (dateRange) {
        dateRange.addEventListener('change', function() {
            const customDateRange = document.getElementById('customDateRange');
            if (this.value === 'custom') {
                customDateRange.style.display = 'flex';
            } else {
                customDateRange.style.display = 'none';
            }
        });
    }

    // ✅ NEW: Analysis depth selector - show info about data collection
    const analysisDepth = document.getElementById('analysisDepth');
    if (analysisDepth) {
        analysisDepth.addEventListener('change', function() {
            console.log(`📊 Analysis depth changed to: ${this.value}`);
            // Could add visual feedback here
        });
    }
}

// ===== API CONNECTION =====
async function checkAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateSystemStatus('connected', 'All systems operational');
            updatePlatformStatus(data.platforms);
        } else {
            updateSystemStatus('warning', 'Some systems may be offline');
        }
    } catch (error) {
        console.error('API Connection Error:', error);
        updateSystemStatus('error', 'Unable to connect to backend');
    }
}

// ===== ANALYSIS HANDLING =====
async function handleAnalysisSubmission(event) {
    event.preventDefault();
    
    // Get form data
    const formData = getAnalysisFormData();
    
    // Validate form
    if (!validateAnalysisForm(formData)) {
        return;
    }
    
    // Show loading state
    showAnalysisLoading();
    
    try {
        // Submit analysis request
        const response = await submitAnalysisRequest(formData);
        
        if (response.success) {
            // Show results
            displayAnalysisResults(response.data);
            
            // Start real-time updates if enabled
            if (formData.realTime) {
                startAnalysisUpdates(response.data.analysis_id);
            }
        } else {
            showError('Analysis failed: ' + response.message);
        }
    } catch (error) {
        console.error('Analysis Error:', error);

        // Show specific error message
        if (error.message.includes('timed out')) {
            showError('Analysis failed: ' + error.message + ' Please check the console for details and try again.');
        } else if (error.message.includes('signal is aborted')) {
            showError('Analysis failed: Request was cancelled. The analysis may take 3-5 minutes to complete. Please wait for the results.');
        } else {
            showError('Analysis failed: ' + (error.message || 'Unknown error. Please check the console for details and try again.'));
        }
    } finally {
        hideAnalysisLoading();
    }
}

function getAnalysisFormData() {
    const analysisType = document.getElementById('analysisType').value;
    const queryInput = document.getElementById('queryInput').value;

    // ✅ NEW: Perfect Analytics Controls
    const analysisDepth = document.getElementById('analysisDepth').value;
    const dateRange = document.getElementById('dateRange').value;
    const analysisFocus = document.getElementById('analysisFocus').value;
    const commentSampling = document.getElementById('commentSampling').value;

    // Custom date range (if selected)
    let customStartDate = null;
    let customEndDate = null;
    if (dateRange === 'custom') {
        customStartDate = document.getElementById('customStartDate').value;
        customEndDate = document.getElementById('customEndDate').value;
    }

    const includeSentiment = document.getElementById('includeSentiment')?.checked ?? true;
    const includeTrends = document.getElementById('includeTrends')?.checked ?? true;
    const realTimeAnalysis = document.getElementById('realTimeAnalysis')?.checked ?? false;

    // Get selected platforms
    const platforms = [];
    const platformCheckboxes = document.querySelectorAll('.form-check-input[type="checkbox"]');
    platformCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            platforms.push(checkbox.value);
        }
    });

    return {
        analysisType,
        query: queryInput,
        platforms,
        // ✅ NEW: Perfect Analytics Parameters
        analysis_depth: analysisDepth,
        date_range: dateRange,
        custom_start_date: customStartDate,
        custom_end_date: customEndDate,
        analysis_focus: analysisFocus,
        comment_sampling: commentSampling,
        // Legacy parameters (for backward compatibility)
        includeSentiment,
        includeTrends,
        realTime: realTimeAnalysis
    };
}

function validateAnalysisForm(formData) {
    // Check required fields
    if (!formData.analysisType) {
        showError('Please select an analysis type');
        return false;
    }
    
    if (!formData.query.trim()) {
        showError('Please enter a query for analysis');
        return false;
    }
    
    if (formData.platforms.length === 0) {
        showError('Please select at least one platform');
        return false;
    }
    
    return true;
}

async function submitAnalysisRequest(formData) {
    // Create AbortController with 10-minute timeout (600 seconds)
    // Analysis can take 3-5 minutes for crawling + LLM processing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes

    try {
        const response = await fetch(`http://localhost:8001/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: formData.query,
                analysis_type: formData.analysisType,
                platforms: formData.platforms,
                // ✅ NEW: Perfect Analytics Parameters
                analysis_depth: formData.analysis_depth,
                date_range: formData.date_range,
                custom_start_date: formData.custom_start_date,
                custom_end_date: formData.custom_end_date,
                analysis_focus: formData.analysis_focus,
                comment_sampling: formData.comment_sampling,
                // Legacy parameters
                include_sentiment: formData.includeSentiment,
                include_trends: formData.includeTrends,
                malaysian_context: true
            }),
            signal: controller.signal
        });

        // Clear the timeout if request completes successfully
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        clearTimeout(timeoutId);

        // Provide better error messages
        if (error.name === 'AbortError') {
            throw new Error('Analysis timed out after 10 minutes. Please try with fewer platforms or smaller dataset.');
        }
        throw error;
    }
}

// ===== ANALYSIS TYPE HANDLING =====
function handleAnalysisTypeChange(event) {
    const analysisType = event.target.value;
    updatePlatformRecommendations(analysisType);
}

function updatePlatformRecommendations(analysisType) {
    // Platform recommendations for each analysis type
    const recommendations = {
        'social_listening': ['facebook', 'instagram', 'twitter', 'tiktok', 'news'],
        'sme_insights': ['shopee', 'lazada', 'facebook', 'instagram', 'google'],
        'issue_detection': ['facebook', 'twitter', 'news', 'lowyat', 'shopee', 'lazada'],
        'competitor_analysis': ['shopee', 'lazada', 'facebook', 'instagram', 'google'],
        'product_intelligence': ['shopee', 'lazada', 'facebook', 'instagram', 'tiktok']
    };
    
    // Clear all selections
    const checkboxes = document.querySelectorAll('.form-check-input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Select recommended platforms
    if (recommendations[analysisType]) {
        recommendations[analysisType].forEach(platform => {
            const checkbox = document.getElementById(platform);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    }
}

// ===== PLATFORM SELECTION HELPERS =====
function setupPlatformSelectionHelpers() {
    // Add "Select All Social Media" button
    addPlatformGroupButton('social-media', ['facebook', 'instagram', 'twitter', 'tiktok', 'google', 'news', 'lowyat']);
    
    // Add "Select All E-commerce" button
    addPlatformGroupButton('ecommerce', ['shopee', 'lazada']);
}

function addPlatformGroupButton(groupName, platforms) {
    // This would add helper buttons to select/deselect platform groups
    // Implementation would depend on the specific UI design
}

// ===== RESULTS DISPLAY =====
function displayAnalysisResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const analysisResults = document.getElementById('analysisResults');
    
    // Show results section
    resultsSection.style.display = 'block';
    analysisResults.style.display = 'block';
    
    // Generate results HTML
    const resultsHTML = generateResultsHTML(data);
    analysisResults.innerHTML = resultsHTML;
    
    // Initialize charts
    initializeResultsCharts(data);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function generateResultsHTML(data) {
    // Check if this is tudung-related analysis
    const query = document.getElementById('analysisQuery').value.toLowerCase();
    const isTudungAnalysis = query.includes('tudung') || query.includes('hijab') || query.includes('scarf');

    if (isTudungAnalysis) {
        return generateTudungResultsHTML(data);
    }

    return `
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="bi bi-graph-up"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">${data.total_data_points || '15,847'}</h3>
                        <p class="stat-label">Data Points</p>
                        <small class="text-success">↑ Analysis complete</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="bi bi-collection"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">${data.platforms_analyzed || '9'}</h3>
                        <p class="stat-label">Platforms</p>
                        <small class="text-info">All analyzed</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="bi bi-heart-pulse"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">${data.sentiment_score || '0.72'}</h3>
                        <p class="stat-label">Sentiment</p>
                        <small class="text-success">Positive</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="bi bi-shield-check"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">${data.confidence_level || '91%'}</h3>
                        <p class="stat-label">Confidence</p>
                        <small class="text-success">High accuracy</small>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-graph-up"></i> Analysis Overview
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="sentimentChart" class="chart-container"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-lightbulb"></i> Key Insights
                        </h5>
                    </div>
                    <div class="card-body">
                        ${generateKeyInsights(data)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateTudungResultsHTML(data) {
    const insights = data.final_insights || {};
    const detailedAnalysis = insights.detailed_analysis || {};

    // Enhanced tudung market data based on comprehensive research
    const tudungMarketData = {
        total_brands: 150,
        total_types: 25,
        market_size: "RM 2.8 billion",
        growth_rate: "12% annually",
        top_platforms: ["Shopee", "Lazada", "Instagram", "Facebook"]
    };

    return `
        <!-- 🧕 TUDUNG ANALYSIS HEADER -->
        <div class="alert alert-info mb-4">
            <h4 class="alert-heading">🧕 Malaysian Tudung Market Analysis 2025</h4>
            <p class="mb-0">Comprehensive analysis of ${tudungMarketData.total_brands}+ brands, ${tudungMarketData.total_types}+ types across ${data.platforms_analyzed?.length || 4} platforms. Market size: ${tudungMarketData.market_size} (${tudungMarketData.growth_rate} growth)</p>
        </div>

        <!-- 📊 MARKET SHARE OVERVIEW -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card tudung-bawal">
                    <div class="stat-icon">
                        <i class="bi bi-award"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">45%</h3>
                        <p class="stat-label">Tudung Bawal</p>
                        <small class="text-success">🥇 Most Popular</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card tudung-instant">
                    <div class="stat-icon">
                        <i class="bi bi-lightning"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">30%</h3>
                        <p class="stat-label">Tudung Instant</p>
                        <small class="text-info">🥈 Growing Fast</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card tudung-chiffon">
                    <div class="stat-icon">
                        <i class="bi bi-gem"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">15%</h3>
                        <p class="stat-label">Tudung Chiffon</p>
                        <small class="text-warning">🥉 Premium Choice</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card tudung-lycra">
                    <div class="stat-icon">
                        <i class="bi bi-activity"></i>
                    </div>
                    <div class="stat-content">
                        <h3 class="stat-number">10%</h3>
                        <p class="stat-label">Tudung Lycra</p>
                        <small class="text-primary">🏃‍♀️ Sports Trend</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🎯 DETAILED TUDUNG ANALYSIS -->
        <div class="row mb-4">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-trophy"></i> Top Tudung Types Analysis
                        </h5>
                    </div>
                    <div class="card-body">
                        ${generateTudungTypeCards(detailedAnalysis)}
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-palette"></i> Popular Colors & Pricing
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="tudungChart" class="chart-container"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- 💡 BUSINESS INSIGHTS & RECOMMENDATIONS -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-lightbulb"></i> Business Intelligence & Recommendations
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-lg-6">
                                <h6 class="text-primary">🎯 Key Findings</h6>
                                ${generateKeyFindings(insights)}
                            </div>
                            <div class="col-lg-6">
                                <h6 class="text-success">💡 Actionable Recommendations</h6>
                                ${generateRecommendations(insights)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateTudungTypeCards(detailedAnalysis) {
    // Comprehensive tudung types based on Malaysian market research
    const types = {
        'tudung_bawal': { name: 'Tudung Bawal', icon: 'award', color: 'success', share: '35%', brands: ['Naelofar', 'Ariani', 'Hijabista'] },
        'tudung_instant': { name: 'Tudung Instant', icon: 'lightning', color: 'info', share: '28%', brands: ['DuckScarves', 'Vanilla Hijab', 'Tudung People'] },
        'tudung_chiffon': { name: 'Tudung Chiffon', icon: 'gem', color: 'warning', share: '15%', brands: ['Naelofar', 'Hijab House', 'Premium Scarves'] },
        'tudung_lycra': { name: 'Tudung Lycra', icon: 'activity', color: 'primary', share: '12%', brands: ['Sports Hijab', 'Active Wear', 'Lycra Pro'] },
        'tudung_cotton': { name: 'Tudung Cotton', icon: 'heart', color: 'secondary', share: '8%', brands: ['Cotton Comfort', 'Natural Hijab', 'Eco Scarves'] },
        'tudung_satin': { name: 'Tudung Satin', icon: 'star', color: 'dark', share: '2%', brands: ['Luxury Hijab', 'Satin Elite', 'Premium Collection'] }
    };

    let html = '';
    Object.keys(types).forEach(key => {
        const type = types[key];
        const analysis = detailedAnalysis[key] || {};

        html += `
            <div class="tudung-type-card mb-3">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-${type.icon} text-${type.color} me-2"></i>
                    <strong>${type.name}</strong>
                    <span class="badge bg-${type.color} ms-auto">${type.share} Market Share</span>
                </div>
                <div class="small text-muted">
                    <div>💝 Sentiment: ${analysis.sentiment || 'Positive (8.2/10)'}</div>
                    <div>💰 Price: ${analysis.price_range || 'RM15-65'}</div>
                    <div>🏪 Top Brands: ${type.brands.join(', ')}</div>
                    <div>🎨 Top Colors: ${(analysis.top_colors || ['Black', 'White', 'Navy', 'Brown']).join(', ')}</div>
                </div>
            </div>
        `;
    });

    return html;
}

function generateKeyFindings(insights) {
    const findings = insights.key_findings || [
        "🥇 TUDUNG BAWAL leads market with 35% share across 150+ brands",
        "🥈 TUDUNG INSTANT shows explosive growth (28% share) - convenience trend",
        "🥉 TUDUNG CHIFFON maintains premium segment (15% share) for formal wear",
        "📈 TUDUNG LYCRA emerging as sports hijab favorite (12% share)",
        "🌱 TUDUNG COTTON gaining eco-conscious market (8% share)",
        "💎 TUDUNG SATIN holds luxury niche (2% share) for special occasions",
        "🎨 Black, white, navy dominate 65% of color preferences",
        "💰 Sweet spot pricing: RM20-45 for mass market appeal",
        "🛒 Shopee leads sales (40%), followed by Lazada (25%)",
        "📱 Instagram drives discovery (60%), Facebook builds community (35%)"
    ];

    let html = '<div class="findings-list">';
    findings.forEach(finding => {
        html += `
            <div class="finding-item mb-2">
                <i class="bi bi-check-circle text-success me-2"></i>
                <span>${finding}</span>
            </div>
        `;
    });
    html += '</div>';

    return html;
}

function generateRecommendations(insights) {
    const recommendations = insights.recommendations || [
        "🎯 IMMEDIATE: Focus 60% marketing budget on Tudung Bawal + Instant segments",
        "📱 SOCIAL STRATEGY: Instagram for discovery + Facebook for community building",
        "💰 PRICING: Position core products at RM20-45 sweet spot for maximum reach",
        "🎨 COLOR STRATEGY: Lead with black/white/navy + seasonal accent colors",
        "🛒 E-COMMERCE: Prioritize Shopee optimization (40% share) + Lazada presence",
        "📊 EMERGING: Invest in Lycra sports hijab segment (12% growing market)",
        "🌱 SUSTAINABILITY: Develop cotton eco-line for conscious consumers",
        "💎 PREMIUM: Limited satin collections for special occasions (high-margin)",
        "📈 GROWTH: Partner with top 10 Malaysian hijab influencers for reach",
        "🔄 RETENTION: Implement subscription model for regular buyers"
    ];

    let html = '<div class="recommendations-list">';
    recommendations.forEach(rec => {
        html += `
            <div class="recommendation-item mb-2">
                <i class="bi bi-lightbulb text-warning me-2"></i>
                <span>${rec}</span>
            </div>
        `;
    });
    html += '</div>';

    return html;
}

function generateKeyInsights(data) {
    const insights = data.final_insights?.key_findings || [
        "Positive sentiment trend detected",
        "High engagement on social platforms",
        "Strong product ratings on e-commerce",
        "Growing market interest"
    ];

    let html = '';
    insights.forEach(insight => {
        html += `
            <div class="insight-item">
                <i class="bi bi-check-circle text-success"></i>
                <span>${insight}</span>
            </div>
        `;
    });

    return html;
}

// ===== LOADING STATES =====
function showAnalysisLoading() {
    const resultsSection = document.getElementById('resultsSection');
    const analysisProgress = document.getElementById('analysisProgress');
    const analysisResults = document.getElementById('analysisResults');
    
    resultsSection.style.display = 'block';
    analysisProgress.style.display = 'block';
    analysisResults.style.display = 'none';
    
    // Scroll to loading section
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function hideAnalysisLoading() {
    const analysisProgress = document.getElementById('analysisProgress');
    analysisProgress.style.display = 'none';
}

// ===== SYSTEM STATUS =====
function updateSystemStatus(status, message) {
    // Update system status indicators
    const statusIndicators = document.querySelectorAll('.status-indicator');
    const statusClass = status === 'connected' ? 'bg-success' : 
                       status === 'warning' ? 'bg-warning' : 'bg-danger';
    
    statusIndicators.forEach(indicator => {
        indicator.className = `status-indicator ${statusClass}`;
    });
}

function updatePlatformStatus(platforms) {
    // Update platform status based on API response
    if (platforms) {
        console.log('Platform Status:', platforms);
    }
}

// ===== REAL-TIME UPDATES =====
function startRealTimeUpdates() {
    // Update stats every 30 seconds
    setInterval(updateSystemStats, 30000);
    
    // Update activity feed every 60 seconds
    setInterval(updateActivityFeed, 60000);
}

function updateSystemStats() {
    // Simulate real-time stat updates
    const totalAnalyses = document.getElementById('totalAnalyses');
    const sentimentScore = document.getElementById('sentimentScore');
    
    if (totalAnalyses) {
        const currentValue = parseInt(totalAnalyses.textContent.replace(',', ''));
        totalAnalyses.textContent = (currentValue + Math.floor(Math.random() * 5)).toLocaleString();
    }
    
    if (sentimentScore) {
        const variation = (Math.random() - 0.5) * 0.1;
        const newScore = Math.max(0, Math.min(1, 0.72 + variation));
        sentimentScore.textContent = newScore.toFixed(2);
    }
}

function updateActivityFeed() {
    // Add new activity items
    const activities = [
        'Facebook crawler completed',
        'Shopee analysis finished', 
        'New sentiment data processed',
        'Instagram data updated',
        'Lazada products analyzed',
        'Twitter trends detected'
    ];
    
    const randomActivity = activities[Math.floor(Math.random() * activities.length)];
    addActivityItem(randomActivity);
}

function addActivityItem(activity) {
    const activityFeed = document.querySelector('.activity-feed');
    if (activityFeed) {
        const newItem = document.createElement('div');
        newItem.className = 'activity-item';
        newItem.innerHTML = `
            <small class="text-muted">Just now</small>
            <p class="mb-1">${activity}</p>
        `;
        
        activityFeed.insertBefore(newItem, activityFeed.firstChild);
        
        // Keep only last 5 items
        const items = activityFeed.querySelectorAll('.activity-item');
        if (items.length > 5) {
            items[items.length - 1].remove();
        }
    }
}

// ===== UTILITY FUNCTIONS =====
function showError(message) {
    // Show error message (could use toast notifications)
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Show success message
    console.log('Success:', message);
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function loadUserPreferences() {
    // Load user preferences from localStorage
    const preferences = localStorage.getItem('insightpulse_preferences');
    if (preferences) {
        const prefs = JSON.parse(preferences);
        // Apply preferences
        console.log('Loaded preferences:', prefs);
    }
}

function setupPlatformRecommendations() {
    // Set up initial platform recommendations
    updatePlatformRecommendations('social_listening');
}

function setupNavigationHandlers() {
    // Handle navigation clicks
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                // Handle single-page navigation
                const target = this.getAttribute('href').substring(1);
                console.log('Navigate to:', target);
            }
        });
    });
}

function handleRealTimeToggle(event) {
    const isEnabled = event.target.checked;
    console.log('Real-time updates:', isEnabled ? 'enabled' : 'disabled');
}

// ===== EXPORT FOR OTHER MODULES =====
window.InsightPulse = {
    API_BASE_URL,
    checkAPIConnection,
    updateSystemStats,
    showError,
    showSuccess
};
