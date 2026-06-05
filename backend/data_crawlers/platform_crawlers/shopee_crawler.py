"""Shopee crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class ShopeeCrawler(BaseCrawler):
    """Crawler for Shopee e-commerce platform."""
    
    def __init__(self):
        super().__init__("shopee")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Shopee Apify actor."""
        return {
            "search": query,
            "maxItems": kwargs.get("max_items", 100),
            "country": kwargs.get("country", "sg"),  # sg, my, th, id, ph, vn, tw
            "scrapeProductDetails": True,
            "scrapeReviews": kwargs.get("scrape_reviews", True),
            "maxReviews": kwargs.get("max_reviews", 50),
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Shopee data to database format."""
        products = []
        
        for item in raw_data:
            # Transform product
            product_data = {
                "platform": self.platform,
                "product_id": str(item.get("itemid", "")),
                "title": item.get("name", ""),
                "description": item.get("description", ""),
                "price": item.get("price", 0) / 100000 if item.get("price") else 0,  # Shopee stores price in cents
                "currency": item.get("currency", "SGD"),
                "url": item.get("url", ""),
                "seller_id": str(item.get("shopid", "")),
                "seller_name": item.get("shop_name", ""),
                "seller_rating": item.get("shop_rating", 0),
                "rating": item.get("item_rating", {}).get("rating_star", 0),
                "reviews_count": item.get("item_rating", {}).get("rating_count", [0])[0],
                "sold_count": item.get("sold", 0),
                "stock": item.get("stock", 0),
                "images": item.get("images", []),
                "categories": [item.get("catid", "")],
                "specifications": item.get("attributes", []),
                "metadata": {
                    "brand": item.get("brand", ""),
                    "condition": item.get("condition", ""),
                    "discount": item.get("discount", ""),
                    "liked_count": item.get("liked_count", 0),
                    "view_count": item.get("view_count", 0),
                }
            }
            products.append(product_data)
        
        return {
            "products": products
        }

