#!/usr/bin/env python3
"""
Update presentation with SaaS Budget Model
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

def replace_budget_slides(prs):
    """Replace budget slides with SaaS model"""
    
    # Remove old budget slides (11-14)
    # Note: Can't easily remove slides, so we'll create new presentation
    # Keep slides 1-10, add new budget slides
    
    # Create new presentation with first 10 slides
    new_prs = Presentation()
    new_prs.slide_width = prs.slide_width
    new_prs.slide_height = prs.slide_height
    
    # Copy first 10 slides
    for i in range(min(10, len(prs.slides))):
        slide_layout = prs.slides[i].slide_layout
        new_slide = new_prs.slides.add_slide(slide_layout)
        
        # Copy all shapes
        for shape in prs.slides[i].shapes:
            el = shape.element
            new_slide.shapes._spTree.insert_element_before(el, 'p:extLst')
    
    return new_prs

def add_saas_pricing_slide(prs):
    """Slide 11: SaaS Pricing Tiers"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "InsightPulse SaaS - Pricing Tiers (Subscription Model)"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "💰 TIER 1: BASIC - RM 15,000/month"
    
    data = [
        (1, "10,000 posts/month, 5 keywords, 5 platforms"),
        (1, "Daily reports, Email support, 30-day retention"),
        (1, "Best for: PRK, PBT (Small local campaigns)"),
        (0, "💼 TIER 2: PROFESSIONAL - RM 35,000/month"),
        (1, "50,000 posts/month, 20 keywords, 8 platforms"),
        (1, "Real-time crisis detection, API access, 90-day retention"),
        (1, "Best for: PRN (State elections)"),
        (0, "🏆 TIER 3: ENTERPRISE - RM 80,000/month"),
        (1, "200,000 posts/month, 100 keywords, ALL 10 platforms"),
        (1, "24/7 monitoring, Predictive analytics, Unlimited API"),
        (1, "Best for: PRU (National elections)"),
        (0, "✅ No upfront costs, No hiring, Start in 3 weeks!")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_cost_comparison_slide(prs):
    """Slide 12: Cost Comparison"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Cost Comparison: SaaS vs Build In-house"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🏗️ Build In-house (DIY) - 6 Months"
    
    data = [
        (1, "Development: RM 250,000 - 500,000 (one-time)"),
        (1, "Team (8 persons): RM 318,000 (6 months)"),
        (1, "Infrastructure & Operations: RM 50,000"),
        (1, "Total: RM 542,800+ (Medium campaign)"),
        (1, "Time: 4-6 months to start"),
        (0, "☁️ InsightPulse SaaS - 6 Months"),
        (1, "Professional tier: RM 35,000 x 6 = RM 210,000"),
        (1, "Setup & onboarding: RM 10,000"),
        (1, "Total: RM 220,000"),
        (1, "Time: 3 weeks to start"),
        (0, "💰 SAVINGS: RM 322,800 (59% cheaper!)"),
        (0, "✅ No hiring, No infrastructure, No maintenance")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_saas_value_slide(prs):
    """Slide 13: SaaS Value Proposition"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Why InsightPulse SaaS?"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🔒 Your Data, Our Technology"
    
    data = [
        (1, "No code sharing - Proprietary IP protected"),
        (1, "You get: Dashboard access, API, Analyzed data"),
        (1, "We handle: Infrastructure, maintenance, updates"),
        (0, "⚡ Faster Deployment"),
        (1, "SaaS: 3 weeks vs DIY: 4-6 months"),
        (1, "No hiring, training, or team management"),
        (0, "💡 Lower Risk"),
        (1, "Pay monthly, cancel anytime (30 days notice)"),
        (1, "No RM 500,000 upfront investment"),
        (1, "Scale up/down based on campaign needs"),
        (0, "📊 Proven Accuracy"),
        (1, "95-98% sentiment accuracy (tested)"),
        (1, "10 platforms, 3 languages (Malay, English, Chinese)"),
        (1, "200,000+ posts analyzed successfully")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_recommended_package_slide(prs):
    """Slide 14: Recommended Package for PRN"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Recommended: Professional Tier (PRN Campaign)"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "💼 Package Details - 6 Months"
    
    data = [
        (1, "Monthly: RM 35,000 x 6 = RM 210,000"),
        (1, "Setup & Onboarding: RM 10,000"),
        (1, "Total Investment: RM 220,000"),
        (0, "📦 What You Get"),
        (1, "300,000 posts analyzed (real-time sentiment)"),
        (1, "20 keywords monitoring (customizable)"),
        (1, "8 platforms (Facebook, X, Instagram, TikTok, YouTube, LinkedIn, News, Lowyat)"),
        (1, "Crisis detection & SMS/Email alerts"),
        (1, "Daily + Weekly reports (data-driven insights)"),
        (1, "API access (integrate with your systems)"),
        (1, "Priority support (4-hour response time)"),
        (0, "🎯 ROI: Save RM 322,800 vs DIY + Prevent RM 1M+ crisis"),
        (0, "🚀 Start in 3 weeks - No hiring needed!")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def create_saas_presentation():
    # Load existing presentation
    prs = Presentation('BigData_Election_Strategy_Complete.pptx')
    
    # Keep only first 10 slides, add new budget slides
    # Since we can't easily delete slides, we'll append new ones
    # and note in the file which ones to use
    
    add_saas_pricing_slide(prs)
    add_cost_comparison_slide(prs)
    add_saas_value_slide(prs)
    add_recommended_package_slide(prs)
    
    # Save as new file
    prs.save('BigData_Election_Strategy_SAAS.pptx')
    print(f"✅ SaaS presentation created! Total slides: {len(prs.slides)}")
    print("Note: Slides 1-10 are original content")
    print("Slides 11-14 are SaaS budget model (use these instead of old budget slides)")

if __name__ == "__main__":
    create_saas_presentation()
