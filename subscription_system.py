#!/usr/bin/env python3
"""
🚀 InsightPulse Subscription Management System
=============================================
Complete subscription and billing system for InsightPulse SaaS platform
Handles tiers, usage tracking, billing, and storage management

🎯 FEATURES:
- 4-tier subscription model (FREE, STARTER, PRO, ENTERPRISE)
- Usage tracking and limits enforcement
- Automated billing with Stripe integration
- Intelligent storage management (Hot/Warm/Cold)
- Data lifecycle automation

Author: InsightPulse Subscription Team
Version: SaaS Edition 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from decimal import Decimal

# Database and external service imports
import stripe
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== SUBSCRIPTION CONFIGURATION =====
class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class StorageTier(str, Enum):
    HOT = "hot"      # 0-30 days, fast access
    WARM = "warm"    # 30-90 days, medium access
    COLD = "cold"    # 90+ days, slow access

# Subscription tier configurations
SUBSCRIPTION_TIERS = {
    SubscriptionTier.FREE: {
        "name": "FREE - Discover InsightPulse",
        "price_myr": 0,
        "price_usd": 0,
        "storage_gb": 1,
        "analyses_per_month": 100,
        "platforms": ["facebook", "instagram", "shopee"],
        "data_retention_days": 7,
        "api_calls_per_month": 0,
        "support_level": "email",
        "features": [
            "Basic sentiment analysis",
            "3 platforms access",
            "7-day data retention",
            "Email support"
        ],
        "limitations": [
            "No API access",
            "No custom reports",
            "No data export",
            "Limited platforms"
        ]
    },
    SubscriptionTier.STARTER: {
        "name": "STARTER - Professional Insights",
        "price_myr": 99,
        "price_usd": 22,
        "storage_gb": 10,
        "analyses_per_month": 1000,
        "platforms": ["facebook", "instagram", "twitter", "tiktok", "google", "news", "lowyat", "shopee", "lazada"],
        "data_retention_days": 180,  # 6 months
        "api_calls_per_month": 1000,
        "support_level": "email_chat",
        "features": [
            "All 9 platforms",
            "Advanced AI analysis",
            "6-month data retention",
            "Basic API access",
            "Email + chat support",
            "Basic reports and exports"
        ],
        "limitations": [
            "No white-label options",
            "No custom integrations",
            "Limited API calls"
        ]
    },
    SubscriptionTier.PRO: {
        "name": "PRO - Enterprise Intelligence",
        "price_myr": 299,
        "price_usd": 67,
        "storage_gb": 50,
        "analyses_per_month": 5000,
        "platforms": ["facebook", "instagram", "twitter", "tiktok", "google", "news", "lowyat", "shopee", "lazada"],
        "data_retention_days": 730,  # 2 years
        "api_calls_per_month": 10000,
        "support_level": "priority",
        "features": [
            "All 9 platforms + priority processing",
            "Advanced AI + custom model training",
            "2-year data retention",
            "Full API access",
            "Priority support (phone + email)",
            "Professional reports + automated insights",
            "Custom dashboards",
            "Team collaboration (5 users)",
            "Data export in multiple formats"
        ],
        "limitations": [
            "Limited team size",
            "No white-label options"
        ]
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "ENTERPRISE - Custom Solutions",
        "price_myr": 999,
        "price_usd": 224,
        "storage_gb": 200,
        "analyses_per_month": -1,  # Unlimited
        "platforms": ["facebook", "instagram", "twitter", "tiktok", "google", "news", "lowyat", "shopee", "lazada"],
        "data_retention_days": -1,  # Unlimited
        "api_calls_per_month": -1,  # Unlimited
        "support_level": "dedicated",
        "features": [
            "All platforms + custom platform integration",
            "Custom AI model development",
            "Unlimited data retention",
            "Unlimited API access",
            "Dedicated support manager",
            "White-label solutions",
            "Custom integrations and webhooks",
            "Advanced security and compliance",
            "Unlimited team members",
            "On-premise deployment options",
            "Custom SLA agreements"
        ],
        "limitations": []
    }
}

# Storage tier configurations
STORAGE_TIERS = {
    StorageTier.HOT: {
        "name": "Hot Storage",
        "description": "Recent data (0-30 days), fast SSD storage, instant access",
        "retention_days": 30,
        "cost_per_gb_myr": 2.0,
        "access_time_ms": 100
    },
    StorageTier.WARM: {
        "name": "Warm Storage", 
        "description": "Archive data (30-90 days), standard storage, quick retrieval",
        "retention_days": 90,
        "cost_per_gb_myr": 1.0,
        "access_time_ms": 1000
    },
    StorageTier.COLD: {
        "name": "Cold Storage",
        "description": "Historical data (90+ days), cheap cloud storage, backup & compliance",
        "retention_days": -1,  # Unlimited
        "cost_per_gb_myr": 0.2,
        "access_time_ms": 300000  # 5 minutes
    }
}

# ===== PYDANTIC MODELS =====
class SubscriptionInfo(BaseModel):
    user_id: str
    tier: SubscriptionTier
    status: str  # active, cancelled, past_due, etc.
    current_period_start: datetime
    current_period_end: datetime
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UsageStats(BaseModel):
    user_id: str
    subscription_tier: SubscriptionTier
    current_period_start: datetime
    current_period_end: datetime
    analyses_used: int
    analyses_limit: int
    storage_used_gb: float
    storage_limit_gb: float
    api_calls_used: int
    api_calls_limit: int
    platforms_used: List[str]
    last_updated: datetime

class BillingInfo(BaseModel):
    user_id: str
    amount_myr: Decimal
    amount_usd: Decimal
    currency: str
    billing_period_start: datetime
    billing_period_end: datetime
    status: str  # pending, paid, failed, refunded
    stripe_invoice_id: Optional[str] = None
    created_at: datetime

class StorageUsage(BaseModel):
    user_id: str
    hot_storage_gb: float
    warm_storage_gb: float
    cold_storage_gb: float
    total_storage_gb: float
    last_cleanup: datetime

# ===== SUBSCRIPTION MANAGER =====
class SubscriptionManager:
    """Manages user subscriptions, usage tracking, and billing"""
    
    def __init__(self, db_pool, mongodb_client, redis_client):
        self.db_pool = db_pool
        self.mongodb = mongodb_client
        self.redis = redis_client
        
        # Initialize Stripe
        stripe.api_key = "sk_test_..."  # Use environment variable in production
        
    async def create_subscription(self, user_id: str, tier: SubscriptionTier, payment_method_id: str = None) -> SubscriptionInfo:
        """Create a new subscription for a user"""
        
        tier_config = SUBSCRIPTION_TIERS[tier]
        
        # For FREE tier, no payment required
        if tier == SubscriptionTier.FREE:
            subscription = SubscriptionInfo(
                user_id=user_id,
                tier=tier,
                status="active",
                current_period_start=datetime.now(),
                current_period_end=datetime.now() + timedelta(days=30),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        else:
            # Create Stripe subscription for paid tiers
            stripe_subscription = await self.create_stripe_subscription(
                user_id, tier, payment_method_id
            )
            
            subscription = SubscriptionInfo(
                user_id=user_id,
                tier=tier,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                stripe_subscription_id=stripe_subscription.id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        # Store in database
        await self.store_subscription(subscription)
        
        # Initialize usage tracking
        await self.initialize_usage_tracking(user_id, tier)
        
        # Set up storage allocation
        await self.allocate_storage(user_id, tier)
        
        logger.info(f"Created {tier} subscription for user {user_id}")
        return subscription
    
    async def get_subscription(self, user_id: str) -> Optional[SubscriptionInfo]:
        """Get current subscription for a user"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM subscriptions WHERE user_id = $1 AND status = 'active'",
                user_id
            )
            if row:
                return SubscriptionInfo(**dict(row))
        return None
    
    async def get_usage_stats(self, user_id: str) -> Optional[UsageStats]:
        """Get current usage statistics for a user"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM usage_stats WHERE user_id = $1",
                user_id
            )
            if row:
                return UsageStats(**dict(row))
        return None
    
    async def check_usage_limits(self, user_id: str, operation: str) -> bool:
        """Check if user can perform an operation based on their limits"""
        
        subscription = await self.get_subscription(user_id)
        if not subscription:
            return False
        
        usage = await self.get_usage_stats(user_id)
        if not usage:
            return False
        
        tier_config = SUBSCRIPTION_TIERS[subscription.tier]
        
        # Check different types of limits
        if operation == "analysis":
            if tier_config["analyses_per_month"] == -1:  # Unlimited
                return True
            return usage.analyses_used < tier_config["analyses_per_month"]
        
        elif operation == "api_call":
            if tier_config["api_calls_per_month"] == -1:  # Unlimited
                return True
            return usage.api_calls_used < tier_config["api_calls_per_month"]
        
        elif operation == "storage":
            if tier_config["storage_gb"] == -1:  # Unlimited
                return True
            return usage.storage_used_gb < tier_config["storage_gb"]
        
        return False
    
    async def increment_usage(self, user_id: str, operation: str, amount: int = 1):
        """Increment usage counter for a user"""
        
        async with self.db_pool.acquire() as conn:
            if operation == "analysis":
                await conn.execute(
                    "UPDATE usage_stats SET analyses_used = analyses_used + $1, last_updated = $2 WHERE user_id = $3",
                    amount, datetime.now(), user_id
                )
            elif operation == "api_call":
                await conn.execute(
                    "UPDATE usage_stats SET api_calls_used = api_calls_used + $1, last_updated = $2 WHERE user_id = $3",
                    amount, datetime.now(), user_id
                )
        
        # Cache in Redis for fast access
        await self.redis.hincrby(f"usage:{user_id}", operation, amount)
    
    async def upgrade_subscription(self, user_id: str, new_tier: SubscriptionTier) -> SubscriptionInfo:
        """Upgrade user's subscription to a higher tier"""
        
        current_subscription = await self.get_subscription(user_id)
        if not current_subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Cancel current Stripe subscription if exists
        if current_subscription.stripe_subscription_id:
            stripe.Subscription.delete(current_subscription.stripe_subscription_id)
        
        # Create new subscription
        new_subscription = await self.create_subscription(user_id, new_tier)
        
        # Update storage allocation
        await self.allocate_storage(user_id, new_tier)
        
        logger.info(f"Upgraded user {user_id} from {current_subscription.tier} to {new_tier}")
        return new_subscription
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user's subscription"""
        
        subscription = await self.get_subscription(user_id)
        if not subscription:
            return False
        
        # Cancel Stripe subscription
        if subscription.stripe_subscription_id:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE subscriptions SET status = 'cancelled', updated_at = $1 WHERE user_id = $2",
                datetime.now(), user_id
            )
        
        # Downgrade to FREE tier
        await self.create_subscription(user_id, SubscriptionTier.FREE)
        
        logger.info(f"Cancelled subscription for user {user_id}")
        return True
    
    # ===== STORAGE MANAGEMENT =====
    async def allocate_storage(self, user_id: str, tier: SubscriptionTier):
        """Allocate storage based on subscription tier"""
        
        tier_config = SUBSCRIPTION_TIERS[tier]
        storage_limit = tier_config["storage_gb"]
        
        # Create storage allocation record
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO storage_allocations (user_id, tier, storage_limit_gb, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    tier = $2, storage_limit_gb = $3, updated_at = $4
            """, user_id, tier, storage_limit, datetime.now())
    
    async def manage_data_lifecycle(self, user_id: str):
        """Manage data lifecycle based on subscription tier and storage tiers"""
        
        subscription = await self.get_subscription(user_id)
        if not subscription:
            return
        
        tier_config = SUBSCRIPTION_TIERS[subscription.tier]
        retention_days = tier_config["data_retention_days"]
        
        # For FREE tier, delete data older than retention period
        if subscription.tier == SubscriptionTier.FREE and retention_days > 0:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            await self.delete_old_data(user_id, cutoff_date)
        
        # For paid tiers, move data through storage tiers
        else:
            await self.move_data_to_warm_storage(user_id)
            await self.move_data_to_cold_storage(user_id)
    
    async def move_data_to_warm_storage(self, user_id: str):
        """Move data older than 30 days to warm storage"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # Implementation would move data from hot to warm storage
        # This is a simplified version
        logger.info(f"Moving data to warm storage for user {user_id}")
    
    async def move_data_to_cold_storage(self, user_id: str):
        """Move data older than 90 days to cold storage"""
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # Implementation would move data from warm to cold storage
        logger.info(f"Moving data to cold storage for user {user_id}")
    
    async def delete_old_data(self, user_id: str, cutoff_date: datetime):
        """Delete data older than cutoff date (for FREE tier)"""
        
        async with self.db_pool.acquire() as conn:
            deleted_count = await conn.fetchval("""
                DELETE FROM analysis_data 
                WHERE user_id = $1 AND created_at < $2
                RETURNING COUNT(*)
            """, user_id, cutoff_date)
        
        logger.info(f"Deleted {deleted_count} old records for FREE user {user_id}")
    
    # ===== STRIPE INTEGRATION =====
    async def create_stripe_subscription(self, user_id: str, tier: SubscriptionTier, payment_method_id: str):
        """Create Stripe subscription for paid tiers"""
        
        tier_config = SUBSCRIPTION_TIERS[tier]
        
        # Create Stripe customer if doesn't exist
        customer = stripe.Customer.create(
            metadata={"user_id": user_id}
        )
        
        # Attach payment method
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer.id
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                "price_data": {
                    "currency": "myr",
                    "product_data": {
                        "name": tier_config["name"]
                    },
                    "unit_amount": int(tier_config["price_myr"] * 100),  # Convert to cents
                    "recurring": {
                        "interval": "month"
                    }
                }
            }],
            default_payment_method=payment_method_id
        )
        
        return subscription
    
    # ===== HELPER METHODS =====
    async def store_subscription(self, subscription: SubscriptionInfo):
        """Store subscription in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO subscriptions (
                    user_id, tier, status, current_period_start, current_period_end,
                    stripe_subscription_id, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id) DO UPDATE SET
                    tier = $2, status = $3, current_period_start = $4,
                    current_period_end = $5, stripe_subscription_id = $6, updated_at = $8
            """, 
            subscription.user_id, subscription.tier, subscription.status,
            subscription.current_period_start, subscription.current_period_end,
            subscription.stripe_subscription_id, subscription.created_at, subscription.updated_at)
    
    async def initialize_usage_tracking(self, user_id: str, tier: SubscriptionTier):
        """Initialize usage tracking for a user"""
        
        tier_config = SUBSCRIPTION_TIERS[tier]
        now = datetime.now()
        
        usage = UsageStats(
            user_id=user_id,
            subscription_tier=tier,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            analyses_used=0,
            analyses_limit=tier_config["analyses_per_month"],
            storage_used_gb=0.0,
            storage_limit_gb=tier_config["storage_gb"],
            api_calls_used=0,
            api_calls_limit=tier_config["api_calls_per_month"],
            platforms_used=[],
            last_updated=now
        )
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO usage_stats (
                    user_id, subscription_tier, current_period_start, current_period_end,
                    analyses_used, analyses_limit, storage_used_gb, storage_limit_gb,
                    api_calls_used, api_calls_limit, platforms_used, last_updated
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (user_id) DO UPDATE SET
                    subscription_tier = $2, analyses_limit = $6, storage_limit_gb = $8,
                    api_calls_limit = $10, last_updated = $12
            """,
            usage.user_id, usage.subscription_tier, usage.current_period_start,
            usage.current_period_end, usage.analyses_used, usage.analyses_limit,
            usage.storage_used_gb, usage.storage_limit_gb, usage.api_calls_used,
            usage.api_calls_limit, usage.platforms_used, usage.last_updated)

# ===== BACKGROUND TASKS =====
async def daily_cleanup_task(subscription_manager: SubscriptionManager):
    """Daily cleanup and data lifecycle management"""
    
    logger.info("Starting daily cleanup task...")
    
    # Get all active users
    async with subscription_manager.db_pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id FROM subscriptions WHERE status = 'active'")
    
    # Process each user
    for user in users:
        user_id = user['user_id']
        try:
            await subscription_manager.manage_data_lifecycle(user_id)
        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}")
    
    logger.info("Daily cleanup task completed")

async def monthly_billing_task(subscription_manager: SubscriptionManager):
    """Monthly billing and usage reset"""
    
    logger.info("Starting monthly billing task...")
    
    # Reset usage counters for all users
    async with subscription_manager.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE usage_stats SET 
                analyses_used = 0,
                api_calls_used = 0,
                current_period_start = CURRENT_TIMESTAMP,
                current_period_end = CURRENT_TIMESTAMP + INTERVAL '30 days',
                last_updated = CURRENT_TIMESTAMP
        """)
    
    logger.info("Monthly billing task completed")

# Export for use in main application
__all__ = [
    'SubscriptionManager',
    'SubscriptionTier', 
    'SUBSCRIPTION_TIERS',
    'STORAGE_TIERS',
    'SubscriptionInfo',
    'UsageStats',
    'daily_cleanup_task',
    'monthly_billing_task'
]
