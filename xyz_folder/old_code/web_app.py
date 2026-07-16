#!/usr/bin/env python3
"""
InsightPulse - Web Application Frontend
Beautiful web interface for social media analytics
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="InsightPulse - Social Media Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8080"

def call_api(endpoint):
    """Call the FastAPI backend"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Make sure the backend is running."}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def post_api(endpoint, data):
    """Post data to the FastAPI backend"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 InsightPulse</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Social Media Analytics Platform</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Check API Status
    api_status = call_api("/health")
    if "error" not in api_status:
        st.sidebar.markdown('<p class="status-good">✅ API Connected</p>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<p class="status-warning">⚠️ API Disconnected</p>', unsafe_allow_html=True)
        st.sidebar.error(api_status.get("error", "Unknown error"))
    
    # Navigation
    page = st.sidebar.selectbox(
        "📍 Navigate",
        ["🏠 Dashboard", "📊 Analytics", "🤖 AI Agents", "🌐 Platforms", "⚙️ Settings"]
    )
    
    # Main Content
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🤖 AI Agents":
        show_agents()
    elif page == "🌐 Platforms":
        show_platforms()
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard():
    """Dashboard page"""
    st.header("📊 Dashboard Overview")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts Analyzed", "12,543", "↗️ +234")
    with col2:
        st.metric("Sentiment Score", "78%", "↗️ +5%")
    with col3:
        st.metric("Active Platforms", "7", "→ 0")
    with col4:
        st.metric("AI Accuracy", "97.3%", "↗️ +0.8%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Sentiment Trends")
        # Sample data for demo
        dates = pd.date_range('2024-06-01', periods=30, freq='D')
        sentiment_data = pd.DataFrame({
            'Date': dates,
            'Positive': [65 + i*0.5 + (i%7)*2 for i in range(30)],
            'Negative': [20 + (i%5)*1.5 for i in range(30)],
            'Neutral': [15 + (i%3)*1 for i in range(30)]
        })
        
        fig = px.line(sentiment_data, x='Date', y=['Positive', 'Negative', 'Neutral'],
                     title="Sentiment Analysis Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🌐 Platform Distribution")
        platform_data = pd.DataFrame({
            'Platform': ['Facebook', 'Instagram', 'Twitter', 'TikTok', 'LinkedIn'],
            'Posts': [3200, 2800, 2100, 1900, 1500]
        })
        
        fig = px.pie(platform_data, values='Posts', names='Platform',
                    title="Posts by Platform")
        st.plotly_chart(fig, use_container_width=True)

def show_analytics():
    """Analytics page"""
    st.header("📊 Social Media Analytics")
    
    # Analysis form
    with st.form("analysis_form"):
        st.subheader("🔍 Analyze Social Media Content")
        
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Search Query", placeholder="Enter keywords to analyze...")
            language = st.selectbox("Language", ["bahasa_malaysia", "english", "chinese"])
        
        with col2:
            platforms = st.multiselect(
                "Select Platforms",
                ["facebook", "instagram", "twitter", "tiktok", "linkedin", "youtube"],
                default=["facebook", "instagram", "twitter"]
            )
        
        submitted = st.form_submit_button("🚀 Analyze", use_container_width=True)
        
        if submitted and query:
            with st.spinner("🤖 AI is analyzing your query..."):
                # Simulate API call
                analysis_data = {
                    "query": query,
                    "platforms": platforms,
                    "language": language
                }
                
                # Mock response for demo
                result = {
                    "query": query,
                    "sentiment": "positive",
                    "confidence": 0.89,
                    "insights": [
                        f"Analysis of '{query}' shows positive sentiment",
                        "Detected cultural context relevant to Malaysian audience",
                        f"Trending patterns identified across {len(platforms)} platforms"
                    ],
                    "platforms_analyzed": platforms,
                    "total_posts": 2847
                }
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sentiment", result["sentiment"].title(), f"{result['confidence']:.1%} confidence")
                with col2:
                    st.metric("Posts Analyzed", f"{result['total_posts']:,}")
                with col3:
                    st.metric("Platforms", len(result["platforms_analyzed"]))
                
                st.subheader("💡 Key Insights")
                for insight in result["insights"]:
                    st.write(f"• {insight}")

def show_agents():
    """AI Agents page"""
    st.header("🤖 AI Agents Status")
    
    # Get agents status from API
    agents_data = call_api("/agents/status")
    
    if "error" not in agents_data:
        st.subheader("🔧 Active Agents")
        
        agents = agents_data.get("agents", {})
        for agent_name, agent_info in agents.items():
            with st.expander(f"🤖 {agent_name.replace('_', ' ').title()}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    status = agent_info.get("status", "unknown")
                    if status == "active":
                        st.markdown('<p class="status-good">✅ Active</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="status-warning">⚠️ Inactive</p>', unsafe_allow_html=True)
                
                with col2:
                    for key, value in agent_info.items():
                        if key != "status":
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # RAG System Status
        st.subheader("📚 RAG System")
        rag_info = agents_data.get("rag_system", {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Vector Database", rag_info.get("vector_db", "unknown"))
        with col2:
            st.metric("Embeddings", rag_info.get("embeddings", "unknown"))
        with col3:
            st.metric("Knowledge Base", rag_info.get("knowledge_base", "unknown"))
    else:
        st.error(agents_data["error"])

def show_platforms():
    """Platforms page"""
    st.header("🌐 Supported Platforms")
    
    platforms_data = call_api("/platforms")
    
    if "error" not in platforms_data:
        platforms = platforms_data.get("supported_platforms", [])
        
        st.subheader(f"📱 {len(platforms)} Platforms Available")
        
        for platform in platforms:
            with st.expander(f"📱 {platform['name']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Status:** {platform['status']}")
                    st.write(f"**API Version:** {platform.get('api_version', 'N/A')}")
                with col2:
                    if platform.get('scraping'):
                        st.write("**Method:** Web Scraping")
                    else:
                        st.write("**Method:** Official API")
        
        # Malaysian specific platforms
        malaysian_platforms = platforms_data.get("malaysian_specific", [])
        if malaysian_platforms:
            st.subheader("🇲🇾 Malaysian-Specific Sources")
            for platform in malaysian_platforms:
                st.write(f"• {platform}")
    else:
        st.error(platforms_data["error"])

def show_settings():
    """Settings page"""
    st.header("⚙️ Settings")
    
    st.subheader("🔧 API Configuration")
    st.code(f"API Base URL: {API_BASE_URL}")
    
    st.subheader("📊 Data Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Default Language", ["bahasa_malaysia", "english", "chinese"])
        st.slider("Analysis Confidence Threshold", 0.0, 1.0, 0.7)
    
    with col2:
        st.multiselect("Default Platforms", 
                      ["facebook", "instagram", "twitter", "tiktok"],
                      default=["facebook", "instagram"])
        st.number_input("Max Posts per Analysis", min_value=100, max_value=10000, value=1000)
    
    if st.button("💾 Save Settings"):
        st.success("✅ Settings saved successfully!")

if __name__ == "__main__":
    main()
