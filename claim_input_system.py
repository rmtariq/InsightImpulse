#!/usr/bin/env python3
"""
Professional Claim Input System for InsightPulse
Smart interface for inputting claims with validation, categorization, and preprocessing
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import uuid
import json
import re
from pathlib import Path
import torch
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
import subprocess
import os

class ClaimCategory(Enum):
    """Predefined claim categories for Malaysian context"""
    POLITICAL = "Political"
    RELIGIOUS = "Religious" 
    ECONOMIC = "Economic"
    SOCIAL = "Social"
    HEALTH = "Health"
    EDUCATION = "Education"
    TECHNOLOGY = "Technology"
    ENVIRONMENT = "Environment"
    CULTURAL = "Cultural"
    SECURITY = "Security"

class ClaimPriority(Enum):
    """Priority levels for claim analysis"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class ClaimLanguage(Enum):
    """Supported languages for Malaysian context"""
    MALAY = "Bahasa Malaysia"
    ENGLISH = "English"
    CHINESE = "Chinese"
    TAMIL = "Tamil"
    MIXED = "Mixed Languages"

@dataclass
class ClaimData:
    """Data structure for storing claim information"""
    id: str
    title: str
    description: str
    category: ClaimCategory
    priority: ClaimPriority
    language: ClaimLanguage
    keywords: List[str]
    target_platforms: List[str]
    created_at: datetime
    created_by: str
    status: str = "pending"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'language': self.language.value,
            'keywords': self.keywords,
            'target_platforms': self.target_platforms,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'status': self.status
        }

class ClaimInputSystem:
    """Professional claim input system with AI-powered validation and preprocessing"""

    def __init__(self):
        self.claims_file = Path("data/claims/claims_database.json")
        self.claims_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize AI models
        self.init_ai_models()

    def init_ai_models(self):
        """Initialize AI models for intelligent classification"""
        try:
            # Load claim classifier model
            self.claim_classifier = pipeline(
                "text-classification",
                model="rmtariq/malay_claim_classifier_v2",
                tokenizer="rmtariq/malay_claim_classifier_v2"
            )

            # Load priority classifier (rule-based)
            self.priority_classifier_available = True

            # Load fact-check model
            self.fact_checker = pipeline(
                "text-classification",
                model="rmtariq/10factcheck",
                tokenizer="rmtariq/10factcheck",
                top_k=None,
                function_to_apply="sigmoid"
            )

            st.success("🤖 AI Models loaded successfully!")

        except Exception as e:
            st.warning(f"⚠️ AI models not available: {e}")
            self.claim_classifier = None
            self.priority_classifier_available = False
            self.fact_checker = None

    def load_claims(self) -> List[Dict]:
        """Load existing claims from storage"""
        if self.claims_file.exists():
            try:
                with open(self.claims_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_claim(self, claim: ClaimData) -> bool:
        """Save claim to storage"""
        try:
            claims = self.load_claims()
            claims.append(claim.to_dict())
            
            with open(self.claims_file, 'w', encoding='utf-8') as f:
                json.dump(claims, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving claim: {e}")
            return False
    
    def validate_claim(self, title: str, description: str) -> Tuple[bool, List[str]]:
        """Validate claim input with comprehensive checks"""
        errors = []
        
        # Title validation
        if not title or len(title.strip()) < 5:
            errors.append("Title must be at least 5 characters long")
        if len(title) > 200:
            errors.append("Title must be less than 200 characters")
            
        # Description validation
        if not description or len(description.strip()) < 20:
            errors.append("Description must be at least 20 characters long")
        if len(description) > 2000:
            errors.append("Description must be less than 2000 characters")
            
        # Content quality checks
        if title and description:
            # Check for meaningful content
            if len(set(title.lower().split())) < 3:
                errors.append("Title should contain at least 3 unique words")
                
            # Check for suspicious patterns
            if re.search(r'(.)\1{4,}', title + description):
                errors.append("Avoid excessive repetition of characters")
                
        return len(errors) == 0, errors
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'yang', 'dan', 'atau', 'ini', 'itu', 'adalah', 'akan', 'telah'}
        keywords = [word for word in words if word not in stop_words]
        return list(set(keywords))[:20]  # Return top 20 unique keywords
    
    def suggest_category(self, title: str, description: str) -> ClaimCategory:
        """AI-powered category suggestion using trained model"""
        text = title + " " + description

        if self.claim_classifier:
            try:
                # Use AI model for classification
                result = self.claim_classifier(text)
                predicted_label = result[0]['label']

                # Map AI model labels to our enum
                label_mapping = {
                    'agama': ClaimCategory.RELIGIOUS,
                    'alam sekitar': ClaimCategory.ENVIRONMENT,
                    'ekonomi': ClaimCategory.ECONOMIC,
                    'kesihatan': ClaimCategory.HEALTH,
                    'pendidikan': ClaimCategory.EDUCATION,
                    'pengguna': ClaimCategory.SOCIAL,
                    'politik': ClaimCategory.POLITICAL,
                    'sosial': ClaimCategory.SOCIAL,
                    'teknologi': ClaimCategory.TECHNOLOGY
                }

                return label_mapping.get(predicted_label, ClaimCategory.SOCIAL)

            except Exception as e:
                st.warning(f"AI classification failed: {e}")

        # Fallback to keyword-based categorization
        text_lower = text.lower()
        category_keywords = {
            ClaimCategory.POLITICAL: ['politik', 'political', 'government', 'kerajaan', 'parti', 'party', 'election', 'pilihanraya'],
            ClaimCategory.RELIGIOUS: ['islam', 'religious', 'agama', 'muslim', 'christian', 'hindu', 'buddha'],
            ClaimCategory.ECONOMIC: ['ekonomi', 'economic', 'money', 'wang', 'business', 'perniagaan', 'trade'],
            ClaimCategory.HEALTH: ['health', 'kesihatan', 'medical', 'perubatan', 'hospital', 'doctor'],
            ClaimCategory.EDUCATION: ['education', 'pendidikan', 'school', 'sekolah', 'university', 'universiti'],
            ClaimCategory.TECHNOLOGY: ['technology', 'teknologi', 'digital', 'internet', 'computer'],
            ClaimCategory.SOCIAL: ['social', 'sosial', 'community', 'masyarakat', 'family', 'keluarga'],
            ClaimCategory.ENVIRONMENT: ['environment', 'alam', 'climate', 'iklim', 'pollution', 'pencemaran'],
            ClaimCategory.CULTURAL: ['culture', 'budaya', 'tradition', 'tradisi', 'festival', 'celebration'],
            ClaimCategory.SECURITY: ['security', 'keselamatan', 'police', 'polis', 'crime', 'jenayah']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return ClaimCategory.SOCIAL  # Default category

    def suggest_priority(self, title: str, description: str) -> ClaimPriority:
        """AI-powered priority suggestion using Malaysian priority classifier"""
        text = title + " " + description

        if self.priority_classifier_available:
            try:
                # Use shell script for priority classification
                script_path = "models/malaysian-priority-classifier/classify_text.sh"
                if os.path.exists(script_path):
                    result = subprocess.run([script_path, text],
                                          capture_output=True, text=True)
                    priority_class = result.stdout.strip()

                    # Map to priority levels
                    priority_mapping = {
                        'Danger': ClaimPriority.CRITICAL,
                        'Government': ClaimPriority.HIGH,
                        'Law': ClaimPriority.HIGH,
                        'Economic': ClaimPriority.MEDIUM
                    }

                    return priority_mapping.get(priority_class, ClaimPriority.MEDIUM)
            except Exception as e:
                st.warning(f"Priority classification failed: {e}")

        # Fallback priority logic
        text_lower = text.lower()
        critical_keywords = ['bahaya', 'danger', 'emergency', 'darurat', 'banjir', 'gempa', 'covid']
        high_keywords = ['kerajaan', 'government', 'politik', 'undang-undang', 'law']

        if any(keyword in text_lower for keyword in critical_keywords):
            return ClaimPriority.CRITICAL
        elif any(keyword in text_lower for keyword in high_keywords):
            return ClaimPriority.HIGH
        else:
            return ClaimPriority.MEDIUM

    def analyze_fact_check_criteria(self, title: str, description: str) -> Dict:
        """Analyze claim using 10FactCheck model"""
        text = title + " " + description

        if self.fact_checker:
            try:
                results = self.fact_checker(text)

                # Process multi-label results
                criteria = {}
                for result in results:
                    label = result['label']
                    score = result['score']
                    criteria[label] = score > 0.5  # Threshold for binary classification

                return criteria
            except Exception as e:
                st.warning(f"Fact-check analysis failed: {e}")

        return {}
    
    def render_input_form(self):
        """Render the professional claim input form"""
        st.header("🎯 Professional Claim Input System")
        st.markdown("Enter claims for comprehensive social media analysis across 7 platforms")
        
        with st.form("claim_input_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Basic claim information
                title = st.text_input(
                    "Claim Title *",
                    placeholder="Enter a clear, concise title for the claim",
                    help="Provide a descriptive title that summarizes the claim"
                )
                
                description = st.text_area(
                    "Claim Description *",
                    placeholder="Provide detailed description of the claim to be analyzed...",
                    height=150,
                    help="Detailed description helps generate better keywords and analysis"
                )
                
                # AI-powered suggestions
                if title or description:
                    suggested_keywords = self.extract_keywords(title + " " + description)
                    if suggested_keywords:
                        st.info(f"💡 Suggested keywords: {', '.join(suggested_keywords[:10])}")

                    # AI category suggestion
                    suggested_category = self.suggest_category(title, description)
                    st.info(f"🤖 AI suggests category: **{suggested_category.value}**")

                    # AI priority suggestion
                    suggested_priority = self.suggest_priority(title, description)
                    st.info(f"🎯 AI suggests priority: **{suggested_priority.value}**")

                    # Fact-check analysis
                    fact_criteria = self.analyze_fact_check_criteria(title, description)
                    if fact_criteria:
                        st.info("🔍 Fact-check analysis available - see summary below")
            
            with col2:
                # Claim metadata
                # AI-powered category selection
                suggested_cat = self.suggest_category(title or "", description or "")
                category = st.selectbox(
                    "Category (AI-Suggested)",
                    options=[cat.value for cat in ClaimCategory],
                    index=[cat.value for cat in ClaimCategory].index(suggested_cat.value) if (title or description) else 0,
                    help="🤖 AI automatically suggests the most appropriate category"
                )

                # AI-powered priority selection
                suggested_pri = self.suggest_priority(title or "", description or "")
                priority = st.selectbox(
                    "Priority Level (AI-Suggested)",
                    options=[p.value for p in ClaimPriority],
                    index=[p.value for p in ClaimPriority].index(suggested_pri.value) if (title or description) else 1,
                    help="🎯 AI automatically suggests priority based on content analysis"
                )
                
                language = st.selectbox(
                    "Primary Language",
                    options=[lang.value for lang in ClaimLanguage],
                    help="Primary language for keyword generation"
                )
                
                # Platform selection
                st.subheader("Target Platforms")
                platforms = {
                    "Facebook": st.checkbox("Facebook", value=True),
                    "Instagram": st.checkbox("Instagram", value=True),
                    "Twitter/X": st.checkbox("Twitter/X", value=True),
                    "TikTok": st.checkbox("TikTok", value=False),
                    "Google": st.checkbox("Google Trends", value=True),
                    "News": st.checkbox("News Sources", value=True),
                    "Forums": st.checkbox("Forums", value=False)
                }
                
                selected_platforms = [platform for platform, selected in platforms.items() if selected]
            
            # Form submission
            submitted = st.form_submit_button("🚀 Submit Claim for Analysis", type="primary")
            
            if submitted:
                # Validate input
                is_valid, errors = self.validate_claim(title, description)
                
                if not is_valid:
                    for error in errors:
                        st.error(f"❌ {error}")
                elif not selected_platforms:
                    st.error("❌ Please select at least one platform for analysis")
                else:
                    # Create claim object
                    claim = ClaimData(
                        id=str(uuid.uuid4()),
                        title=title.strip(),
                        description=description.strip(),
                        category=ClaimCategory(category),
                        priority=ClaimPriority(priority),
                        language=ClaimLanguage(language),
                        keywords=self.extract_keywords(title + " " + description),
                        target_platforms=selected_platforms,
                        created_at=datetime.now(),
                        created_by="user"  # Can be enhanced with user authentication
                    )
                    
                    # Save claim
                    if self.save_claim(claim):
                        st.success("✅ Claim submitted successfully!")
                        st.balloons()
                        
                        # Show claim summary with AI analysis
                        with st.expander("📋 Claim Summary & AI Analysis", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**ID:** {claim.id}")
                                st.write(f"**Title:** {claim.title}")
                                st.write(f"**Category:** {claim.category.value} 🤖")
                                st.write(f"**Priority:** {claim.priority.value} 🎯")
                            with col2:
                                st.write(f"**Language:** {claim.language.value}")
                                st.write(f"**Platforms:** {', '.join(claim.target_platforms)}")
                                st.write(f"**Keywords:** {', '.join(claim.keywords[:5])}...")
                                st.write(f"**Created:** {claim.created_at.strftime('%Y-%m-%d %H:%M')}")

                            # Show fact-check analysis
                            fact_criteria = self.analyze_fact_check_criteria(claim.title, claim.description)
                            if fact_criteria:
                                st.subheader("🔍 AI Fact-Check Analysis")

                                # Create two columns for criteria
                                col_a, col_b = st.columns(2)

                                criteria_labels = {
                                    'has_fact_value': 'Has Fact Value',
                                    'causes_confusion': 'May Cause Confusion',
                                    'causes_chaos': 'May Cause Chaos',
                                    'affects_government': 'Affects Government',
                                    'impacts_economy': 'Economic Impact',
                                    'breaks_law': 'Legal Concerns',
                                    'public_interest': 'Public Interest',
                                    'life_threatening': 'Life Threatening',
                                    'already_viral': 'Already Viral',
                                    'time_sensitive': 'Time Sensitive'
                                }

                                criteria_items = list(criteria_labels.items())
                                mid_point = len(criteria_items) // 2

                                with col_a:
                                    for key, label in criteria_items[:mid_point]:
                                        if key in fact_criteria:
                                            icon = "✅" if fact_criteria[key] else "❌"
                                            st.write(f"{icon} {label}")

                                with col_b:
                                    for key, label in criteria_items[mid_point:]:
                                        if key in fact_criteria:
                                            icon = "✅" if fact_criteria[key] else "❌"
                                            st.write(f"{icon} {label}")

                                # Priority recommendation based on fact-check
                                high_priority_criteria = ['life_threatening', 'causes_chaos', 'breaks_law', 'time_sensitive']
                                if any(fact_criteria.get(criteria, False) for criteria in high_priority_criteria):
                                    st.warning("⚠️ **High Priority Recommended** - This claim meets critical fact-check criteria")
                                elif fact_criteria.get('has_fact_value', False):
                                    st.info("ℹ️ **Medium Priority** - This claim has fact-checking value")
                                else:
                                    st.success("✅ **Low Priority** - Standard processing recommended")
                    else:
                        st.error("❌ Failed to save claim. Please try again.")
    
    def render_claims_history(self):
        """Render claims history and management"""
        st.header("📚 Claims History")
        
        claims = self.load_claims()
        
        if not claims:
            st.info("No claims submitted yet. Submit your first claim above!")
            return
            
        # Convert to DataFrame for better display
        df = pd.DataFrame(claims)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Claims", len(claims))
        with col2:
            st.metric("Pending", len([c for c in claims if c['status'] == 'pending']))
        with col3:
            st.metric("Categories", df['category'].nunique())
        with col4:
            st.metric("This Week", len(df[df['created_at'] > datetime.now() - timedelta(days=7)]))
        
        # Claims table
        st.subheader("Recent Claims")
        
        # Display claims in an interactive table
        for _, claim in df.head(10).iterrows():
            with st.expander(f"🎯 {claim['title']} ({claim['category']})", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {claim['description']}")
                    st.write(f"**Keywords:** {', '.join(claim['keywords'])}")
                with col2:
                    st.write(f"**Priority:** {claim['priority']}")
                    st.write(f"**Language:** {claim['language']}")
                    st.write(f"**Platforms:** {', '.join(claim['target_platforms'])}")
                    st.write(f"**Created:** {claim['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Status:** {claim['status']}")

def main():
    """Main function for testing the claim input system"""
    st.set_page_config(
        page_title="InsightPulse - Claim Input",
        page_icon="🎯",
        layout="wide"
    )
    
    claim_system = ClaimInputSystem()
    
    tab1, tab2 = st.tabs(["📝 Submit Claim", "📚 Claims History"])
    
    with tab1:
        claim_system.render_input_form()
    
    with tab2:
        claim_system.render_claims_history()

if __name__ == "__main__":
    main()
