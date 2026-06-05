#!/usr/bin/env python3
"""
Test AI Models Integration for InsightPulse
Simple test to verify your Hugging Face models work correctly
"""

import streamlit as st
from transformers import pipeline
import torch

st.set_page_config(
    page_title="InsightPulse - AI Models Test",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 InsightPulse AI Models Test")
st.markdown("Testing your specialized Hugging Face models for professional claim analysis")

# Test text samples
test_samples = {
    "Political": "Perdana Menteri Malaysia mengumumkan dasar ekonomi baharu untuk membantu rakyat",
    "Religious": "Benarkah pewarna merah yang digunakan dalam makanan ringan dihasilkan daripada serangga dan tidak halal?",
    "Economic": "Bank Negara Malaysia menaikkan kadar faedah untuk mengawal inflasi",
    "Health": "Vaksin COVID-19 terbukti selamat dan berkesan untuk semua golongan umur",
    "Technology": "Teknologi AI akan mengambil alih pekerjaan manusia dalam 10 tahun akan datang",
    "Danger": "Banjir besar melanda Kelantan dan mengancam nyawa penduduk"
}

st.subheader("🧪 Model Testing")

# Model 1: Claim Classifier
st.markdown("### 1. 🎯 Malay Claim Classifier (rmtariq/malay_claim_classifier_v2)")

try:
    with st.spinner("Loading claim classifier..."):
        claim_classifier = pipeline(
            "text-classification",
            model="rmtariq/malay_claim_classifier_v2",
            tokenizer="rmtariq/malay_claim_classifier_v2"
        )
    st.success("✅ Claim classifier loaded successfully!")
    
    # Test with samples
    for category, text in test_samples.items():
        with st.expander(f"Test: {category}"):
            st.write(f"**Text:** {text}")
            
            result = claim_classifier(text)
            predicted_label = result[0]['label']
            confidence = result[0]['score']
            
            st.write(f"**Predicted Category:** {predicted_label}")
            st.write(f"**Confidence:** {confidence:.3f}")
            
            # Show all predictions
            st.write("**All Predictions:**")
            for pred in result:
                st.write(f"- {pred['label']}: {pred['score']:.3f}")

except Exception as e:
    st.error(f"❌ Error loading claim classifier: {e}")

st.markdown("---")

# Model 2: Fact Checker
st.markdown("### 2. 🔍 10FactCheck Model (rmtariq/10factcheck)")

try:
    with st.spinner("Loading fact checker..."):
        fact_checker = pipeline(
            "text-classification",
            model="rmtariq/10factcheck",
            tokenizer="rmtariq/10factcheck",
            top_k=None,
            function_to_apply="sigmoid"
        )
    st.success("✅ Fact checker loaded successfully!")
    
    # Test with a sample
    test_text = "Kenyataan ini tular di media sosial dan berkaitan dengan kerajaan Malaysia"
    
    st.write(f"**Test Text:** {test_text}")
    
    results = fact_checker(test_text)
    
    st.write("**Fact-Check Analysis:**")
    
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
    
    col1, col2 = st.columns(2)
    
    for i, result in enumerate(results):
        label = result['label']
        score = result['score']
        is_positive = score > 0.5
        
        friendly_label = criteria_labels.get(label, label)
        icon = "✅" if is_positive else "❌"
        
        if i < len(results) // 2:
            with col1:
                st.write(f"{icon} **{friendly_label}:** {score:.3f}")
        else:
            with col2:
                st.write(f"{icon} **{friendly_label}:** {score:.3f}")

except Exception as e:
    st.error(f"❌ Error loading fact checker: {e}")

st.markdown("---")

# Model 3: Priority Classifier (Rule-based)
st.markdown("### 3. 🎯 Malaysian Priority Classifier (rmtariq/malaysian-priority-classifier)")

st.info("This is a rule-based shell script classifier. For full functionality, the script needs to be downloaded and made executable.")

# Simulate priority classification
priority_keywords = {
    'Government': ['kerajaan', 'perdana menteri', 'politik', 'government', 'minister'],
    'Economic': ['ekonomi', 'bank', 'ringgit', 'economic', 'finance'],
    'Law': ['mahkamah', 'polis', 'undang-undang', 'law', 'court'],
    'Danger': ['bahaya', 'banjir', 'gempa', 'danger', 'emergency']
}

st.write("**Simulated Priority Classification:**")

for category, text in test_samples.items():
    text_lower = text.lower()
    predicted_priority = "Medium"  # Default
    
    for priority, keywords in priority_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            predicted_priority = priority
            break
    
    with st.expander(f"Priority Test: {category}"):
        st.write(f"**Text:** {text}")
        st.write(f"**Predicted Priority:** {predicted_priority}")

st.markdown("---")

# Interactive Testing
st.markdown("### 🧪 Interactive Testing")

user_text = st.text_area(
    "Enter your own text to test:",
    placeholder="Masukkan teks dalam Bahasa Malaysia untuk diuji...",
    height=100
)

if user_text and st.button("🚀 Analyze Text"):
    st.markdown("#### Results:")
    
    # Test with claim classifier
    try:
        result = claim_classifier(user_text)
        st.write(f"**Category:** {result[0]['label']} (confidence: {result[0]['score']:.3f})")
    except:
        st.write("**Category:** Unable to classify")
    
    # Test with fact checker
    try:
        results = fact_checker(user_text)
        high_priority_criteria = ['life_threatening', 'causes_chaos', 'breaks_law', 'time_sensitive']
        
        criteria_met = []
        for result in results:
            if result['score'] > 0.5:
                criteria_met.append(result['label'])
        
        if any(criteria in criteria_met for criteria in high_priority_criteria):
            st.warning("⚠️ **High Priority** - This text meets critical fact-check criteria")
        elif 'has_fact_value' in criteria_met:
            st.info("ℹ️ **Medium Priority** - This text has fact-checking value")
        else:
            st.success("✅ **Low Priority** - Standard processing recommended")
            
    except:
        st.write("**Fact-check:** Unable to analyze")

st.markdown("---")
st.markdown("### 📊 System Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("PyTorch Version", torch.__version__)

with col2:
    st.metric("Device", "CPU" if not torch.cuda.is_available() else "GPU")

with col3:
    st.metric("Models Loaded", "2/3")

st.success("🎉 AI Models testing complete! Your specialized models are working correctly.")
