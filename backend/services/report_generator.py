"""
🎯 Professional Report Generation System
Generates comprehensive reports for all analysis types:
- Politics, SME, Issues, Research, Government, etc.

Outputs:
1. dashboard.html - Interactive dashboard
2. Management_Presentation.pptx - PowerPoint
3. EXECUTIVE_SUMMARY.md - Executive summary
4. PUBLIC_COMMUNICATION_PLAN.md - Communication plan
5. most_negative_posts.csv - Negative posts
6. most_positive_posts.csv - Positive posts
7. platform_comparison.csv - Platform comparison
8. top_comments_by_engagement.csv - Top comments
9. top_posts_by_engagement.csv - Top posts
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProfessionalReportGenerator:
    """Generate professional reports for stakeholders"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_all_reports(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str
    ) -> Dict[str, str]:
        """
        Generate all 9 professional reports
        
        Args:
            analysis_data: Complete analysis results
            query: Original search query
            analysis_type: Type of analysis (social_listening, brand_monitoring, etc.)
            
        Returns:
            Dictionary mapping report type to file path
        """
        logger.info(f"🎯 Generating professional reports for: {query}")
        
        # Create timestamped folder for this analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        report_folder = self.output_dir / f"{timestamp}_{safe_query}"
        report_folder.mkdir(exist_ok=True)
        
        logger.info(f"📁 Report folder: {report_folder}")
        
        report_paths = {}
        
        try:
            # 1. Generate CSV exports (fastest, do first)
            logger.info("📊 Generating CSV exports...")
            report_paths.update(self._generate_csv_exports(analysis_data, report_folder))
            
            # 2. Generate Executive Summary
            logger.info("📝 Generating Executive Summary...")
            report_paths['executive_summary'] = self._generate_executive_summary(
                analysis_data, query, analysis_type, report_folder
            )
            
            # 3. Generate Communication Plan
            logger.info("📢 Generating Communication Plan...")
            report_paths['communication_plan'] = self._generate_communication_plan(
                analysis_data, query, analysis_type, report_folder
            )
            
            # 4. Generate Interactive Dashboard
            logger.info("📊 Generating Interactive Dashboard...")
            report_paths['dashboard'] = self._generate_dashboard_html(
                analysis_data, query, analysis_type, report_folder
            )
            
            # 5. Generate PowerPoint Presentation
            logger.info("📊 Generating PowerPoint Presentation...")
            report_paths['presentation'] = self._generate_powerpoint(
                analysis_data, query, analysis_type, report_folder
            )

            # 6. Generate DOCX versions of Executive Summary and Communication Plan
            logger.info("📄 Generating DOCX documents...")
            report_paths['executive_summary_docx'] = self._generate_executive_summary_docx(
                analysis_data, query, analysis_type, report_folder
            )
            report_paths['communication_plan_docx'] = self._generate_communication_plan_docx(
                analysis_data, query, analysis_type, report_folder
            )

            logger.info(f"✅ All reports generated successfully in: {report_folder}")

            return report_paths
            
        except Exception as e:
            logger.error(f"❌ Error generating reports: {e}")
            raise
    
    def _generate_csv_exports(
        self,
        analysis_data: Dict[str, Any],
        report_folder: Path
    ) -> Dict[str, str]:
        """Generate 5 CSV export files"""
        csv_paths = {}
        
        # Extract data from analysis
        all_posts = analysis_data.get('raw_data', [])
        sentiment_data = analysis_data.get('sentiment_analysis', {})
        
        # 1. Most Negative Posts
        negative_posts = self._get_most_negative_posts(all_posts, sentiment_data)
        csv_paths['most_negative'] = self._write_csv(
            negative_posts,
            report_folder / "most_negative_posts.csv",
            ['platform', 'content', 'sentiment_score', 'engagement', 'url', 'date']
        )
        
        # 2. Most Positive Posts
        positive_posts = self._get_most_positive_posts(all_posts, sentiment_data)
        csv_paths['most_positive'] = self._write_csv(
            positive_posts,
            report_folder / "most_positive_posts.csv",
            ['platform', 'content', 'sentiment_score', 'engagement', 'url', 'date']
        )
        
        # 3. Platform Comparison
        platform_comparison = self._get_platform_comparison(all_posts, sentiment_data)
        csv_paths['platform_comparison'] = self._write_csv(
            platform_comparison,
            report_folder / "platform_comparison.csv",
            ['platform', 'total_posts', 'avg_sentiment', 'total_engagement', 'positive_ratio', 'negative_ratio']
        )
        
        # 4. Top Comments by Engagement
        top_comments = self._get_top_comments(all_posts)
        csv_paths['top_comments'] = self._write_csv(
            top_comments,
            report_folder / "top_comments_by_engagement.csv",
            ['platform', 'post_content', 'comment_content', 'engagement', 'sentiment', 'date']
        )
        
        # 5. Top Posts by Engagement
        top_posts = self._get_top_posts(all_posts)
        csv_paths['top_posts'] = self._write_csv(
            top_posts,
            report_folder / "top_posts_by_engagement.csv",
            ['platform', 'content', 'engagement', 'likes', 'comments', 'shares', 'sentiment', 'url', 'date']
        )
        
        return csv_paths

    def _get_most_negative_posts(self, posts: List[Dict], sentiment_data: Dict) -> List[Dict]:
        """Get top 50 most negative posts"""
        posts_with_sentiment = []
        for post in posts:
            sentiment_score = post.get('sentiment_score', 0)
            if sentiment_score < 0:  # Negative sentiment
                posts_with_sentiment.append({
                    'platform': post.get('platform', 'Unknown'),
                    'content': post.get('text', '')[:200],  # First 200 chars
                    'sentiment_score': sentiment_score,
                    'engagement': post.get('engagement', {}).get('total', 0),
                    'url': post.get('url', ''),
                    'date': post.get('created_at', '')
                })

        # Sort by sentiment score (most negative first)
        posts_with_sentiment.sort(key=lambda x: x['sentiment_score'])
        return posts_with_sentiment[:50]

    def _get_most_positive_posts(self, posts: List[Dict], sentiment_data: Dict) -> List[Dict]:
        """Get top 50 most positive posts"""
        posts_with_sentiment = []
        for post in posts:
            sentiment_score = post.get('sentiment_score', 0)
            if sentiment_score > 0:  # Positive sentiment
                posts_with_sentiment.append({
                    'platform': post.get('platform', 'Unknown'),
                    'content': post.get('text', '')[:200],
                    'sentiment_score': sentiment_score,
                    'engagement': post.get('engagement', {}).get('total', 0),
                    'url': post.get('url', ''),
                    'date': post.get('created_at', '')
                })

        # Sort by sentiment score (most positive first)
        posts_with_sentiment.sort(key=lambda x: x['sentiment_score'], reverse=True)
        return posts_with_sentiment[:50]

    def _get_platform_comparison(self, posts: List[Dict], sentiment_data: Dict) -> List[Dict]:
        """Compare metrics across platforms"""
        platform_stats = {}

        for post in posts:
            platform = post.get('platform', 'Unknown')
            if platform not in platform_stats:
                platform_stats[platform] = {
                    'total_posts': 0,
                    'total_sentiment': 0,
                    'total_engagement': 0,
                    'positive_count': 0,
                    'negative_count': 0
                }

            stats = platform_stats[platform]
            stats['total_posts'] += 1
            stats['total_sentiment'] += post.get('sentiment_score', 0)
            stats['total_engagement'] += post.get('engagement', {}).get('total', 0)

            if post.get('sentiment_score', 0) > 0:
                stats['positive_count'] += 1
            elif post.get('sentiment_score', 0) < 0:
                stats['negative_count'] += 1

        # Calculate averages and ratios
        comparison = []
        for platform, stats in platform_stats.items():
            total = stats['total_posts']
            comparison.append({
                'platform': platform,
                'total_posts': total,
                'avg_sentiment': round(stats['total_sentiment'] / total, 3) if total > 0 else 0,
                'total_engagement': stats['total_engagement'],
                'positive_ratio': round(stats['positive_count'] / total * 100, 1) if total > 0 else 0,
                'negative_ratio': round(stats['negative_count'] / total * 100, 1) if total > 0 else 0
            })

        # Sort by total engagement
        comparison.sort(key=lambda x: x['total_engagement'], reverse=True)
        return comparison

    def _get_top_comments(self, posts: List[Dict]) -> List[Dict]:
        """Get top 100 comments by engagement"""
        all_comments = []

        for post in posts:
            post_content = post.get('text', '')[:100]
            comments = post.get('comments', [])

            for comment in comments:
                all_comments.append({
                    'platform': post.get('platform', 'Unknown'),
                    'post_content': post_content,
                    'comment_content': comment.get('text', '')[:200],
                    'engagement': comment.get('likes', 0) + comment.get('replies', 0),
                    'sentiment': comment.get('sentiment_score', 0),
                    'date': comment.get('created_at', '')
                })

        # Sort by engagement
        all_comments.sort(key=lambda x: x['engagement'], reverse=True)
        return all_comments[:100]

    def _get_top_posts(self, posts: List[Dict]) -> List[Dict]:
        """Get top 100 posts by engagement"""
        posts_with_engagement = []

        for post in posts:
            engagement = post.get('engagement', {})
            posts_with_engagement.append({
                'platform': post.get('platform', 'Unknown'),
                'content': post.get('text', '')[:200],
                'engagement': engagement.get('total', 0),
                'likes': engagement.get('likes', 0),
                'comments': engagement.get('comments', 0),
                'shares': engagement.get('shares', 0),
                'sentiment': post.get('sentiment_score', 0),
                'url': post.get('url', ''),
                'date': post.get('created_at', '')
            })

        # Sort by total engagement
        posts_with_engagement.sort(key=lambda x: x['engagement'], reverse=True)
        return posts_with_engagement[:100]

    def _write_csv(self, data: List[Dict], filepath: Path, fieldnames: List[str]) -> str:
        """Write data to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"✅ CSV written: {filepath.name} ({len(data)} rows)")
            return str(filepath)
        except Exception as e:
            logger.error(f"❌ Error writing CSV {filepath.name}: {e}")
            return ""

    def _generate_executive_summary(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate executive summary markdown"""
        filepath = report_folder / "EXECUTIVE_SUMMARY.md"

        # Extract key metrics
        total_posts = len(analysis_data.get('raw_data', []))
        sentiment = analysis_data.get('sentiment_analysis', {})
        insights = analysis_data.get('insights', {})

        # Calculate key metrics
        positive_ratio = sentiment.get('positive_ratio', 0)
        negative_ratio = sentiment.get('negative_ratio', 0)
        neutral_ratio = sentiment.get('neutral_ratio', 0)

        # Get top platforms
        platform_data = analysis_data.get('platform_breakdown', {})

        content = f"""# EXECUTIVE SUMMARY
## {query}

**Analysis Type:** {analysis_type.replace('_', ' ').title()}
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Total Data Points:** {total_posts:,}

---

## 🎯 KEY FINDINGS

### Overall Sentiment
- **Positive:** {positive_ratio:.1f}%
- **Neutral:** {neutral_ratio:.1f}%
- **Negative:** {negative_ratio:.1f}%

### Sentiment Verdict
{self._get_sentiment_verdict(positive_ratio, negative_ratio)}

---

## 📊 PLATFORM BREAKDOWN

{self._format_platform_breakdown(platform_data)}

---

## 🔥 TOP INSIGHTS

{self._format_top_insights(insights)}

---

## ⚠️ CRITICAL ISSUES

{self._format_critical_issues(analysis_data)}

---

## 💡 RECOMMENDATIONS

{self._format_recommendations(analysis_type, analysis_data)}

---

## 📈 ACTION ITEMS

{self._format_action_items(analysis_type, analysis_data)}

---

## 📎 SUPPORTING DOCUMENTS

1. `dashboard.html` - Interactive visual dashboard
2. `Management_Presentation.pptx` - PowerPoint for stakeholders
3. `PUBLIC_COMMUNICATION_PLAN.md` - Communication strategy
4. `most_negative_posts.csv` - Negative sentiment posts
5. `most_positive_posts.csv` - Positive sentiment posts
6. `platform_comparison.csv` - Cross-platform analysis
7. `top_comments_by_engagement.csv` - High-engagement comments
8. `top_posts_by_engagement.csv` - Viral content analysis

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**System:** InsightPulse Professional Analytics
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Executive Summary generated: {filepath.name}")
        return str(filepath)

    def _get_sentiment_verdict(self, positive: float, negative: float) -> str:
        """Get overall sentiment verdict"""
        if positive > 60:
            return "✅ **HIGHLY POSITIVE** - Strong public support and favorable sentiment"
        elif positive > 40 and negative < 30:
            return "✅ **POSITIVE** - Generally favorable sentiment with room for improvement"
        elif negative > 50:
            return "⚠️ **HIGHLY NEGATIVE** - Significant concerns and negative sentiment detected"
        elif negative > 30:
            return "⚠️ **NEGATIVE** - Notable negative sentiment requiring attention"
        else:
            return "➖ **NEUTRAL** - Mixed sentiment, balanced public opinion"

    def _format_platform_breakdown(self, platform_data: Dict) -> str:
        """Format platform breakdown section"""
        if not platform_data:
            return "No platform data available"

        lines = []
        for platform, data in sorted(platform_data.items(), key=lambda x: x[1].get('total', 0), reverse=True):
            total = data.get('total', 0)
            sentiment = data.get('avg_sentiment', 0)
            lines.append(f"- **{platform.title()}**: {total:,} posts (Avg Sentiment: {sentiment:.2f})")

        return "\n".join(lines)

    def _format_top_insights(self, insights: Dict) -> str:
        """Format top insights"""
        insight_list = insights.get('key_insights', [])
        if not insight_list:
            return "Analysis in progress..."

        lines = []
        for i, insight in enumerate(insight_list[:5], 1):
            lines.append(f"{i}. {insight}")

        return "\n".join(lines)

    def _format_critical_issues(self, analysis_data: Dict) -> str:
        """Format critical issues"""
        issues = analysis_data.get('critical_issues', [])
        if not issues:
            return "No critical issues detected"

        lines = []
        for i, issue in enumerate(issues[:5], 1):
            lines.append(f"{i}. ⚠️ {issue}")

        return "\n".join(lines)

    def _format_recommendations(self, analysis_type: str, analysis_data: Dict) -> str:
        """Format recommendations based on analysis type"""
        recommendations = analysis_data.get('recommendations', [])
        if recommendations:
            return "\n".join([f"{i}. {rec}" for i, rec in enumerate(recommendations[:5], 1)])

        # Default recommendations by type
        if analysis_type == "brand_monitoring":
            return """1. Monitor negative sentiment trends closely
2. Engage with positive brand advocates
3. Address customer concerns promptly
4. Amplify positive testimonials
5. Track competitor mentions"""
        elif analysis_type == "issue_detection":
            return """1. Investigate root causes of negative sentiment
2. Prepare crisis communication plan
3. Monitor issue escalation
4. Engage with affected stakeholders
5. Implement corrective measures"""
        else:
            return """1. Continue monitoring sentiment trends
2. Engage with key influencers
3. Address negative feedback
4. Amplify positive content
5. Track emerging topics"""

    def _format_action_items(self, analysis_type: str, analysis_data: Dict) -> str:
        """Format action items"""
        return """### Immediate (24-48 hours)
- [ ] Review all negative posts and comments
- [ ] Prepare response to critical issues
- [ ] Brief stakeholders on findings

### Short-term (1-2 weeks)
- [ ] Implement communication plan
- [ ] Monitor sentiment changes
- [ ] Engage with key influencers

### Long-term (1-3 months)
- [ ] Track trend evolution
- [ ] Measure impact of interventions
- [ ] Refine strategy based on results"""

    def _generate_communication_plan(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate public communication plan"""
        from .report_templates import generate_communication_plan_template

        filepath = report_folder / "PUBLIC_COMMUNICATION_PLAN.md"
        content = generate_communication_plan_template(query, analysis_type, analysis_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Communication Plan generated: {filepath.name}")
        return str(filepath)

    def _generate_dashboard_html(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate interactive HTML dashboard"""
        from .report_templates import generate_dashboard_html_template

        filepath = report_folder / "dashboard.html"
        content = generate_dashboard_html_template(query, analysis_type, analysis_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Dashboard HTML generated: {filepath.name}")
        return str(filepath)

    def _generate_powerpoint(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate PowerPoint presentation"""
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            from pptx.enum.text import PP_ALIGN
            from pptx.dml.color import RGBColor
        except ImportError:
            logger.warning("⚠️ python-pptx not installed. Skipping PowerPoint generation.")
            logger.info("   Install with: pip install python-pptx")
            return ""

        filepath = report_folder / "Management_Presentation.pptx"

        try:
            # Create presentation
            prs = Presentation()
            prs.slide_width = Inches(10)
            prs.slide_height = Inches(7.5)

            # Extract data
            sentiment = analysis_data.get('sentiment_analysis', {})
            platform_data = analysis_data.get('platform_breakdown', {})
            total_posts = len(analysis_data.get('raw_data', []))

            positive_ratio = sentiment.get('positive_ratio', 0)
            negative_ratio = sentiment.get('negative_ratio', 0)
            neutral_ratio = sentiment.get('neutral_ratio', 0)

            # Slide 1: Title Slide
            slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

            # Add gradient background (simulated with colored rectangle)
            left = top = Inches(0)
            width = prs.slide_width
            height = prs.slide_height
            shape = slide.shapes.add_shape(1, left, top, width, height)  # Rectangle
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(102, 126, 234)
            shape.line.fill.background()

            # Title
            title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1))
            title_frame = title_box.text_frame
            title_frame.text = "InsightPulse Analytics Report"
            title_para = title_frame.paragraphs[0]
            title_para.font.size = Pt(44)
            title_para.font.bold = True
            title_para.font.color.rgb = RGBColor(255, 255, 255)
            title_para.alignment = PP_ALIGN.CENTER

            # Subtitle
            subtitle_box = slide.shapes.add_textbox(Inches(1), Inches(3.5), Inches(8), Inches(0.8))
            subtitle_frame = subtitle_box.text_frame
            subtitle_frame.text = query
            subtitle_para = subtitle_frame.paragraphs[0]
            subtitle_para.font.size = Pt(32)
            subtitle_para.font.color.rgb = RGBColor(255, 255, 255)
            subtitle_para.alignment = PP_ALIGN.CENTER

            # Date
            date_box = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(0.5))
            date_frame = date_box.text_frame
            date_frame.text = datetime.now().strftime('%B %d, %Y')
            date_para = date_frame.paragraphs[0]
            date_para.font.size = Pt(18)
            date_para.font.color.rgb = RGBColor(255, 255, 255)
            date_para.alignment = PP_ALIGN.CENTER

            # Slide 2: Executive Summary
            slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title and Content
            title = slide.shapes.title
            title.text = "Executive Summary"

            content = slide.placeholders[1]
            tf = content.text_frame
            tf.text = f"Total Data Points: {total_posts:,}"

            p = tf.add_paragraph()
            p.text = f"Analysis Type: {analysis_type.replace('_', ' ').title()}"
            p.level = 0

            p = tf.add_paragraph()
            p.text = f"Positive Sentiment: {positive_ratio:.1f}%"
            p.level = 0

            p = tf.add_paragraph()
            p.text = f"Neutral Sentiment: {neutral_ratio:.1f}%"
            p.level = 0

            p = tf.add_paragraph()
            p.text = f"Negative Sentiment: {negative_ratio:.1f}%"
            p.level = 0

            # Slide 3: Sentiment Analysis
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = "Sentiment Analysis"

            content = slide.placeholders[1]
            tf = content.text_frame

            if positive_ratio > 60:
                verdict = "✅ HIGHLY POSITIVE - Strong public support"
            elif positive_ratio > 40:
                verdict = "✅ POSITIVE - Generally favorable"
            elif negative_ratio > 50:
                verdict = "⚠️ HIGHLY NEGATIVE - Significant concerns"
            elif negative_ratio > 30:
                verdict = "⚠️ NEGATIVE - Notable negative sentiment"
            else:
                verdict = "➖ NEUTRAL - Mixed sentiment"

            tf.text = f"Overall Verdict: {verdict}"

            p = tf.add_paragraph()
            p.text = f"Positive: {positive_ratio:.1f}% ({int(total_posts * positive_ratio / 100):,} posts)"
            p.level = 1

            p = tf.add_paragraph()
            p.text = f"Neutral: {neutral_ratio:.1f}% ({int(total_posts * neutral_ratio / 100):,} posts)"
            p.level = 1

            p = tf.add_paragraph()
            p.text = f"Negative: {negative_ratio:.1f}% ({int(total_posts * negative_ratio / 100):,} posts)"
            p.level = 1

            # Slide 4: Platform Breakdown
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = "Platform Breakdown"

            content = slide.placeholders[1]
            tf = content.text_frame
            tf.text = "Performance by Platform:"

            for platform, data in sorted(platform_data.items(), key=lambda x: x[1].get('total', 0), reverse=True):
                p = tf.add_paragraph()
                total = data.get('total', 0)
                avg_sentiment = data.get('avg_sentiment', 0)
                p.text = f"{platform.title()}: {total:,} posts (Avg Sentiment: {avg_sentiment:.2f})"
                p.level = 1

            # Slide 5: Key Insights
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = "Key Insights"

            content = slide.placeholders[1]
            tf = content.text_frame

            insights = analysis_data.get('insights', {}).get('key_insights', [])
            if insights:
                tf.text = insights[0] if len(insights) > 0 else "Analysis in progress..."
                for insight in insights[1:5]:
                    p = tf.add_paragraph()
                    p.text = insight
                    p.level = 0
            else:
                tf.text = "• Comprehensive data collection across all platforms"
                p = tf.add_paragraph()
                p.text = "• Sentiment analysis using Malaysian-focused AI models"
                p = tf.add_paragraph()
                p.text = "• Real-time monitoring and trend detection"

            # Slide 6: Recommendations
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = "Recommendations"

            content = slide.placeholders[1]
            tf = content.text_frame
            tf.text = "Monitor negative sentiment trends closely"

            p = tf.add_paragraph()
            p.text = "Engage with positive brand advocates"

            p = tf.add_paragraph()
            p.text = "Address customer concerns promptly"

            p = tf.add_paragraph()
            p.text = "Amplify positive testimonials"

            p = tf.add_paragraph()
            p.text = "Track emerging topics and trends"

            # Slide 7: Action Items
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = "Action Items"

            content = slide.placeholders[1]
            tf = content.text_frame
            tf.text = "Immediate (24-48 hours):"

            p = tf.add_paragraph()
            p.text = "Review all negative posts and comments"
            p.level = 1

            p = tf.add_paragraph()
            p.text = "Prepare response to critical issues"
            p.level = 1

            p = tf.add_paragraph()
            p.text = "Short-term (1-2 weeks):"
            p.level = 0

            p = tf.add_paragraph()
            p.text = "Implement communication plan"
            p.level = 1

            p = tf.add_paragraph()
            p.text = "Monitor sentiment changes"
            p.level = 1

            # Save presentation
            prs.save(str(filepath))

            logger.info(f"✅ PowerPoint Presentation generated: {filepath.name}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error generating PowerPoint: {e}")
            return ""

    def _generate_executive_summary_docx(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate Executive Summary as DOCX"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            logger.warning("⚠️ python-docx not installed. Skipping DOCX generation.")
            logger.info("   Install with: pip install python-docx")
            return ""

        filepath = report_folder / "EXECUTIVE_SUMMARY.docx"

        try:
            # Create document
            doc = Document()

            # Set document margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)

            # Extract key metrics
            total_posts = len(analysis_data.get('raw_data', []))
            sentiment = analysis_data.get('sentiment_analysis', {})
            insights = analysis_data.get('insights', {})

            positive_ratio = sentiment.get('positive_ratio', 0)
            negative_ratio = sentiment.get('negative_ratio', 0)
            neutral_ratio = sentiment.get('neutral_ratio', 0)

            platform_data = analysis_data.get('platform_breakdown', {})

            # Title
            title = doc.add_heading('EXECUTIVE SUMMARY', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Subtitle
            subtitle = doc.add_heading(query, 1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Metadata
            meta = doc.add_paragraph()
            meta.add_run(f"Analysis Type: ").bold = True
            meta.add_run(f"{analysis_type.replace('_', ' ').title()}\n")
            meta.add_run(f"Date: ").bold = True
            meta.add_run(f"{datetime.now().strftime('%B %d, %Y')}\n")
            meta.add_run(f"Total Data Points: ").bold = True
            meta.add_run(f"{total_posts:,}")
            meta.alignment = WD_ALIGN_PARAGRAPH.CENTER

            doc.add_paragraph()  # Spacing

            # Key Findings
            doc.add_heading('🎯 KEY FINDINGS', 1)

            doc.add_heading('Overall Sentiment', 2)
            sentiment_para = doc.add_paragraph()
            sentiment_para.add_run(f"• Positive: ").bold = True
            sentiment_para.add_run(f"{positive_ratio:.1f}%\n")
            sentiment_para.add_run(f"• Neutral: ").bold = True
            sentiment_para.add_run(f"{neutral_ratio:.1f}%\n")
            sentiment_para.add_run(f"• Negative: ").bold = True
            sentiment_para.add_run(f"{negative_ratio:.1f}%")

            # Sentiment Verdict
            doc.add_heading('Sentiment Verdict', 2)
            verdict = self._get_sentiment_verdict(positive_ratio, negative_ratio)
            doc.add_paragraph(verdict)

            # Platform Breakdown
            doc.add_heading('📊 PLATFORM BREAKDOWN', 1)
            for platform, data in sorted(platform_data.items(), key=lambda x: x[1].get('total', 0), reverse=True):
                total = data.get('total', 0)
                sentiment_score = data.get('avg_sentiment', 0)
                platform_para = doc.add_paragraph(style='List Bullet')
                platform_para.add_run(f"{platform.title()}: ").bold = True
                platform_para.add_run(f"{total:,} posts (Avg Sentiment: {sentiment_score:.2f})")

            # Top Insights
            doc.add_heading('🔥 TOP INSIGHTS', 1)
            insight_list = insights.get('key_insights', [])
            if insight_list:
                for i, insight in enumerate(insight_list[:5], 1):
                    doc.add_paragraph(f"{i}. {insight}", style='List Number')
            else:
                doc.add_paragraph("Analysis in progress...")

            # Critical Issues
            doc.add_heading('⚠️ CRITICAL ISSUES', 1)
            issues = analysis_data.get('critical_issues', [])
            if issues:
                for issue in issues[:5]:
                    doc.add_paragraph(f"⚠️ {issue}", style='List Bullet')
            else:
                doc.add_paragraph("No critical issues detected")

            # Recommendations
            doc.add_heading('💡 RECOMMENDATIONS', 1)
            recommendations = self._format_recommendations(analysis_type, analysis_data)
            for line in recommendations.split('\n'):
                if line.strip():
                    doc.add_paragraph(line, style='List Number')

            # Action Items
            doc.add_heading('📈 ACTION ITEMS', 1)

            doc.add_heading('Immediate (24-48 hours)', 2)
            doc.add_paragraph("Review all negative posts and comments", style='List Bullet')
            doc.add_paragraph("Prepare response to critical issues", style='List Bullet')
            doc.add_paragraph("Brief stakeholders on findings", style='List Bullet')

            doc.add_heading('Short-term (1-2 weeks)', 2)
            doc.add_paragraph("Implement communication plan", style='List Bullet')
            doc.add_paragraph("Monitor sentiment changes", style='List Bullet')
            doc.add_paragraph("Engage with key influencers", style='List Bullet')

            doc.add_heading('Long-term (1-3 months)', 2)
            doc.add_paragraph("Track trend evolution", style='List Bullet')
            doc.add_paragraph("Measure impact of interventions", style='List Bullet')
            doc.add_paragraph("Refine strategy based on results", style='List Bullet')

            # Supporting Documents
            doc.add_heading('📎 SUPPORTING DOCUMENTS', 1)
            supporting_docs = [
                "dashboard.html - Interactive visual dashboard",
                "Management_Presentation.pptx - PowerPoint for stakeholders",
                "PUBLIC_COMMUNICATION_PLAN.docx - Communication strategy",
                "most_negative_posts.csv - Negative sentiment posts",
                "most_positive_posts.csv - Positive sentiment posts",
                "platform_comparison.csv - Cross-platform analysis",
                "top_comments_by_engagement.csv - High-engagement comments",
                "top_posts_by_engagement.csv - Viral content analysis"
            ]
            for doc_name in supporting_docs:
                doc.add_paragraph(doc_name, style='List Number')

            # Footer
            doc.add_paragraph()
            footer = doc.add_paragraph()
            footer.add_run(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n").italic = True
            footer.add_run("System: InsightPulse Professional Analytics").italic = True
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Save document
            doc.save(str(filepath))

            logger.info(f"✅ Executive Summary DOCX generated: {filepath.name}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error generating Executive Summary DOCX: {e}")
            return ""

    def _generate_communication_plan_docx(
        self,
        analysis_data: Dict[str, Any],
        query: str,
        analysis_type: str,
        report_folder: Path
    ) -> str:
        """Generate Communication Plan as DOCX"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            logger.warning("⚠️ python-docx not installed. Skipping DOCX generation.")
            return ""

        filepath = report_folder / "PUBLIC_COMMUNICATION_PLAN.docx"

        try:
            # Create document
            doc = Document()

            # Set document margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)

            # Extract sentiment data
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

            # Title
            title = doc.add_heading('PUBLIC COMMUNICATION PLAN', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Subtitle
            subtitle = doc.add_heading(query, 1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Metadata
            meta = doc.add_paragraph()
            meta.add_run(f"Date: ").bold = True
            meta.add_run(f"{datetime.now().strftime('%B %d, %Y')}\n")
            meta.add_run(f"Crisis Level: ").bold = True
            meta.add_run(f"{crisis_level}\n")
            meta.add_run(f"Recommended Tone: ").bold = True
            meta.add_run(f"{tone}")
            meta.alignment = WD_ALIGN_PARAGRAPH.CENTER

            doc.add_paragraph()  # Spacing

            # Communication Objectives
            doc.add_heading('🎯 COMMUNICATION OBJECTIVES', 1)
            objectives = [
                "Address Public Concerns - Acknowledge and respond to key issues",
                "Restore Confidence - Rebuild trust through transparency",
                "Provide Clarity - Clear, factual information",
                "Demonstrate Action - Show concrete steps being taken",
                "Maintain Engagement - Keep dialogue open"
            ]
            for obj in objectives:
                doc.add_paragraph(obj, style='List Number')

            # Key Messages
            doc.add_heading('📢 KEY MESSAGES', 1)

            doc.add_heading('Primary Message', 2)
            doc.add_paragraph('"We hear your concerns and are committed to [specific action]. Our priority is [key value proposition]."')

            doc.add_heading('Supporting Messages', 2)
            doc.add_paragraph("Transparency: \"We are committed to open communication...\"", style='List Number')
            doc.add_paragraph("Action: \"We have already taken steps to...\"", style='List Number')
            doc.add_paragraph("Commitment: \"Moving forward, we will...\"", style='List Number')

            # Spokesperson Guidelines
            doc.add_heading('🎤 SPOKESPERSON GUIDELINES', 1)

            doc.add_heading("Do's ✅", 2)
            dos = [
                "Acknowledge concerns empathetically",
                "Provide specific, factual information",
                "Show concrete actions being taken",
                "Maintain calm, professional tone",
                "Offer clear next steps"
            ]
            for item in dos:
                doc.add_paragraph(item, style='List Bullet')

            doc.add_heading("Don'ts ❌", 2)
            donts = [
                "Make defensive statements",
                "Provide speculative information",
                "Over-promise without delivery plan",
                "Ignore negative feedback",
                "Use corporate jargon"
            ]
            for item in donts:
                doc.add_paragraph(item, style='List Bullet')

            # Platform-Specific Strategy
            doc.add_heading('📱 PLATFORM-SPECIFIC STRATEGY', 1)

            platforms_strategy = {
                "Facebook": {
                    "Approach": "Detailed posts with context",
                    "Frequency": "2-3 times daily during crisis",
                    "Content": "Mix of updates, FAQs, testimonials"
                },
                "Twitter/X": {
                    "Approach": "Quick updates, thread for details",
                    "Frequency": "Hourly during active crisis",
                    "Content": "Brief updates, links to full statements"
                },
                "Instagram": {
                    "Approach": "Visual storytelling",
                    "Frequency": "Daily stories, 2-3 posts/week",
                    "Content": "Behind-the-scenes, human element"
                },
                "LinkedIn": {
                    "Approach": "Professional, detailed updates",
                    "Frequency": "1-2 times weekly",
                    "Content": "Official statements, thought leadership"
                }
            }

            for platform, strategy in platforms_strategy.items():
                doc.add_heading(platform, 2)
                for key, value in strategy.items():
                    para = doc.add_paragraph()
                    para.add_run(f"{key}: ").bold = True
                    para.add_run(value)

            # Response Templates
            doc.add_heading('💬 RESPONSE TEMPLATES', 1)

            doc.add_heading('For Negative Comments', 2)
            doc.add_paragraph('"Thank you for sharing your concerns. We take this feedback seriously. [Specific acknowledgment of issue]. We are [specific action being taken]. Please contact us at [contact] for further assistance."')

            doc.add_heading('For Questions', 2)
            doc.add_paragraph('"Great question! [Direct answer]. For more information, please visit [link] or contact our team at [contact]."')

            doc.add_heading('For Positive Feedback', 2)
            doc.add_paragraph('"Thank you for your support! We\'re committed to [value proposition] and appreciate customers like you."')

            # Communication Timeline
            doc.add_heading('⏰ COMMUNICATION TIMELINE', 1)

            doc.add_heading('Immediate (0-24 hours)', 2)
            doc.add_paragraph("Issue initial statement acknowledging situation", style='List Bullet')
            doc.add_paragraph("Respond to top 10 most engaged negative posts", style='List Bullet')
            doc.add_paragraph("Brief internal stakeholders", style='List Bullet')
            doc.add_paragraph("Prepare FAQ document", style='List Bullet')

            doc.add_heading('Short-term (1-7 days)', 2)
            doc.add_paragraph("Daily updates on progress", style='List Bullet')
            doc.add_paragraph("Host Q&A session (if appropriate)", style='List Bullet')
            doc.add_paragraph("Share positive testimonials", style='List Bullet')
            doc.add_paragraph("Monitor sentiment shifts", style='List Bullet')

            doc.add_heading('Medium-term (1-4 weeks)', 2)
            doc.add_paragraph("Weekly progress reports", style='List Bullet')
            doc.add_paragraph("Case studies of improvements", style='List Bullet')
            doc.add_paragraph("Engage with influencers", style='List Bullet')
            doc.add_paragraph("Measure communication impact", style='List Bullet')

            # Monitoring & Measurement
            doc.add_heading('📊 MONITORING & MEASUREMENT', 1)

            doc.add_heading('Key Metrics to Track', 2)
            metrics = [
                "Sentiment score changes",
                "Engagement rate on responses",
                "Share of voice vs competitors",
                "Response time to comments",
                "Issue resolution rate"
            ]
            for metric in metrics:
                doc.add_paragraph(metric, style='List Bullet')

            doc.add_heading('Success Indicators', 2)
            success = [
                "✅ Negative sentiment decreasing",
                "✅ Positive engagement increasing",
                "✅ Issue mentions declining",
                "✅ Brand trust scores improving"
            ]
            for indicator in success:
                doc.add_paragraph(indicator, style='List Bullet')

            # Escalation Protocol
            doc.add_heading('🚨 ESCALATION PROTOCOL', 1)

            doc.add_heading('Level 1: Standard Response', 2)
            doc.add_paragraph("Individual team member responds", style='List Bullet')
            doc.add_paragraph("Use approved templates", style='List Bullet')
            doc.add_paragraph("Log in tracking system", style='List Bullet')

            doc.add_heading('Level 2: Manager Review', 2)
            doc.add_paragraph("Sensitive or complex issues", style='List Bullet')
            doc.add_paragraph("Manager approval required", style='List Bullet')
            doc.add_paragraph("Coordinated response", style='List Bullet')

            doc.add_heading('Level 3: Executive Involvement', 2)
            doc.add_paragraph("Crisis situation", style='List Bullet')
            doc.add_paragraph("Legal/regulatory concerns", style='List Bullet')
            doc.add_paragraph("CEO/spokesperson statement", style='List Bullet')

            # Footer
            doc.add_paragraph()
            footer = doc.add_paragraph()
            footer.add_run(f"Plan Prepared: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n").italic = True
            footer.add_run("System: InsightPulse Professional Analytics").italic = True
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Save document
            doc.save(str(filepath))

            logger.info(f"✅ Communication Plan DOCX generated: {filepath.name}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Error generating Communication Plan DOCX: {e}")
            return ""

