"""
Report Templates for Professional Report Generation
Contains templates for Communication Plan, Dashboard HTML, and PowerPoint
"""

from datetime import datetime
from typing import Dict, Any, List


def generate_communication_plan_template(
    query: str,
    analysis_type: str,
    analysis_data: Dict[str, Any]
) -> str:
    """Generate public communication plan markdown"""
    
    sentiment = analysis_data.get('sentiment_analysis', {})
    negative_ratio = sentiment.get('negative_ratio', 0)
    
    # Determine crisis level
    if negative_ratio > 50:
        crisis_level = "🔴 HIGH - Immediate action required"
        tone = "Empathetic, Transparent, Action-Oriented"
    elif negative_ratio > 30:
        crisis_level = "🟡 MEDIUM - Proactive response needed"
        tone = "Professional, Reassuring, Solution-Focused"
    else:
        crisis_level = "🟢 LOW - Standard monitoring"
        tone = "Positive, Engaging, Informative"
    
    template = f"""# PUBLIC COMMUNICATION PLAN
## {query}

**Date:** {datetime.now().strftime('%B %d, %Y')}  
**Crisis Level:** {crisis_level}  
**Recommended Tone:** {tone}

---

## 🎯 COMMUNICATION OBJECTIVES

1. **Address Public Concerns** - Acknowledge and respond to key issues
2. **Restore Confidence** - Rebuild trust through transparency
3. **Provide Clarity** - Clear, factual information
4. **Demonstrate Action** - Show concrete steps being taken
5. **Maintain Engagement** - Keep dialogue open

---

## 📢 KEY MESSAGES

### Primary Message
*[Main message addressing the core issue/topic]*

"We hear your concerns and are committed to [specific action]. Our priority is [key value proposition]."

### Supporting Messages
1. **Transparency**: "We are committed to open communication..."
2. **Action**: "We have already taken steps to..."
3. **Commitment**: "Moving forward, we will..."

---

## 🎤 SPOKESPERSON GUIDELINES

### Do's ✅
- Acknowledge concerns empathetically
- Provide specific, factual information
- Show concrete actions being taken
- Maintain calm, professional tone
- Offer clear next steps

### Don'ts ❌
- Make defensive statements
- Provide speculative information
- Over-promise without delivery plan
- Ignore negative feedback
- Use corporate jargon

---

## 📱 PLATFORM-SPECIFIC STRATEGY

### Facebook
- **Approach**: Detailed posts with context
- **Frequency**: 2-3 times daily during crisis
- **Content**: Mix of updates, FAQs, testimonials

### Twitter/X
- **Approach**: Quick updates, thread for details
- **Frequency**: Hourly during active crisis
- **Content**: Brief updates, links to full statements

### Instagram
- **Approach**: Visual storytelling
- **Frequency**: Daily stories, 2-3 posts/week
- **Content**: Behind-the-scenes, human element

### LinkedIn
- **Approach**: Professional, detailed updates
- **Frequency**: 1-2 times weekly
- **Content**: Official statements, thought leadership

---

## 💬 RESPONSE TEMPLATES

### For Negative Comments
```
"Thank you for sharing your concerns. We take this feedback seriously. 
[Specific acknowledgment of issue]. We are [specific action being taken]. 
Please contact us at [contact] for further assistance."
```

### For Questions
```
"Great question! [Direct answer]. For more information, please visit 
[link] or contact our team at [contact]."
```

### For Positive Feedback
```
"Thank you for your support! We're committed to [value proposition] 
and appreciate customers like you."
```

---

## ⏰ COMMUNICATION TIMELINE

### Immediate (0-24 hours)
- [ ] Issue initial statement acknowledging situation
- [ ] Respond to top 10 most engaged negative posts
- [ ] Brief internal stakeholders
- [ ] Prepare FAQ document

### Short-term (1-7 days)
- [ ] Daily updates on progress
- [ ] Host Q&A session (if appropriate)
- [ ] Share positive testimonials
- [ ] Monitor sentiment shifts

### Medium-term (1-4 weeks)
- [ ] Weekly progress reports
- [ ] Case studies of improvements
- [ ] Engage with influencers
- [ ] Measure communication impact

---

## 📊 MONITORING & MEASUREMENT

### Key Metrics to Track
- Sentiment score changes
- Engagement rate on responses
- Share of voice vs competitors
- Response time to comments
- Issue resolution rate

### Success Indicators
- ✅ Negative sentiment decreasing
- ✅ Positive engagement increasing
- ✅ Issue mentions declining
- ✅ Brand trust scores improving

---

## 🚨 ESCALATION PROTOCOL

### Level 1: Standard Response
- Individual team member responds
- Use approved templates
- Log in tracking system

### Level 2: Manager Review
- Sensitive or complex issues
- Manager approval required
- Coordinated response

### Level 3: Executive Involvement
- Crisis situation
- Legal/regulatory concerns
- CEO/spokesperson statement

---

## 📞 CONTACT INFORMATION

**Media Inquiries:** [media@company.com]  
**Customer Support:** [support@company.com]  
**Crisis Hotline:** [emergency contact]

---

**Plan Prepared:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Next Review:** [Schedule regular updates]  
**System:** InsightPulse Professional Analytics
"""
    
    return template


def generate_dashboard_html_template(
    query: str,
    analysis_type: str,
    analysis_data: Dict[str, Any]
) -> str:
    """Generate interactive HTML dashboard with Chart.js"""

    # Extract data
    sentiment = analysis_data.get('sentiment_analysis', {})
    platform_data = analysis_data.get('platform_breakdown', {})
    raw_data = analysis_data.get('raw_data', [])

    from html import escape

    # Calculate metrics
    total_posts = len(raw_data)
    positive_ratio = sentiment.get('positive_ratio', 0)
    negative_ratio = sentiment.get('negative_ratio', 0)
    neutral_ratio = sentiment.get('neutral_ratio', 0)

    def _number(value, default=0):
        try:
            if value is None or str(value).lower() == 'nan':
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _field(post, *names, default=''):
        for name in names:
            value = post.get(name)
            if value is not None and str(value).lower() != 'nan':
                return value
        return default

    def _sentiment_label(post):
        label = str(_field(post, 'sentiment_label', 'Sentiment', 'sentiment', default='')).lower()
        if label in {'positive', 'neutral', 'negative'}:
            return label
        score = _number(post.get('sentiment_score'), 0.5)
        return 'positive' if score > 0.6 else 'negative' if score < 0.4 else 'neutral'

    def _engagement(post):
        engagement = post.get('engagement') if isinstance(post.get('engagement'), dict) else {}
        if engagement:
            return int(_number(engagement.get('total'), 0))
        total = post.get('total_engagement')
        if total is None:
            total = _number(post.get('likes'), 0) + _number(post.get('shares'), 0) + _number(post.get('comments_count'), 0)
        return int(_number(total, 0))

    if raw_data and (positive_ratio + negative_ratio + neutral_ratio) == 0:
        counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        for row in raw_data:
            counts[_sentiment_label(row)] += 1
        total = sum(counts.values()) or 1
        positive_ratio = counts['positive'] / total * 100
        neutral_ratio = counts['neutral'] / total * 100
        negative_ratio = counts['negative'] / total * 100

    brand_health = max(0, min(100, round(positive_ratio + (neutral_ratio * 0.45) - (negative_ratio * 0.8), 1)))
    risk_level = 'High' if negative_ratio >= 30 else 'Medium' if negative_ratio >= 15 else 'Low'
    priority_action = 'Activate response room' if risk_level == 'High' else 'Engage and clarify concerns' if risk_level == 'Medium' else 'Amplify advocates'

    # Get top posts
    top_posts = sorted(raw_data, key=_engagement, reverse=True)[:10]

    # Prepare platform data for charts
    platform_names = []
    platform_posts = []
    platform_engagement = []
    platform_sentiment = []

    for platform, data in sorted(platform_data.items()):
        platform_names.append(platform.title())
        platform_posts.append(data.get('total', 0))
        platform_engagement.append(data.get('total_engagement', 0))
        platform_sentiment.append(round(_number(data.get('avg_sentiment'), 0), 3))

    # Convert to JSON for JavaScript
    import json
    platform_names_json = json.dumps(platform_names)
    platform_posts_json = json.dumps(platform_posts)
    platform_engagement_json = json.dumps(platform_engagement)
    platform_sentiment_json = json.dumps(platform_sentiment)

    # Generate top posts HTML
    top_posts_html = ""
    for i, post in enumerate(top_posts[:5], 1):
        total_eng = _engagement(post)
        sentiment_label_raw = _sentiment_label(post)
        sentiment_label = sentiment_label_raw.title()
        sentiment_class = "success" if sentiment_label_raw == 'positive' else "danger" if sentiment_label_raw == 'negative' else "secondary"
        platform_name = escape(str(_field(post, 'platform', 'Platform', default='Unknown')).title())
        content_text = escape(str(_field(post, 'text', 'Text', 'content', default='No content available'))[:120])

        top_posts_html += f"""
        <tr>
            <td>{i}</td>
            <td>{platform_name}</td>
            <td>{content_text}...</td>
            <td>{total_eng:,}</td>
            <td><span class="badge bg-{sentiment_class}">{sentiment_label}</span></td>
        </tr>
        """

    if not top_posts_html:
        top_posts_html = """
        <tr><td colspan="5" class="text-center text-muted py-4">
            No ranked content available for this run. Try increasing dataset size or adding more platforms.
        </td></tr>
        """

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InsightPulse Dashboard - {query}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background: #eef2ff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .dashboard-header {{
            background: radial-gradient(circle at top left, #22d3ee 0, transparent 28%), linear-gradient(135deg, #111827 0%, #312e81 55%, #7c3aed 100%);
            color: white;
            padding: 2.5rem 2rem;
            margin-bottom: 2rem;
            border-radius: 0 0 1rem 1rem;
        }}
        .metric-card {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }}
        .metric-label {{
            color: #6c757d;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .chart-container {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }}
        .table-container {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .insight-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e5e7eb;
            border-radius: 1rem;
            padding: 1.25rem;
            box-shadow: 0 10px 25px rgba(15,23,42,0.08);
            height: 100%;
        }}
        .insight-value {{ font-size: 1.8rem; font-weight: 800; color: #1e1b4b; }}
        .section-title {{ color: #1e1b4b; font-weight: 800; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="dashboard-header">
        <div class="container">
            <h1><i class="bi bi-graph-up"></i> InsightPulse Dashboard</h1>
            <h2>{query}</h2>
            <p class="mb-0">
                <i class="bi bi-calendar"></i> {datetime.now().strftime('%B %d, %Y at %H:%M')} |
                <i class="bi bi-tag"></i> {analysis_type.replace('_', ' ').title()}
            </p>
        </div>
    </div>

    <div class="container">
        <!-- Key Metrics Row -->
        <div class="row">
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label"><i class="bi bi-file-text"></i> Total Posts</div>
                    <div class="metric-value">{total_posts:,}</div>
                    <small class="text-muted">Across all platforms</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label positive"><i class="bi bi-emoji-smile"></i> Positive</div>
                    <div class="metric-value positive">{positive_ratio:.1f}%</div>
                    <small class="text-muted">Positive sentiment</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label neutral"><i class="bi bi-emoji-neutral"></i> Neutral</div>
                    <div class="metric-value neutral">{neutral_ratio:.1f}%</div>
                    <small class="text-muted">Neutral sentiment</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-label negative"><i class="bi bi-emoji-frown"></i> Negative</div>
                    <div class="metric-value negative">{negative_ratio:.1f}%</div>
                    <small class="text-muted">Negative sentiment</small>
                </div>
            </div>
        </div>

        <!-- Executive Decision Row -->
        <div class="row mb-4">
            <div class="col-md-4 mb-3">
                <div class="insight-card">
                    <div class="metric-label"><i class="bi bi-shield-check"></i> Brand Health</div>
                    <div class="insight-value">{brand_health}%</div>
                    <small class="text-muted">Positive momentum adjusted for risk</small>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="insight-card">
                    <div class="metric-label"><i class="bi bi-exclamation-triangle"></i> Reputation Risk</div>
                    <div class="insight-value">{risk_level}</div>
                    <small class="text-muted">Based on negative sentiment share</small>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="insight-card">
                    <div class="metric-label"><i class="bi bi-lightning-charge"></i> Next Best Action</div>
                    <div class="insight-value" style="font-size:1.25rem;">{priority_action}</div>
                    <small class="text-muted">Recommended immediate focus</small>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row">
            <!-- Sentiment Distribution -->
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 class="section-title"><i class="bi bi-pie-chart"></i> Sentiment Distribution</h4>
                    <canvas id="sentimentChart"></canvas>
                </div>
            </div>

            <!-- Platform Comparison -->
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 class="section-title"><i class="bi bi-bar-chart"></i> Records by Platform</h4>
                    <canvas id="platformChart"></canvas>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Engagement by Platform -->
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 class="section-title"><i class="bi bi-heart"></i> Engagement by Platform</h4>
                    <canvas id="engagementChart"></canvas>
                </div>
            </div>

            <!-- Sentiment by Platform -->
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 class="section-title"><i class="bi bi-graph-up-arrow"></i> Average Sentiment by Platform</h4>
                    <canvas id="sentimentByPlatformChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Top Posts Table -->
        <div class="row">
            <div class="col-12">
                <div class="table-container">
                    <h4 class="section-title"><i class="bi bi-trophy"></i> Highest-Impact Content</h4>
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Platform</th>
                                <th>Content</th>
                                <th>Engagement</th>
                                <th>Sentiment</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_posts_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-4 mb-4">
            <p class="text-muted">
                <i class="bi bi-shield-check"></i> Generated by InsightPulse Professional Analytics<br>
                <small>Powered by Malaysian custom AI models and real-time data crawling</small>
            </p>
        </div>
    </div>

    <script>
        // Sentiment Distribution Pie Chart
        const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
        new Chart(sentimentCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{{
                    data: [{positive_ratio:.1f}, {neutral_ratio:.1f}, {negative_ratio:.1f}],
                    backgroundColor: ['#28a745', '#6c757d', '#dc3545'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Platform Posts Bar Chart
        const platformCtx = document.getElementById('platformChart').getContext('2d');
        new Chart(platformCtx, {{
            type: 'bar',
            data: {{
                labels: {platform_names_json},
                datasets: [{{
                    label: 'Number of Posts',
                    data: {platform_posts_json},
                    backgroundColor: '#667eea',
                    borderColor: '#764ba2',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Engagement by Platform
        const engagementCtx = document.getElementById('engagementChart').getContext('2d');
        new Chart(engagementCtx, {{
            type: 'bar',
            data: {{
                labels: {platform_names_json},
                datasets: [{{
                    label: 'Total Engagement',
                    data: {platform_engagement_json},
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Sentiment by Platform
        const sentimentByPlatformCtx = document.getElementById('sentimentByPlatformChart').getContext('2d');
        new Chart(sentimentByPlatformCtx, {{
            type: 'line',
            data: {{
                labels: {platform_names_json},
                datasets: [{{
                    label: 'Average Sentiment Score',
                    data: {platform_sentiment_json},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return template

