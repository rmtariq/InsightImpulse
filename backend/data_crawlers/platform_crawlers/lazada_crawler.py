"""Lazada crawler implementation."""
from typing import Dict, Any, List
from datetime import datetime
from .base_crawler import BaseCrawler


class LazadaCrawler(BaseCrawler):
    """Crawler for Lazada e-commerce platform."""
    
    def __init__(self):
        super().__init__("lazada")
    
    def prepare_input(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare input for Lazada Apify actor."""
        return {
            "search": query,
            "maxItems": kwargs.get("max_items", 100),
            "country": kwargs.get("country", "sg"),  # sg, my, th, id, ph, vn
            "scrapeProductDetails": True,
            "scrapeReviews": kwargs.get("scrape_reviews", True),
            "maxReviews": kwargs.get("max_reviews", 50),
        }
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Lazada data to database format."""
        products = []
        
        for item in raw_data:
            # Transform product
            product_data = {
                "platform": self.platform,
                "product_id": str(item.get("itemId", "")),
                "title": item.get("name", ""),
                "description": item.get("description", ""),
                "price": item.get("price", 0),
                "currency": item.get("currency", "SGD"),
                "url": item.get("productUrl", ""),
                "seller_id": str(item.get("sellerId", "")),
                "seller_name": item.get("sellerName", ""),
                "seller_rating": item.get("sellerRating", 0),
                "rating": item.get("ratingScore", 0),
                "reviews_count": item.get("review", 0),
                "sold_count": item.get("itemSoldCnt", 0),
                "stock": item.get("quantity", 0),
                "images": item.get("images", []),
                "categories": item.get("categories", []),
                "specifications": item.get("specifications", {}),
                "metadata": {
                    "brand": item.get("brand", ""),
                    "discount": item.get("discount", ""),
                    "original_price": item.get("originalPrice", 0),
                    "location": item.get("location", ""),
                }
            }
            products.append(product_data)
        
        return {
            "products": products
        }

