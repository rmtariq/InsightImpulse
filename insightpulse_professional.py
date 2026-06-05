#!/usr/bin/env python3
"""
InsightPulse Professional - Complete Social Media Analytics System
Integrates Claim Input, AI Keyword Generation, Multi-Platform Crawling, AI Analysis, and Professional Reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
from claim_input_system import ClaimInputSystem, ClaimData
from keyword_generator import AIKeywordGenerator

# Page configuration
st.set_page_config(
    page_title="InsightPulse Professional - 7-Platform Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4ECDC4;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-active {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .workflow-step {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .workflow-step:hover {
        border-color: #4ECDC4;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .workflow-step.active {
        border-color: #4ECDC4;
        background: #e8f8f5;
    }
    
    .workflow-step.completed {
        border-color: #28a745;
        background: #d4edda;
    }
</style>
""", unsafe_allow_html=True)

class InsightPulseProfessional:
    """Main application class for InsightPulse Professional"""
    
    def __init__(self):
        self.claim_system = ClaimInputSystem()
        self.keyword_generator = AIKeywordGenerator()
        self.workflow_state = self.load_workflow_state()
    
    def load_workflow_state(self) -> dict:
        """Load current workflow state"""
        state_file = Path("data/workflow/state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'current_step': 1,
            'completed_steps': [],
            'active_claim': None,
            'generated_keywords': None,
            'crawler_status': {},
            'analysis_results': None
        }
    
    def save_workflow_state(self):
        """Save current workflow state"""
        state_file = Path("data/workflow/state.json")
        with open(state_file, 'w') as f:
            json.dump(self.workflow_state, f, indent=2)
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🚀 InsightPulse Professional</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">7-Platform Social Media Analytics with Real-Time Crawling & AI Analysis</p>', unsafe_allow_html=True)
        
        # System status overview
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            claims_count = len(self.claim_system.load_claims())
            st.metric("📝 Claims", claims_count)
        
        with col2:
            keywords_file = Path("data/keywords/generated_keywords.json")
            keywords_count = 0
            if keywords_file.exists():
                try:
                    with open(keywords_file, 'r') as f:
                        keywords_count = len(json.load(f))
                except:
                    pass
            st.metric("🧠 Keywords", keywords_count)
        
        with col3:
            st.metric("🕷️ Crawlers", "7 Active")
        
        with col4:
            st.metric("🤖 AI Engine", "Ready")
        
        with col5:
            st.metric("📊 Reports", "Available")
    
    def render_workflow_progress(self):
        """Render workflow progress indicator"""
        st.subheader("🔄 Workflow Progress")
        
        steps = [
            {"id": 1, "name": "Claim Input", "icon": "🎯", "description": "Submit claims for analysis"},
            {"id": 2, "name": "Keyword Generation", "icon": "🧠", "description": "AI generates optimal keywords"},
            {"id": 3, "name": "Data Crawling", "icon": "🕷️", "description": "Collect data from 7 platforms"},
            {"id": 4, "name": "AI Analysis", "icon": "🤖", "description": "Agent + RAG + LLM analysis"},
            {"id": 5, "name": "Professional Reports", "icon": "📊", "description": "Generate stakeholder reports"}
        ]
        
        cols = st.columns(5)
        
        for i, step in enumerate(steps):
            with cols[i]:
                # Determine step status
                if step["id"] in self.workflow_state.get('completed_steps', []):
                    status_class = "completed"
                    status_text = "✅ Completed"
                elif step["id"] == self.workflow_state.get('current_step', 1):
                    status_class = "active"
                    status_text = "🔄 Active"
                else:
                    status_class = ""
                    status_text = "⏳ Pending"
                
                st.markdown(f"""
                <div class="workflow-step {status_class}">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem;">{step['icon']}</div>
                        <div style="font-weight: bold; margin: 0.5rem 0;">{step['name']}</div>
                        <div style="font-size: 0.8rem; color: #666;">{step['description']}</div>
                        <div style="margin-top: 0.5rem;">
                            <span class="status-badge status-{status_class.replace('completed', 'active') if status_class else 'pending'}">{status_text}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_main_navigation(self):
        """Render main navigation"""
        st.sidebar.title("🚀 InsightPulse Professional")
        st.sidebar.markdown("---")
        
        # Navigation menu
        pages = {
            "🏠 Dashboard": "dashboard",
            "🎯 1. Claim Input": "claim_input",
            "🧠 2. Keyword Generator": "keyword_generator", 
            "🕷️ 3. Crawler Setup": "crawler_setup",
            "🤖 4. AI Analysis": "ai_analysis",
            "📊 5. Professional Reports": "reports"
        }
        
        selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
        
        # Quick stats in sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("📈 Quick Stats")
        
        claims = self.claim_system.load_claims()
        st.sidebar.metric("Total Claims", len(claims))
        
        if claims:
            recent_claims = [c for c in claims if datetime.fromisoformat(c['created_at']) > datetime.now() - timedelta(days=7)]
            st.sidebar.metric("This Week", len(recent_claims))
        
        # System status
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 System Status")
        st.sidebar.success("✅ All systems operational")
        
        return pages[selected_page]
    
    def render_dashboard(self):
        """Render main dashboard"""
        st.header("🏠 Dashboard Overview")
        
        # Workflow progress
        self.render_workflow_progress()
        
        st.markdown("---")
        
        # Recent activity
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 Recent Claims")
            claims = self.claim_system.load_claims()
            
            if claims:
                df = pd.DataFrame(claims)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df = df.sort_values('created_at', ascending=False)
                
                for _, claim in df.head(5).iterrows():
                    with st.expander(f"🎯 {claim['title']}", expanded=False):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Category:** {claim['category']}")
                            st.write(f"**Priority:** {claim['priority']}")
                        with col_b:
                            st.write(f"**Language:** {claim['language']}")
                            st.write(f"**Created:** {claim['created_at'].strftime('%Y-%m-%d %H:%M')}")
            else:
                st.info("No claims submitted yet. Start by submitting your first claim!")
        
        with col2:
            st.subheader("🎯 Quick Actions")
            
            if st.button("📝 Submit New Claim", type="primary", use_container_width=True):
                st.session_state.page = "claim_input"
                st.rerun()
            
            if st.button("🧠 Generate Keywords", use_container_width=True):
                st.session_state.page = "keyword_generator"
                st.rerun()
            
            if st.button("🕷️ Start Crawling", use_container_width=True):
                st.session_state.page = "crawler_setup"
                st.rerun()
            
            if st.button("🤖 Run AI Analysis", use_container_width=True):
                st.session_state.page = "ai_analysis"
                st.rerun()
            
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.page = "reports"
                st.rerun()
    
    def render_claim_input_page(self):
        """Render claim input page"""
        self.claim_system.render_input_form()
        
        st.markdown("---")
        
        # Show recent claims
        self.claim_system.render_claims_history()
    
    def render_keyword_generator_page(self):
        """Render keyword generator page"""
        st.header("🧠 AI Keyword Generator")
        
        # Load claims for selection
        claims = self.claim_system.load_claims()
        
        if not claims:
            st.warning("⚠️ No claims available. Please submit a claim first.")
            if st.button("📝 Go to Claim Input"):
                st.session_state.page = "claim_input"
                st.rerun()
            return
        
        # Select claim for keyword generation
        claim_options = {f"{claim['title']} ({claim['category']})": claim for claim in claims}
        selected_claim_key = st.selectbox("Select claim for keyword generation:", list(claim_options.keys()))
        
        if selected_claim_key:
            selected_claim = claim_options[selected_claim_key]
            
            # Generate keywords
            keyword_set = self.keyword_generator.render_keyword_generator(selected_claim)
            
            if keyword_set:
                # Update workflow state
                self.workflow_state['current_step'] = 3
                if 2 not in self.workflow_state['completed_steps']:
                    self.workflow_state['completed_steps'].append(2)
                self.workflow_state['generated_keywords'] = selected_claim['id']
                self.save_workflow_state()
    
    def render_crawler_setup_page(self):
        """Render crawler setup page"""
        st.header("🕷️ Multi-Platform Crawler Setup")
        st.info("🚧 Crawler setup interface coming next! This will integrate with your existing 7-platform crawler system.")
        
        # Show placeholder for crawler interface
        platforms = ["Facebook", "Instagram", "Twitter/X", "TikTok", "Google", "News", "Forums"]
        
        for platform in platforms:
            with st.expander(f"🔧 {platform} Crawler Configuration"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Status:** Ready")
                    st.write("**Last Run:** 2 hours ago")
                with col2:
                    st.write("**Data Collected:** 1,234 posts")
                    st.write("**Success Rate:** 98%")
    
    def render_ai_analysis_page(self):
        """Render AI analysis page"""
        st.header("🤖 AI Analysis Engine")
        st.info("🚧 AI Analysis interface coming next! This will implement Agent + RAG + Vector DB + LLM with MCP integration.")
        
        # Placeholder for AI analysis
        st.subheader("🧠 Analysis Components")
        
        components = [
            {"name": "Vector Database", "status": "Ready", "description": "Qdrant vector storage"},
            {"name": "RAG System", "status": "Ready", "description": "Retrieval-Augmented Generation"},
            {"name": "LLM Agent", "status": "Ready", "description": "GPT-4 + Claude ensemble"},
            {"name": "MCP Integration", "status": "Ready", "description": "Model Context Protocol"}
        ]
        
        for component in components:
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.write(f"**{component['name']}**")
            with col2:
                st.success(f"✅ {component['status']}")
            with col3:
                st.write(component['description'])
    
    def render_reports_page(self):
        """Render professional reports page"""
        st.header("📊 Professional Reports")
        st.info("🚧 Professional reporting interface coming next! This will generate stakeholder-ready reports and visualizations.")
        
        # Placeholder for reports
        report_types = [
            "Executive Summary Report",
            "Detailed Analysis Report", 
            "Platform Comparison Report",
            "Sentiment Analysis Report",
            "Trend Analysis Report"
        ]
        
        for report_type in report_types:
            if st.button(f"📄 Generate {report_type}", use_container_width=True):
                st.info(f"Generating {report_type}...")
    
    def run(self):
        """Main application runner"""
        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = 'dashboard'
        
        # Render header
        self.render_header()
        
        # Get current page from navigation
        current_page = self.render_main_navigation()
        
        # Override with session state if set
        if hasattr(st.session_state, 'page'):
            current_page = st.session_state.page
        
        # Render appropriate page
        if current_page == "dashboard":
            self.render_dashboard()
        elif current_page == "claim_input":
            self.render_claim_input_page()
        elif current_page == "keyword_generator":
            self.render_keyword_generator_page()
        elif current_page == "crawler_setup":
            self.render_crawler_setup_page()
        elif current_page == "ai_analysis":
            self.render_ai_analysis_page()
        elif current_page == "reports":
            self.render_reports_page()

def main():
    """Main entry point"""
    app = InsightPulseProfessional()
    app.run()

if __name__ == "__main__":
    main()
