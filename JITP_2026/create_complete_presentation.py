#!/usr/bin/env python3
"""
Complete PowerPoint Presentation:
Big Data & Analytic: Strategi Pilihan Raya dan Taktikal
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def add_title_slide(prs):
    """Slide 1: Title"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1))
    tf = title_box.text_frame
    tf.text = "Big Data & Analytic"
    p = tf.paragraphs[0]
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 51, 102)
    p.alignment = PP_ALIGN.CENTER
    
    subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.5), Inches(9), Inches(1))
    tf2 = subtitle_box.text_frame
    tf2.text = "Strategi Pilihan Raya dan Taktikal"
    p2 = tf2.paragraphs[0]
    p2.font.size = Pt(36)
    p2.font.color.rgb = RGBColor(192, 0, 0)
    p2.alignment = PP_ALIGN.CENTER
    
    author_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(0.5))
    tf3 = author_box.text_frame
    tf3.text = "InsightPulse Analytics Platform"
    p3 = tf3.paragraphs[0]
    p3.font.size = Pt(20)
    p3.font.italic = True
    p3.alignment = PP_ALIGN.CENTER

def add_agenda_slide(prs):
    """Slide 2: Agenda"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Agenda"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "Pengenalan Big Data dalam Politik"
    
    for text in [
        "Kepentingan Analytics dalam Pilihan Raya",
        "Platform InsightPulse - Tools Monitoring",
        "Strategi Taktikal Menggunakan Data",
        "Case Study & Contoh Aplikasi",
        "Kesimpulan & Q&A"
    ]:
        p = tf.add_paragraph()
        p.text = text
        p.level = 0

def add_bigdata_intro_slide(prs):
    """Slide 3: Big Data Introduction"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Big Data dalam Politik: Era Baru Kempen"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "✅ Volume Data Besar-besaran"
    
    data = [
        (1, "Jutaan posting media sosial setiap hari"),
        (1, "10 platform: Facebook, Instagram, X, TikTok, YouTube, LinkedIn, News, Lowyat, Shopee, Lazada"),
        (0, "✅ Kelajuan & Masa Nyata (Real-time)"),
        (1, "Sentiment berubah dalam masa nyata"),
        (1, "Crisis detection dalam minit"),
        (0, "✅ Kepelbagaian Data"),
        (1, "Text, images, videos, engagement metrics"),
        (1, "Multilingual: Malay, English, Chinese")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_analytics_importance_slide(prs):
    """Slide 4: Analytics Importance"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Kepentingan Analytics dalam Pilihan Raya"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🎯 Fahami Sentiment Pengundi"
    
    data = [
        (1, "Positive, Neutral, Negative - masa nyata"),
        (1, "Emosi: Joy, Anger, Fear, Sadness, Love, Surprise"),
        (0, "📊 Monitor Isu Trending"),
        (1, "Topik panas dalam kalangan pengundi"),
        (1, "Viral detection & response strategy"),
        (0, "⚠️ Crisis Detection"),
        (1, "Detect negative sentiment spikes"),
        (1, "Response dalam 15-30 minit"),
        (0, "📍 Geographic & Demographic Insights"),
        (1, "Sentiment by location & demographics"),
        (1, "Targeted campaign strategies")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_insightpulse_slide(prs):
    """Slide 5: InsightPulse Platform"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "InsightPulse - Platform Analytics Pilihan Raya"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🚀 Features Utama"
    
    data = [
        (1, "10 Platform Monitoring (Social Media + E-commerce)"),
        (1, "Multilingual AI: Malay, English, Chinese"),
        (1, "Real-time Sentiment & Emotion Analysis"),
        (1, "Crisis Detection & Alerts"),
        (1, "Trend Analysis & Forecasting"),
        (0, "📈 Metrics Penting"),
        (1, "Engagement Score (likes + shares + comments + views)"),
        (1, "Sentiment Score (-1 to +1)"),
        (1, "Viral Coefficient & Reach"),
        (0, "💾 Data Storage"),
        (1, "Raw Data: 30-day retention"),
        (1, "Analyzed Data: 7-day retention"),
        (1, "Combined Cross-platform Data")
    ]
    
    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_tactical_strategy_slide(prs):
    """Slide 6: Tactical Strategies"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Strategi Taktikal Menggunakan Big Data"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🎯 Strategi 1: Monitoring Lawan"

    data = [
        (1, "Track sentiment terhadap lawan"),
        (1, "Identify weaknesses & attack points"),
        (0, "🎯 Strategi 2: Micro-targeting"),
        (1, "Segment pengundi by demographics"),
        (1, "Personalized messaging per segment"),
        (0, "🎯 Strategi 3: Rapid Response"),
        (1, "Monitor negative sentiment spikes"),
        (1, "Response strategy dalam 15-30 minit"),
        (0, "🎯 Strategi 4: Content Optimization"),
        (1, "Test A/B messaging"),
        (1, "Optimize posting time & format")
    ]

    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_sample_keywords_slide(prs):
    """Slide 7: Sample Keywords for Election Monitoring"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Sample Keywords - InsightPulse Monitoring"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "🔍 Election General Keywords"

    data = [
        (1, "PRU16, PRN Selangor, Pilihan Raya Negeri"),
        (1, "Pengundi, Mengundi, Daftar Undi"),
        (0, "🔍 Party & Candidate Keywords"),
        (1, "Pakatan Harapan, Perikatan Nasional, Barisan Nasional"),
        (1, "[Nama Calon], [Nama Ketua Parti]"),
        (0, "🔍 Issue-Based Keywords"),
        (1, "Kos Sara Hidup, Inflasi, Gaji Minimum"),
        (1, "Corruption, Rasuah, Integriti"),
        (1, "Pendidikan, Kesihatan, Perumahan"),
        (0, "🔍 Sentiment Keywords"),
        (1, "Kecewa, Harapan, Marah, Gembira"),
        (1, "Sokong, Tolak, Tukar, Ubah")
    ]

    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_case_study_slide(prs):
    """Slide 8: Case Study"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Case Study: Monitoring Pilihan Raya PBT"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "📊 Data Collection"

    data = [
        (1, "Keywords: 'Pilihan Raya PBT', 'PKS', 'Election'"),
        (1, "Platforms: Facebook, X, Instagram, News"),
        (1, "Dataset: 500+ posts & comments"),
        (0, "📈 Analysis Results"),
        (1, "Sentiment: 45% Positive, 30% Neutral, 25% Negative"),
        (1, "Top Emotions: Joy (35%), Anger (20%), Neutral (45%)"),
        (1, "Peak Engagement: 8-10 PM daily"),
        (0, "🎯 Actionable Insights"),
        (1, "Positive sentiment on education & infrastructure"),
        (1, "Negative sentiment on corruption & transparency"),
        (1, "Recommendation: Focus on anti-corruption messaging")
    ]

    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_data_flow_slide(prs):
    """Slide 9: InsightPulse Data Flow"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "InsightPulse: Data Flow Pipeline"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "1️⃣ Data Collection"

    data = [
        (1, "Crawl 10 platforms simultaneously"),
        (1, "Store raw data: data/smart_crawlers/PLATFORM/"),
        (0, "2️⃣ AI Analysis"),
        (1, "Sentiment Analysis (Multilingual)"),
        (1, "Emotion Detection (8 emotions)"),
        (1, "Engagement Scoring"),
        (0, "3️⃣ Data Storage"),
        (1, "Analyzed data: data/analyzed/"),
        (1, "Combined cross-platform: data/combined/"),
        (0, "4️⃣ Visualization & Insights"),
        (1, "Real-time dashboard"),
        (1, "Trend graphs & sentiment timeline"),
        (1, "Export to Excel/CSV for reporting")
    ]

    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def add_conclusion_slide(prs):
    """Slide 10: Conclusion"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Kesimpulan"
    content = slide.placeholders[1]
    tf = content.text_frame
    tf.text = "✅ Big Data = Competitive Advantage"

    data = [
        (1, "Real-time insights untuk decision making"),
        (1, "Data-driven campaign strategies"),
        (0, "✅ InsightPulse = Complete Solution"),
        (1, "10 platforms monitoring"),
        (1, "Multilingual AI analysis"),
        (1, "Crisis detection & rapid response"),
        (0, "✅ Next Steps"),
        (1, "Define keywords for monitoring"),
        (1, "Setup automated daily reports"),
        (1, "Train team on data interpretation"),
        (0, "🙏 Terima Kasih! Q&A")
    ]

    for level, text in data:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    add_title_slide(prs)
    add_agenda_slide(prs)
    add_bigdata_intro_slide(prs)
    add_analytics_importance_slide(prs)
    add_insightpulse_slide(prs)
    add_tactical_strategy_slide(prs)
    add_sample_keywords_slide(prs)
    add_case_study_slide(prs)
    add_data_flow_slide(prs)
    add_conclusion_slide(prs)

    prs.save('BigData_Election_Strategy_Complete.pptx')
    print("✅ Complete presentation created (10 slides)")

if __name__ == "__main__":
    create_presentation()
