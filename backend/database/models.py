"""Database models for social media crawler."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, BigInteger, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Post(Base):
    """Model for social media posts."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Project isolation - NEW FIELD for robust multi-project support
    project_name = Column(String(100), nullable=True, index=True, default='general')

    platform = Column(String(50), nullable=False, index=True)
    post_id = Column(String(255), nullable=False, unique=True, index=True)
    author_id = Column(String(255), index=True)
    author_username = Column(String(255))
    author_name = Column(String(255))
    content = Column(Text)
    url = Column(String(500))
    created_at = Column(DateTime, index=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Engagement metrics
    likes_count = Column(BigInteger, default=0)
    comments_count = Column(BigInteger, default=0)
    shares_count = Column(BigInteger, default=0)
    views_count = Column(BigInteger, default=0)

    # Sentiment & Emotion Analysis
    sentiment = Column(String(20))  # negative, neutral, positive
    sentiment_score = Column(Float)  # confidence score
    emotion = Column(String(20))  # anger, fear, happy, love, sadness, surprise
    emotion_score = Column(Float)  # confidence score

    # Additional data
    hashtags = Column(JSON)
    mentions = Column(JSON)
    media_urls = Column(JSON)
    extra_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    __table_args__ = (
        Index('idx_platform_created', 'platform', 'created_at'),
        Index('idx_project_platform', 'project_name', 'platform'),
    )


class Comment(Base):
    """Model for comments on posts."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Project isolation - NEW FIELD for robust multi-project support
    project_name = Column(String(100), nullable=True, index=True, default='general')

    platform = Column(String(50), nullable=False, index=True)
    comment_id = Column(String(255), nullable=False, unique=True, index=True)
    post_id = Column(String(255), nullable=False, index=True)  # Changed from Integer to String
    author_id = Column(String(255))
    author_username = Column(String(255))
    author_name = Column(String(255))
    content = Column(Text)
    created_at = Column(DateTime, index=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)

    # Engagement metrics
    likes_count = Column(BigInteger, default=0)
    replies_count = Column(BigInteger, default=0)

    # Sentiment & Emotion Analysis
    sentiment = Column(String(20))  # negative, neutral, positive
    sentiment_score = Column(Float)  # confidence score
    emotion = Column(String(20))  # anger, fear, happy, love, sadness, surprise
    emotion_score = Column(Float)  # confidence score

    # Additional data
    extra_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    # Relationships removed - post_id is now String, not ForeignKey

    __table_args__ = (
        Index('idx_project_platform_comment', 'project_name', 'platform'),
    )


class UserProfile(Base):
    """Model for user profiles."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    username = Column(String(255), index=True)
    display_name = Column(String(255))
    bio = Column(Text)
    profile_url = Column(String(500))
    avatar_url = Column(String(500))
    verified = Column(Integer, default=0)
    
    # Stats
    followers_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, default=0)
    posts_count = Column(BigInteger, default=0)
    
    # Timestamps
    account_created_at = Column(DateTime)
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional data
    extra_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    
    __table_args__ = (
        Index('idx_platform_user', 'platform', 'user_id', unique=True),
    )


class Product(Base):
    """Model for e-commerce products (Shopee, Lazada)."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    product_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text)
    price = Column(Float)
    currency = Column(String(10))
    url = Column(String(500))
    
    # Seller info
    seller_id = Column(String(255))
    seller_name = Column(String(255))
    seller_rating = Column(Float)
    
    # Product metrics
    rating = Column(Float)
    reviews_count = Column(Integer, default=0)
    sold_count = Column(Integer, default=0)
    stock = Column(Integer)
    
    # Additional data
    images = Column(JSON)
    categories = Column(JSON)
    specifications = Column(JSON)
    extra_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    
    # Timestamps
    crawled_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_platform_product', 'platform', 'product_id', unique=True),
    )


class CrawlJob(Base):
    """Model for tracking crawl jobs."""
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    job_type = Column(String(50))  # search, profile, hashtag, etc.
    query = Column(String(500))
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    items_collected = Column(Integer, default=0)
    error_message = Column(Text)
    extra_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

