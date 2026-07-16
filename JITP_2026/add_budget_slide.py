#!/usr/bin/env python3
"""
Add Budget Slide to Election Strategy Presentation
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def add_budget_slide(prs):
    """Add Budget Recommendation Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Cadangan Belanjawan - Big Data Analytics"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "💰 Platform & Tools (Monthly)"
    
    data = [
        (1, "InsightPulse Platform: RM 5,000 - 10,000"),
        (1, "Apify Crawling Credits: RM 3,000 - 5,000"),
        (1, "SerpAPI (News monitoring): RM 500 - 1,000"),
        (1, "Cloud Storage (AWS/Azure): RM 1,000 - 2,000"),
        (0, "👥 Human Resources (Monthly)"),
        (1, "Data Analyst (1-2 pax): RM 8,000 - 15,000"),
        (1, "Social Media Strategist (1 pax): RM 6,000 - 10,000"),
        (1, "Content Writer/Responder (2 pax): RM 5,000 - 8,000"),
        (0, "📊 Total Monthly Budget"),
        (1, "Small Campaign: RM 25,000 - 40,000/bulan"),
        (1, "Medium Campaign: RM 50,000 - 80,000/bulan"),
        (1, "Large Campaign (PRU): RM 100,000 - 200,000/bulan"),
        (0, "🎯 ROI & Benefits"),
        (1, "Crisis prevention worth 10x investment"),
        (1, "Data-driven decisions reduce waste by 30-40%"),
        (1, "Targeted messaging increases engagement by 50%")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_implementation_timeline_slide(prs):
    """Add Implementation Timeline Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Timeline Pelaksanaan - 3 Fasa"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "📅 FASA 1: Setup & Training (Week 1-2)"
    
    data = [
        (1, "Platform setup & API configuration"),
        (1, "Define keywords & monitoring strategy"),
        (1, "Team training (2-3 hari)"),
        (1, "Budget: RM 15,000 - 25,000"),
        (0, "📅 FASA 2: Pilot Testing (Week 3-4)"),
        (1, "Monitor 3-5 keywords"),
        (1, "Test crisis response protocol"),
        (1, "Fine-tune sentiment models"),
        (1, "Budget: RM 20,000 - 35,000"),
        (0, "📅 FASA 3: Full Deployment (Ongoing)"),
        (1, "24/7 real-time monitoring"),
        (1, "Daily sentiment reports"),
        (1, "Weekly strategy meetings"),
        (1, "Budget: RM 50,000 - 150,000/bulan"),
        (0, "⏱️ Total Setup: 4 minggu | 💰 Total Initial: RM 85,000 - 210,000")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_cost_breakdown_slide(prs):
    """Add Detailed Cost Breakdown Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Pecahan Kos Terperinci"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "💻 Technology Stack (One-time + Monthly)"
    
    data = [
        (1, "InsightPulse License: RM 10,000 (setup) + RM 8,000/bulan"),
        (1, "Apify Credits: RM 5,000/bulan (500,000 results)"),
        (1, "SerpAPI: RM 800/bulan (unlimited searches)"),
        (1, "AWS/Azure Hosting: RM 1,500/bulan"),
        (1, "Database & Storage: RM 500/bulan"),
        (0, "📱 Campaign Operations (Monthly)"),
        (1, "3 Data Analysts: RM 25,000/bulan"),
        (1, "2 Content Strategists: RM 18,000/bulan"),
        (1, "1 Tech Support: RM 8,000/bulan"),
        (0, "📊 Additional Costs (Optional)"),
        (1, "Training & Workshops: RM 5,000 (quarterly)"),
        (1, "Consultant/Advisor: RM 10,000/bulan"),
        (1, "Emergency Response Fund: RM 20,000 (reserve)"),
        (0, "💰 TOTAL: RM 76,800/bulan + RM 10,000 setup")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_roi_analysis_slide(prs):
    """Add ROI Analysis Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Return on Investment (ROI) Analysis"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "💡 Cost Savings"
    
    data = [
        (1, "Prevent 1 major crisis: Save RM 500,000 - 2,000,000"),
        (1, "Reduce ineffective advertising: Save 30-40%"),
        (1, "Targeted campaigns vs broadcast: 3x efficiency"),
        (0, "📈 Revenue/Value Generation"),
        (1, "Increased voter engagement: +50%"),
        (1, "Better resource allocation: +40% efficiency"),
        (1, "Win marginal seats: Priceless"),
        (0, "⚖️ ROI Calculation (Medium Campaign)"),
        (1, "Investment: RM 80,000/bulan x 6 bulan = RM 480,000"),
        (1, "Crisis prevention value: RM 1,000,000+"),
        (1, "Ad waste reduction: RM 300,000+"),
        (1, "Net ROI: 200-300% minimum"),
        (0, "✅ Breakeven: After 2-3 major crisis prevented")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def update_presentation():
    # Load existing presentation
    prs = Presentation('BigData_Election_Strategy_Complete.pptx')
    
    # Add new slides before conclusion (slide 9 is conclusion, insert before)
    # We'll add 4 new budget-related slides
    
    # Note: We need to add slides AFTER the existing slides
    add_budget_slide(prs)
    add_implementation_timeline_slide(prs)
    add_cost_breakdown_slide(prs)
    add_roi_analysis_slide(prs)
    
    # Save updated presentation
    prs.save('BigData_Election_Strategy_Complete.pptx')
    print("✅ Budget slides added! Total slides: " + str(len(prs.slides)))

if __name__ == "__main__":
    update_presentation()
