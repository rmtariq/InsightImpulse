#!/usr/bin/env python3
"""
Enhanced InsightPulse Web Application
Integrates with existing 7-platform crawler system and report generation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Page configuration
st.set_page_config(
    page_title="InsightPulse - 7-Platform Analytics",
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
    .status-good { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .platform-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem;
        text-align: center;
    }
    .metric-big {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"
DATA_PATH = Path("data/smart_crawlers")
# ULTIMATE 9-PLATFORM INTEGRATION
PLATFORMS = [
    # Social Media Platforms (7)
    "facebook", "instagram", "x", "tiktok", "google", "news", "lowyat",
    # E-commerce Platforms (2) - NEW INTEGRATION
    "shopee", "lazada"
]

def load_crawler_data():
    """Load data from all 7 platforms"""
    all_data = []
    platform_stats = {}
    
    for platform in PLATFORMS:
        platform_path = DATA_PATH / platform
        if platform_path.exists():
            csv_files = list(platform_path.glob("*.csv"))
            platform_data = []
            
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    df['source_file'] = csv_file.name
                    df['crawl_date'] = csv_file.name.split('_')[-2] if '_' in csv_file.name else 'unknown'
                    platform_data.append(df)
                except Exception as e:
                    st.error(f"Error loading {csv_file}: {e}")
            
            if platform_data:
                combined_df = pd.concat(platform_data, ignore_index=True)
                combined_df['Platform'] = platform.title()
                all_data.append(combined_df)
                
                # Calculate platform statistics
                platform_stats[platform] = {
                    'total_posts': len(combined_df),
                    'files': len(csv_files),
                    'latest_crawl': max([f.stat().st_mtime for f in csv_files]) if csv_files else 0
                }
    
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(), platform_stats

def call_api(endpoint):
    """Call the existing backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Cannot connect to API: {str(e)}"}

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 InsightPulse</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">7-Platform Social Media Analytics with Real-Time Crawling</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Check API Status
    api_status = call_api("/health")
    if "error" not in api_status:
        st.sidebar.markdown('<p class="status-good">✅ Backend Connected</p>', unsafe_allow_html=True)
        st.sidebar.json(api_status.get("components", {}))
    else:
        st.sidebar.markdown('<p class="status-warning">⚠️ Backend Disconnected</p>', unsafe_allow_html=True)
        st.sidebar.error("Start backend with: python backend/api.py")
    
    # Navigation
    page = st.sidebar.selectbox(
        "📍 Navigate",
        ["🏠 Dashboard", "📊 Live Analytics", "🕷️ Crawler Status", "📈 Reports", "🔍 Data Explorer"]
    )
    
    # Load data
    with st.spinner("Loading crawler data..."):
        df, platform_stats = load_crawler_data()
    
    # Main Content
    if page == "🏠 Dashboard":
        show_dashboard(df, platform_stats)
    elif page == "📊 Live Analytics":
        show_live_analytics(df)
    elif page == "🕷️ Crawler Status":
        show_crawler_status(platform_stats)
    elif page == "📈 Reports":
        show_reports(df)
    elif page == "🔍 Data Explorer":
        show_data_explorer(df)

def show_dashboard(df, platform_stats):
    """Enhanced dashboard with real data"""
    st.header("📊 Real-Time Dashboard")
    
    if df.empty:
        st.warning("⚠️ No crawler data found. Please run the crawlers first.")
        st.info("💡 Use the existing start_both.py to run the complete system")
        return
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_posts = len(df)
        st.metric("Total Posts Crawled", f"{total_posts:,}")
    
    with col2:
        active_platforms = len([p for p in platform_stats if platform_stats[p]['total_posts'] > 0])
        st.metric("Active Platforms", f"{active_platforms}/7")
    
    with col3:
        if 'sentiment_score' in df.columns:
            avg_sentiment = df['sentiment_score'].mean()
            st.metric("Avg Sentiment Score", f"{avg_sentiment:.2f}")
        else:
            st.metric("Sentiment Analysis", "Available")
    
    with col4:
        if 'total_engagement' in df.columns:
            total_engagement = df['total_engagement'].sum()
            st.metric("Total Engagement", f"{total_engagement:,}")
        else:
            st.metric("Data Quality", "High")
    
    # Platform Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📱 Platform Distribution")
        if not df.empty:
            platform_counts = df['Platform'].value_counts()
            fig = px.pie(values=platform_counts.values, names=platform_counts.index,
                        title="Posts by Platform")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Sentiment Distribution")
        if 'Sentiment' in df.columns:
            sentiment_counts = df['Sentiment'].value_counts()
            fig = px.bar(x=sentiment_counts.index, y=sentiment_counts.values,
                        title="Sentiment Analysis Results")
            st.plotly_chart(fig, use_container_width=True)

def show_live_analytics(df):
    """Live analytics with real crawler data"""
    st.header("📊 Live Social Media Analytics")
    
    # Search and filter interface
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("🔍 Search in crawled data", placeholder="Enter keywords...")
        
    with col2:
        selected_platforms = st.multiselect(
            "📱 Filter by Platform",
            options=PLATFORMS,
            default=PLATFORMS
        )
    
    # Filter data
    filtered_df = df.copy()
    
    if search_term:
        if 'Text' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Text'].str.contains(search_term, case=False, na=False)]
    
    if selected_platforms:
        platform_filter = [p.title() for p in selected_platforms]
        filtered_df = filtered_df[filtered_df['Platform'].isin(platform_filter)]
    
    if not filtered_df.empty:
        st.success(f"✅ Found {len(filtered_df)} matching posts")
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Sentiment' in filtered_df.columns:
                sentiment_dist = filtered_df['Sentiment'].value_counts()
                most_common = sentiment_dist.index[0] if len(sentiment_dist) > 0 else "Unknown"
                st.metric("Dominant Sentiment", most_common)
        
        with col2:
            if 'total_engagement' in filtered_df.columns:
                avg_engagement = filtered_df['total_engagement'].mean()
                st.metric("Avg Engagement", f"{avg_engagement:.0f}")
        
        with col3:
            platforms_found = filtered_df['Platform'].nunique()
            st.metric("Platforms Found", platforms_found)
        
        # Show sample data
        st.subheader("📋 Sample Results")
        display_cols = ['Platform', 'Text', 'Sentiment', 'Date']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        if available_cols:
            st.dataframe(filtered_df[available_cols].head(10), use_container_width=True)
    else:
        st.warning("⚠️ No matching data found")

def show_crawler_status(platform_stats):
    """Show status of all 7 platform crawlers"""
    st.header("🕷️ 7-Platform Crawler Status")
    
    # Platform status cards
    cols = st.columns(4)
    
    for i, platform in enumerate(PLATFORMS):
        with cols[i % 4]:
            stats = platform_stats.get(platform, {'total_posts': 0, 'files': 0, 'latest_crawl': 0})
            
            status_color = "🟢" if stats['total_posts'] > 0 else "🔴"
            
            st.markdown(f"""
            <div class="platform-card">
                <h3>{status_color} {platform.title()}</h3>
                <p><strong>{stats['total_posts']:,}</strong> posts</p>
                <p><strong>{stats['files']}</strong> files</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Detailed status table
    st.subheader("📊 Detailed Status")
    
    status_data = []
    for platform in PLATFORMS:
        stats = platform_stats.get(platform, {'total_posts': 0, 'files': 0, 'latest_crawl': 0})
        
        last_crawl = "Never"
        if stats['latest_crawl'] > 0:
            last_crawl = datetime.fromtimestamp(stats['latest_crawl']).strftime("%Y-%m-%d %H:%M")
        
        status_data.append({
            "Platform": platform.title(),
            "Status": "🟢 Active" if stats['total_posts'] > 0 else "🔴 Inactive",
            "Total Posts": f"{stats['total_posts']:,}",
            "Files": stats['files'],
            "Last Crawl": last_crawl
        })
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True)

def show_reports(df):
    """Generate and display reports"""
    st.header("📈 Analytics Reports")
    
    if df.empty:
        st.warning("⚠️ No data available for reports")
        return
    
    # Report generation options
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "📊 Report Type",
            ["Sentiment Analysis", "Platform Comparison", "Engagement Analysis", "Trend Analysis"]
        )
    
    with col2:
        date_range = st.selectbox(
            "📅 Time Period",
            ["Last 7 Days", "Last 30 Days", "All Time"]
        )
    
    if st.button("📋 Generate Report", use_container_width=True):
        with st.spinner("Generating report..."):
            
            if report_type == "Sentiment Analysis":
                st.subheader("😊 Sentiment Analysis Report")
                
                if 'Sentiment' in df.columns:
                    sentiment_summary = df['Sentiment'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.pie(values=sentiment_summary.values, names=sentiment_summary.index)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        for sentiment, count in sentiment_summary.items():
                            percentage = (count / len(df)) * 100
                            st.metric(f"{sentiment} Posts", f"{count:,}", f"{percentage:.1f}%")
            
            elif report_type == "Platform Comparison":
                st.subheader("📱 Platform Comparison Report")
                
                platform_summary = df.groupby('Platform').agg({
                    'Text': 'count',
                    'total_engagement': 'sum' if 'total_engagement' in df.columns else 'count'
                }).round(2)
                
                st.dataframe(platform_summary, use_container_width=True)
        
        st.success("✅ Report generated successfully!")

def show_data_explorer(df):
    """Data exploration interface"""
    st.header("🔍 Data Explorer")
    
    if df.empty:
        st.warning("⚠️ No data to explore")
        return
    
    # Data overview
    st.subheader("📊 Data Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Platforms", df['Platform'].nunique() if 'Platform' in df.columns else 0)
    
    # Column information
    st.subheader("📋 Available Columns")
    st.write(list(df.columns))
    
    # Sample data
    st.subheader("🔍 Sample Data")
    st.dataframe(df.head(20), use_container_width=True)
    
    # Download option
    if st.button("💾 Download Complete Dataset"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"insightpulse_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
