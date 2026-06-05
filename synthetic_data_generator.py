"""
🚀 INSIGHTPULSE SYNTHETIC DATA GENERATOR
=======================================

Professional synthetic data generator that simulates real-time crawling
across all 9 platforms for complete InsightPulse development and testing.

Platforms Supported:
- Social Media (7): Facebook, Instagram, X/Twitter, TikTok, Google, News, Lowyat
- E-commerce (2): Shopee, Lazada

Features:
- Intelligent keyword extraction and expansion
- Malaysian context-aware content generation
- Realistic sentiment distribution
- Platform-specific content styles
- Time-based data generation
- Query-relevant content matching

Author: InsightPulse Team
"""

import pandas as pd
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlatformConfig:
    """Configuration for each platform's data generation"""
    name: str
    content_style: str
    avg_engagement: int
    sentiment_bias: float  # -1 to 1, where 1 is very positive
    language_mix: Dict[str, float]  # {"english": 0.7, "malay": 0.3}
    content_length: Dict[str, int]  # {"min": 50, "max": 280}

class SyntheticDataGenerator:
    """
    Advanced synthetic data generator for InsightPulse development
    """
    
    def __init__(self):
        self.data_dir = Path("data/smart_crawlers")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Platform configurations
        self.platforms = {
            "facebook": PlatformConfig(
                name="Facebook",
                content_style="conversational",
                avg_engagement=150,
                sentiment_bias=0.1,
                language_mix={"english": 0.6, "malay": 0.4},
                content_length={"min": 100, "max": 500}
            ),
            "instagram": PlatformConfig(
                name="Instagram",
                content_style="visual_focused",
                avg_engagement=200,
                sentiment_bias=0.3,
                language_mix={"english": 0.7, "malay": 0.3},
                content_length={"min": 50, "max": 200}
            ),
            "x": PlatformConfig(
                name="X/Twitter",
                content_style="news_opinion",
                avg_engagement=80,
                sentiment_bias=0.0,
                language_mix={"english": 0.8, "malay": 0.2},
                content_length={"min": 50, "max": 280}
            ),
            "tiktok": PlatformConfig(
                name="TikTok",
                content_style="viral_trendy",
                avg_engagement=500,
                sentiment_bias=0.4,
                language_mix={"english": 0.5, "malay": 0.5},
                content_length={"min": 30, "max": 150}
            ),
            "google": PlatformConfig(
                name="Google",
                content_style="informational",
                avg_engagement=50,
                sentiment_bias=0.1,
                language_mix={"english": 0.9, "malay": 0.1},
                content_length={"min": 200, "max": 800}
            ),
            "news": PlatformConfig(
                name="News",
                content_style="formal_news",
                avg_engagement=100,
                sentiment_bias=0.0,
                language_mix={"english": 0.8, "malay": 0.2},
                content_length={"min": 300, "max": 1000}
            ),
            "lowyat": PlatformConfig(
                name="Lowyat",
                content_style="tech_forum",
                avg_engagement=75,
                sentiment_bias=0.2,
                language_mix={"english": 0.9, "malay": 0.1},
                content_length={"min": 100, "max": 400}
            ),
            "shopee": PlatformConfig(
                name="Shopee",
                content_style="product_review",
                avg_engagement=120,
                sentiment_bias=0.2,
                language_mix={"english": 0.4, "malay": 0.6},
                content_length={"min": 80, "max": 300}
            ),
            "lazada": PlatformConfig(
                name="Lazada",
                content_style="product_review",
                avg_engagement=100,
                sentiment_bias=0.1,
                language_mix={"english": 0.5, "malay": 0.5},
                content_length={"min": 80, "max": 300}
            )
        }
        
        # Malaysian context templates
        self.malaysian_contexts = {
            "food": {
                "locations": ["Kuala Lumpur", "Selangor", "Penang", "Johor Bahru", "Ipoh", "Melaka", "Kota Kinabalu"],
                "terms": ["halal", "sedap", "murah", "best", "viral", "trending", "recommended"],
                "foods": ["nasi lemak", "roti canai", "laksa", "char kway teow", "satay", "rendang", "cendol"]
            },
            "fashion": {
                "items": ["tudung", "hijab", "baju kurung", "kebaya", "songket", "batik", "seluar", "kasut"],
                "brands": ["Naelofar", "Duckscarves", "Ariani", "Vanilla Hijab", "Bokitta", "Muslimah Active"],
                "qualities": ["premium", "affordable", "trendy", "comfortable", "stylish", "viral", "popular"]
            },
            "technology": {
                "products": ["smartphone", "laptop", "tablet", "smartwatch", "earbuds", "camera", "gaming"],
                "brands": ["Samsung Galaxy A54", "iPhone 15", "Xiaomi Redmi Note 13", "OPPO A78", "Vivo Y36", "Realme 11", "OnePlus Nord CE3", "Honor 90 Lite"],
                "features": ["budget king", "flagship killer", "camera beast", "battery champion", "gaming phone", "value for money", "best buy"],
                "specs": ["6GB RAM", "8GB RAM", "128GB storage", "256GB storage", "5000mAh battery", "108MP camera", "120Hz display", "67W fast charging"],
                "prices": ["RM899", "RM1299", "RM1599", "RM1899", "under RM1000", "RM1000-1500", "RM1500-2000"],
                "retailers": ["Shopee Malaysia", "Lazada Malaysia", "DirectD", "SenHeng", "Harvey Norman", "Courts Malaysia"],
                "local_terms": ["Malaysian warranty", "local distributor", "service center", "dual SIM", "halal certified accessories"]
            }
        }

    def extract_keywords_from_query(self, query: str) -> Dict[str, Any]:
        """
        Extract and expand keywords from user query with Malaysian context
        """
        query_lower = query.lower()
        
        # Detect domain
        domain = "general"
        if any(food in query_lower for food in self.malaysian_contexts["food"]["foods"]):
            domain = "food"
        elif any(item in query_lower for item in self.malaysian_contexts["fashion"]["items"]):
            domain = "fashion"
        elif any(tech in query_lower for tech in self.malaysian_contexts["technology"]["products"]):
            domain = "technology"
        
        # Extract base keywords
        keywords = query_lower.split()
        
        # Expand with domain-specific terms
        if domain in self.malaysian_contexts:
            context = self.malaysian_contexts[domain]
            for category, terms in context.items():
                for term in terms:
                    if term.lower() in query_lower:
                        keywords.extend([term, f"{term} Malaysia", f"best {term}"])
        
        # Add Malaysian context
        malaysian_terms = ["Malaysia", "KL", "Selangor", "viral", "trending", "popular", "best"]
        keywords.extend(malaysian_terms)
        
        return {
            "domain": domain,
            "keywords": list(set(keywords)),
            "expanded_keywords": keywords,
            "malaysian_context": True
        }

    def generate_realistic_content(self, platform: str, query: str, keyword_data: Dict[str, Any]) -> str:
        """
        Generate realistic content based on platform style and query context
        """
        config = self.platforms[platform]
        domain = keyword_data["domain"]
        
        # Base content templates by domain and platform
        templates = self._get_content_templates(platform, domain)
        
        # Select random template
        template = random.choice(templates)
        
        # Fill template with relevant data
        content = self._fill_template(template, query, keyword_data, config)
        
        return content

    def _get_content_templates(self, platform: str, domain: str) -> List[str]:
        """Get content templates for specific platform and domain"""
        # This would be expanded with hundreds of templates
        # For now, showing key examples
        
        if domain == "food" and platform == "facebook":
            return [
                "Baru try {food} kat {location}! Memang {quality} sangat. Highly recommended untuk yang cari {food} {quality} di {location}. Rating: {rating}/5 ⭐",
                "{location} ada {food} yang viral sekarang! Pergi {restaurant} tadi, memang {quality}. Harga pun reasonable. Worth it!",
                "Korang dah try {food} kat {location} belum? Memang {quality} gila! Viral sebab memang sedap. Queue panjang tapi berbaloi!"
            ]
        elif domain == "fashion" and platform == "shopee":
            return [
                "{item} {brand} ni memang {quality}! Kualiti {material} dan {design}. Harga {price_comment}. Highly recommended!",
                "Baru beli {item} dari {brand}. {quality} sangat! {material} comfortable dan {design}. Worth the price!",
                "{item} viral ni memang {quality}! {brand} punya quality consistent. {design} dan {material} top notch."
            ]
        elif domain == "technology" and platform == "lowyat":
            return [
                "{product} {brand} review: {feature} performance excellent. {price_comment} for the specs. Recommended for {use_case}.",
                "Just got the {product} {brand}. {feature} is impressive. {performance} smooth. Good value for money.",
                "{brand} {product} - {feature} standout feature. {performance} reliable. {price_comment} considering the competition."
            ]
        
        # Default templates
        return [
            "Great experience with {query}! Highly recommended in Malaysia.",
            "{query} in Malaysia is really good. Worth trying!",
            "Just tried {query} - amazing quality and value!"
        ]

    def _fill_template(self, template: str, query: str, keyword_data: Dict[str, Any], config: PlatformConfig) -> str:
        """Fill template with realistic data"""
        domain = keyword_data["domain"]
        
        # Replacement data
        replacements = {
            "query": query,
            "rating": random.choice(["4.2", "4.5", "4.7", "4.8", "4.9"]),
            "quality": random.choice(["sedap", "best", "excellent", "amazing", "fantastic", "viral"]),
            "price_comment": random.choice(["affordable", "reasonable price", "worth it", "good value", "budget-friendly"])
        }
        
        # Domain-specific replacements
        if domain == "food":
            food_context = self.malaysian_contexts["food"]
            replacements.update({
                "food": random.choice(food_context["foods"]),
                "location": random.choice(food_context["locations"]),
                "restaurant": f"Restoran {random.choice(['Seri Melayu', 'Pak Su', 'Village Park', 'Pelita', 'Mamak Penang'])}"
            })
        elif domain == "fashion":
            fashion_context = self.malaysian_contexts["fashion"]
            replacements.update({
                "item": random.choice(fashion_context["items"]),
                "brand": random.choice(fashion_context["brands"]),
                "material": random.choice(["cotton", "chiffon", "silk", "jersey", "premium fabric"]),
                "design": random.choice(["trendy", "elegant", "modern", "classic", "stylish"])
            })
        elif domain == "technology":
            tech_context = self.malaysian_contexts["technology"]
            replacements.update({
                "product": random.choice(tech_context["products"]),
                "brand": random.choice(tech_context["brands"]),
                "feature": random.choice(tech_context["features"]),
                "performance": random.choice(["smooth", "fast", "reliable", "excellent", "outstanding"]),
                "use_case": random.choice(["gaming", "photography", "business", "daily use", "content creation"])
            })
        
        # Apply replacements
        content = template
        for key, value in replacements.items():
            content = content.replace(f"{{{key}}}", str(value))
        
        return content

    def generate_platform_data(self, platform: str, query: str, num_posts: int = 50) -> pd.DataFrame:
        """
        Generate synthetic data for a specific platform based on query
        """
        logger.info(f"🎯 Generating {num_posts} posts for {platform} with query: '{query}'")

        # Extract keywords and context
        keyword_data = self.extract_keywords_from_query(query)
        config = self.platforms[platform]

        # Generate posts
        posts = []
        base_date = datetime.now() - timedelta(days=30)

        for i in range(num_posts):
            # Generate realistic content
            content = self.generate_realistic_content(platform, query, keyword_data)

            # Generate engagement metrics
            base_engagement = config.avg_engagement
            engagement_variance = random.uniform(0.5, 2.0)
            likes = int(base_engagement * engagement_variance * random.uniform(0.8, 1.5))
            shares = int(likes * random.uniform(0.1, 0.3))
            comments = int(likes * random.uniform(0.05, 0.2))
            views = int(likes * random.uniform(5, 15))

            # Generate sentiment
            sentiment_base = config.sentiment_bias
            sentiment_score = max(0.1, min(0.9, sentiment_base + random.uniform(-0.3, 0.3)))
            sentiment_label = "Positive" if sentiment_score > 0.6 else "Negative" if sentiment_score < 0.4 else "Neutral"

            # Generate date
            post_date = base_date + timedelta(days=random.randint(0, 30),
                                            hours=random.randint(0, 23),
                                            minutes=random.randint(0, 59))

            post = {
                "Platform": platform.title(),
                "Type": self._get_post_type(platform),
                "ID": f"{platform.upper()}{i+1:03d}",
                "Text": content,
                "Sentiment": sentiment_label,
                "Date": post_date.strftime("%Y-%m-%d"),
                "likes": likes,
                "shares": shares,
                "comments_count": comments,
                "views": views,
                "sentiment_score": round(sentiment_score, 2),
                "total_engagement": likes + shares + comments
            }

            posts.append(post)

        df = pd.DataFrame(posts)
        logger.info(f"✅ Generated {len(df)} posts for {platform}")
        return df

    def _get_post_type(self, platform: str) -> str:
        """Get appropriate post type for platform"""
        post_types = {
            "facebook": ["Post", "Share", "Photo", "Video", "Link"],
            "instagram": ["Photo", "Video", "Story", "Reel", "IGTV"],
            "x": ["Tweet", "Retweet", "Reply", "Quote Tweet"],
            "tiktok": ["Video", "Live", "Duet", "Stitch"],
            "google": ["Search Result", "News Article", "Blog Post"],
            "news": ["News Article", "Press Release", "Editorial"],
            "lowyat": ["Forum Post", "Reply", "Review", "Discussion"],
            "shopee": ["Product Review", "Q&A", "Product Description"],
            "lazada": ["Product Review", "Q&A", "Product Description"]
        }
        return random.choice(post_types.get(platform, ["Post"]))

    def generate_complete_dataset(self, query: str, platforms: List[str], posts_per_platform: int = 50) -> Dict[str, pd.DataFrame]:
        """
        Generate complete synthetic dataset for all requested platforms
        """
        logger.info(f"🚀 Starting complete dataset generation for query: '{query}'")
        logger.info(f"📱 Platforms: {platforms}")
        logger.info(f"📊 Posts per platform: {posts_per_platform}")

        datasets = {}

        for platform in platforms:
            if platform not in self.platforms:
                logger.warning(f"⚠️ Unknown platform: {platform}")
                continue

            try:
                # Generate data for platform
                df = self.generate_platform_data(platform, query, posts_per_platform)
                datasets[platform] = df

                # Save to CSV
                self.save_platform_data(platform, query, df)

            except Exception as e:
                logger.error(f"❌ Error generating data for {platform}: {e}")
                continue

        logger.info(f"✅ Complete dataset generation finished. Generated data for {len(datasets)} platforms.")
        return datasets

    def save_platform_data(self, platform: str, query: str, df: pd.DataFrame):
        """
        Save platform data to CSV file with proper naming convention
        """
        # Create platform directory
        platform_dir = self.data_dir / platform
        platform_dir.mkdir(exist_ok=True)

        # Generate filename
        query_clean = re.sub(r'[^\w\s-]', '', query).strip()
        query_clean = re.sub(r'[-\s]+', '_', query_clean)
        timestamp = datetime.now().strftime("%Y%m%d")

        filename = f"{platform}_{query_clean}_{timestamp}.csv"
        filepath = platform_dir / filename

        # Save CSV
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved {len(df)} records to {filepath}")

    def simulate_real_time_crawling(self, query: str, platforms: List[str], posts_per_platform: int = 50) -> Dict[str, Any]:
        """
        Simulate real-time crawling process with progress updates
        """
        logger.info(f"🔄 Simulating real-time crawling for: '{query}'")

        # Extract keywords for better simulation
        keyword_data = self.extract_keywords_from_query(query)

        results = {
            "query": query,
            "keyword_analysis": keyword_data,
            "platforms_requested": platforms,
            "posts_per_platform": posts_per_platform,
            "crawl_status": "in_progress",
            "platform_results": {},
            "total_posts_generated": 0,
            "crawl_start_time": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(seconds=len(platforms) * 2)).isoformat()
        }

        # Simulate crawling each platform
        for i, platform in enumerate(platforms):
            logger.info(f"🕷️ Crawling {platform}... ({i+1}/{len(platforms)})")

            try:
                # Generate data
                df = self.generate_platform_data(platform, query, posts_per_platform)

                # Save data
                self.save_platform_data(platform, query, df)

                # Update results
                results["platform_results"][platform] = {
                    "status": "completed",
                    "posts_found": len(df),
                    "avg_sentiment": df["sentiment_score"].mean(),
                    "total_engagement": df["total_engagement"].sum(),
                    "completion_time": datetime.now().isoformat()
                }

                results["total_posts_generated"] += len(df)

            except Exception as e:
                logger.error(f"❌ Error crawling {platform}: {e}")
                results["platform_results"][platform] = {
                    "status": "error",
                    "error": str(e),
                    "posts_found": 0
                }

        results["crawl_status"] = "completed"
        results["crawl_end_time"] = datetime.now().isoformat()

        logger.info(f"✅ Crawling simulation completed. Total posts: {results['total_posts_generated']}")
        return results


# Convenience functions for easy integration
def quick_generate_data(query: str, platforms: List[str] = None, posts_per_platform: int = 50) -> Dict[str, Any]:
    """
    Quick function to generate synthetic data for testing
    """
    if platforms is None:
        platforms = ["facebook", "instagram", "shopee"]

    generator = SyntheticDataGenerator()
    return generator.simulate_real_time_crawling(query, platforms, posts_per_platform)


def generate_for_query(query: str, posts_per_platform: int = 50) -> Dict[str, Any]:
    """
    Generate data for all 9 platforms based on query
    """
    all_platforms = ["facebook", "instagram", "x", "tiktok", "google", "news", "lowyat", "shopee", "lazada"]
    return quick_generate_data(query, all_platforms, posts_per_platform)


def generate_fashion_data(query: str = "tudung paling viral 2025", posts_per_platform: int = 30) -> Dict[str, Any]:
    """
    Generate fashion-specific data across relevant platforms
    """
    fashion_platforms = ["facebook", "instagram", "tiktok", "shopee", "lazada"]
    return quick_generate_data(query, fashion_platforms, posts_per_platform)


def generate_food_data(query: str = "makanan halal sedap di Kuala Lumpur", posts_per_platform: int = 30) -> Dict[str, Any]:
    """
    Generate food-specific data across relevant platforms
    """
    food_platforms = ["facebook", "instagram", "google", "news", "shopee"]
    return quick_generate_data(query, food_platforms, posts_per_platform)


def generate_tech_data(query: str = "best budget smartphone Malaysia 2025", posts_per_platform: int = 30) -> Dict[str, Any]:
    """
    Generate technology-specific data across relevant platforms
    """
    tech_platforms = ["facebook", "x", "lowyat", "shopee", "lazada"]
    return quick_generate_data(query, tech_platforms, posts_per_platform)


if __name__ == "__main__":
    # Example usage
    print("🚀 InsightPulse Synthetic Data Generator")
    print("=" * 50)

    # Test with different queries
    test_queries = [
        "tudung paling viral 2025",
        "makanan halal sedap di Kuala Lumpur",
        "best budget smartphone Malaysia 2025"
    ]

    for query in test_queries:
        print(f"\n🎯 Testing query: '{query}'")
        result = quick_generate_data(query, ["facebook", "instagram", "shopee"], 20)
        print(f"✅ Generated {result['total_posts_generated']} posts across {len(result['platform_results'])} platforms")

        # Show sample results
        for platform, platform_result in result['platform_results'].items():
            if platform_result['status'] == 'completed':
                print(f"   📱 {platform}: {platform_result['posts_found']} posts, avg sentiment: {platform_result['avg_sentiment']:.2f}")

    print(f"\n🎉 Synthetic data generation complete!")
    print(f"📂 Data saved to: data/smart_crawlers/")
    print(f"🔍 You can now test InsightPulse with realistic data!")
