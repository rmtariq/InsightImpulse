"""Repository pattern for database operations."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

from .models import Post, Comment, UserProfile, Product, CrawlJob


class BaseRepository:
    """Base repository with common operations."""
    
    def __init__(self, session: Session, model):
        self.session = session
        self.model = model
    
    def create(self, **kwargs) -> Any:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance
    
    def get_by_id(self, id: int) -> Optional[Any]:
        """Get record by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Get all records with pagination."""
        return self.session.query(self.model).limit(limit).offset(offset).all()
    
    def update(self, id: int, **kwargs) -> Optional[Any]:
        """Update a record."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.session.flush()
        return instance
    
    def delete(self, id: int) -> bool:
        """Delete a record."""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            return True
        return False


class PostRepository(BaseRepository):
    """Repository for Post operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Post)
    
    def get_by_post_id(self, post_id: str) -> Optional[Post]:
        """Get post by platform-specific post ID."""
        return self.session.query(Post).filter(Post.post_id == post_id).first()
    
    def get_by_platform(self, platform: str, limit: int = 100) -> List[Post]:
        """Get posts by platform."""
        return self.session.query(Post).filter(Post.platform == platform).order_by(desc(Post.created_at)).limit(limit).all()
    
    def upsert(self, post_data: Dict[str, Any]) -> Post:
        """Insert or update a post."""
        existing = self.get_by_post_id(post_data.get("post_id"))
        if existing:
            for key, value in post_data.items():
                setattr(existing, key, value)
            return existing
        else:
            return self.create(**post_data)


class CommentRepository(BaseRepository):
    """Repository for Comment operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Comment)
    
    def get_by_comment_id(self, comment_id: str) -> Optional[Comment]:
        """Get comment by platform-specific comment ID."""
        return self.session.query(Comment).filter(Comment.comment_id == comment_id).first()
    
    def get_by_post(self, post_id: int, limit: int = 100) -> List[Comment]:
        """Get comments for a specific post."""
        return self.session.query(Comment).filter(Comment.post_id == post_id).limit(limit).all()


class UserProfileRepository(BaseRepository):
    """Repository for UserProfile operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, UserProfile)
    
    def get_by_platform_user(self, platform: str, user_id: str) -> Optional[UserProfile]:
        """Get user profile by platform and user ID."""
        return self.session.query(UserProfile).filter(
            UserProfile.platform == platform,
            UserProfile.user_id == user_id
        ).first()
    
    def upsert(self, profile_data: Dict[str, Any]) -> UserProfile:
        """Insert or update a user profile."""
        existing = self.get_by_platform_user(profile_data.get("platform"), profile_data.get("user_id"))
        if existing:
            for key, value in profile_data.items():
                setattr(existing, key, value)
            return existing
        else:
            return self.create(**profile_data)


class ProductRepository(BaseRepository):
    """Repository for Product operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Product)
    
    def get_by_platform_product(self, platform: str, product_id: str) -> Optional[Product]:
        """Get product by platform and product ID."""
        return self.session.query(Product).filter(
            Product.platform == platform,
            Product.product_id == product_id
        ).first()
    
    def upsert(self, product_data: Dict[str, Any]) -> Product:
        """Insert or update a product."""
        existing = self.get_by_platform_product(product_data.get("platform"), product_data.get("product_id"))
        if existing:
            for key, value in product_data.items():
                setattr(existing, key, value)
            return existing
        else:
            return self.create(**product_data)


class CrawlJobRepository(BaseRepository):
    """Repository for CrawlJob operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, CrawlJob)
    
    def create_job(self, platform: str, job_type: str, query: str, extra_data: Dict = None) -> CrawlJob:
        """Create a new crawl job."""
        return self.create(
            platform=platform,
            job_type=job_type,
            query=query,
            status="pending",
            extra_data=extra_data or {}
        )
    
    def update_status(self, job_id: int, status: str, items_collected: int = None, error_message: str = None):
        """Update job status."""
        update_data = {"status": status}
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        if items_collected is not None:
            update_data["items_collected"] = items_collected
        if error_message:
            update_data["error_message"] = error_message
        return self.update(job_id, **update_data)

