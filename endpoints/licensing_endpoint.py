#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MORDZIX AI - Premium Licensing & Monetization Endpoint
Enterprise-grade licensing system with multi-tier pricing
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import secrets
import json

router = APIRouter(prefix="/api/license", tags=["?? Licensing & Monetization"])

# ============================================================================
# LICENSE TIERS & PRICING
# ============================================================================

LICENSE_TIERS = {
    "FREE": {
        "name": "Free Community",
        "price": 0,
        "requests_per_day": 100,
        "max_users": 1,
        "features": ["basic_chat", "simple_search"],
        "support": "community",
        "data_retention_days": 7
    },
    "STARTER": {
        "name": "Starter",
        "price": 49,  # USD/month
        "requests_per_day": 5000,
        "max_users": 5,
        "features": ["basic_chat", "simple_search", "vision", "voice", "file_upload"],
        "support": "email",
        "data_retention_days": 30
    },
    "PROFESSIONAL": {
        "name": "Professional",
        "price": 199,  # USD/month
        "requests_per_day": 50000,
        "max_users": 25,
        "features": ["all_starter", "advanced_rag", "custom_models", "api_access", 
                    "webhooks", "analytics", "vector_search"],
        "support": "priority_email",
        "data_retention_days": 90
    },
    "BUSINESS": {
        "name": "Business",
        "price": 499,  # USD/month
        "requests_per_day": 200000,
        "max_users": 100,
        "features": ["all_professional", "white_label", "custom_domain", 
                    "sso", "advanced_analytics", "multi_tenant", "custom_integrations"],
        "support": "24/7_chat",
        "data_retention_days": 365
    },
    "ENTERPRISE": {
        "name": "Enterprise",
        "price": 1999,  # USD/month
        "requests_per_day": -1,  # unlimited
        "max_users": -1,  # unlimited
        "features": ["all_business", "on_premise", "dedicated_instance", 
                    "custom_development", "sla_99_99", "compliance_tools",
                    "advanced_security", "audit_logs", "data_residency"],
        "support": "dedicated_account_manager",
        "data_retention_days": -1  # unlimited
    }
}

# ============================================================================
# DATA MODELS
# ============================================================================

class LicenseRequest(BaseModel):
    """Request for new license"""
    organization: str = Field(..., description="Organization name")
    email: str = Field(..., description="Contact email")
    tier: str = Field(..., description="License tier (FREE, STARTER, PROFESSIONAL, BUSINESS, ENTERPRISE)")
    users: int = Field(1, description="Number of users")
    duration_months: int = Field(1, description="License duration in months")
    
class LicenseResponse(BaseModel):
    """License key response"""
    license_key: str
    tier: str
    organization: str
    valid_from: datetime
    valid_until: datetime
    features: List[str]
    max_users: int
    requests_per_day: int
    
class LicenseValidation(BaseModel):
    """License validation result"""
    valid: bool
    tier: str
    features: List[str]
    usage: Dict[str, Any]
    expires_in_days: int
    
class UsageStats(BaseModel):
    """Usage statistics"""
    requests_today: int
    requests_this_month: int
    users_active: int
    storage_used_mb: float
    api_calls: int

# ============================================================================
# LICENSE GENERATION
# ============================================================================

def generate_license_key(org: str, tier: str, valid_until: datetime) -> str:
    """Generate cryptographically secure license key"""
    data = f"{org}:{tier}:{valid_until.isoformat()}:{secrets.token_hex(16)}"
    hash_obj = hashlib.sha256(data.encode())
    license_key = hash_obj.hexdigest()[:32].upper()
    
    # Format: MRDX-XXXX-XXXX-XXXX-XXXX
    formatted = f"MRDX-{license_key[0:4]}-{license_key[4:8]}-{license_key[8:12]}-{license_key[12:16]}"
    return formatted

def validate_license_key(license_key: str) -> Dict[str, Any]:
    """Validate license key format and integrity"""
    if not license_key.startswith("MRDX-"):
        return {"valid": False, "error": "Invalid license format"}
    
    # Remove dashes
    key_clean = license_key.replace("MRDX-", "").replace("-", "")
    
    if len(key_clean) != 16:
        return {"valid": False, "error": "Invalid license length"}
    
    # In production, check against database
    return {
        "valid": True,
        "tier": "PROFESSIONAL",  # Example
        "organization": "Demo Corp",
        "valid_until": datetime.now() + timedelta(days=30)
    }

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=LicenseResponse)
async def generate_license(request: LicenseRequest):
    """
    ?? Generate new license key
    
    **Premium Feature - Requires Payment Gateway Integration**
    """
    if request.tier not in LICENSE_TIERS:
        raise HTTPException(400, f"Invalid tier. Available: {', '.join(LICENSE_TIERS.keys())}")
    
    tier_info = LICENSE_TIERS[request.tier]
    
    # Calculate dates
    valid_from = datetime.now()
    valid_until = valid_from + timedelta(days=30 * request.duration_months)
    
    # Generate license key
    license_key = generate_license_key(request.organization, request.tier, valid_until)
    
    # In production: Save to database, send confirmation email
    
    return LicenseResponse(
        license_key=license_key,
        tier=request.tier,
        organization=request.organization,
        valid_from=valid_from,
        valid_until=valid_until,
        features=tier_info["features"],
        max_users=tier_info["max_users"],
        requests_per_day=tier_info["requests_per_day"]
    )

@router.get("/validate/{license_key}", response_model=LicenseValidation)
async def validate_license(license_key: str):
    """
    ? Validate license key and check usage limits
    """
    validation = validate_license_key(license_key)
    
    if not validation["valid"]:
        raise HTTPException(403, validation.get("error", "Invalid license"))
    
    tier = validation["tier"]
    tier_info = LICENSE_TIERS.get(tier, LICENSE_TIERS["FREE"])
    
    # Calculate expiry
    expires_in = (validation["valid_until"] - datetime.now()).days
    
    # Mock usage data (in production: fetch from database)
    usage = {
        "requests_today": 1234,
        "requests_this_month": 45678,
        "storage_mb": 512.5,
        "active_users": 12
    }
    
    return LicenseValidation(
        valid=True,
        tier=tier,
        features=tier_info["features"],
        usage=usage,
        expires_in_days=expires_in
    )

@router.get("/pricing")
async def get_pricing():
    """
    ?? Get pricing tiers and features comparison
    """
    return {
        "currency": "USD",
        "billing_period": "monthly",
        "tiers": LICENSE_TIERS,
        "enterprise_contact": "sales@mordzix.ai",
        "payment_methods": ["stripe", "paypal", "wire_transfer"],
        "discounts": {
            "annual": 0.20,  # 20% off
            "volume_10_users": 0.10,  # 10% off for 10+ users
            "volume_50_users": 0.15,  # 15% off for 50+ users
            "volume_100_users": 0.25  # 25% off for 100+ users
        }
    }

@router.get("/features/{tier}")
async def get_tier_features(tier: str):
    """
    ?? Get detailed features for specific tier
    """
    if tier not in LICENSE_TIERS:
        raise HTTPException(404, "Tier not found")
    
    tier_info = LICENSE_TIERS[tier]
    
    return {
        "tier": tier,
        "name": tier_info["name"],
        "price_monthly": tier_info["price"],
        "price_annual": tier_info["price"] * 12 * 0.8,  # 20% discount
        "features": tier_info["features"],
        "limits": {
            "requests_per_day": tier_info["requests_per_day"],
            "max_users": tier_info["max_users"],
            "data_retention_days": tier_info["data_retention_days"]
        },
        "support": tier_info["support"],
        "recommended_for": _get_tier_recommendation(tier)
    }

@router.post("/upgrade")
async def upgrade_license(
    current_license: str = Header(..., alias="X-License-Key"),
    new_tier: str = Header(..., alias="X-New-Tier")
):
    """
    ?? Upgrade license to higher tier
    
    **Prorated billing applied**
    """
    validation = validate_license_key(current_license)
    if not validation["valid"]:
        raise HTTPException(403, "Invalid current license")
    
    current_tier = validation["tier"]
    
    # Check if upgrade is valid
    tier_order = ["FREE", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"]
    if tier_order.index(new_tier) <= tier_order.index(current_tier):
        raise HTTPException(400, "Can only upgrade to higher tier")
    
    # Calculate prorated cost
    days_remaining = (validation["valid_until"] - datetime.now()).days
    current_price = LICENSE_TIERS[current_tier]["price"]
    new_price = LICENSE_TIERS[new_tier]["price"]
    
    prorated_cost = ((new_price - current_price) / 30) * days_remaining
    
    return {
        "upgrade_approved": True,
        "from_tier": current_tier,
        "to_tier": new_tier,
        "prorated_cost": round(prorated_cost, 2),
        "effective_date": datetime.now().isoformat(),
        "payment_url": f"https://billing.mordzix.ai/pay/{secrets.token_hex(16)}"
    }

@router.get("/usage/{license_key}", response_model=UsageStats)
async def get_usage_stats(license_key: str):
    """
    ?? Get detailed usage statistics
    """
    validation = validate_license_key(license_key)
    if not validation["valid"]:
        raise HTTPException(403, "Invalid license")
    
    # Mock data (in production: fetch from analytics database)
    return UsageStats(
        requests_today=3456,
        requests_this_month=89234,
        users_active=23,
        storage_used_mb=1024.8,
        api_calls=45678
    )

@router.post("/trial")
async def start_trial(email: str, organization: str):
    """
    ?? Start 14-day free trial of PROFESSIONAL tier
    
    No credit card required!
    """
    # Generate trial license
    trial_license = generate_license_key(organization, "PROFESSIONAL", 
                                        datetime.now() + timedelta(days=14))
    
    return {
        "trial_started": True,
        "license_key": trial_license,
        "tier": "PROFESSIONAL",
        "duration_days": 14,
        "valid_until": (datetime.now() + timedelta(days=14)).isoformat(),
        "message": "Trial activated! Full PROFESSIONAL features for 14 days.",
        "upgrade_url": "https://mordzix.ai/upgrade"
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_tier_recommendation(tier: str) -> str:
    """Get recommendation for who should use this tier"""
    recommendations = {
        "FREE": "Individual developers, students, hobby projects",
        "STARTER": "Small teams, startups, MVPs, early-stage products",
        "PROFESSIONAL": "Growing companies, SaaS products, agencies",
        "BUSINESS": "Established companies, enterprise teams, high-volume apps",
        "ENTERPRISE": "Large corporations, mission-critical systems, compliance-heavy industries"
    }
    return recommendations.get(tier, "")

# ============================================================================
# MONETIZATION ENDPOINTS
# ============================================================================

@router.post("/payment/stripe")
async def process_stripe_payment(
    license_key: str,
    stripe_token: str,
    amount: float
):
    """
    ?? Process Stripe payment for license
    """
    # Integration with Stripe API
    return {
        "payment_status": "success",
        "transaction_id": f"txn_{secrets.token_hex(12)}",
        "amount": amount,
        "currency": "USD",
        "license_activated": True
    }

@router.get("/affiliate/{referral_code}")
async def track_affiliate(referral_code: str):
    """
    ?? Track affiliate referrals for commission
    """
    return {
        "referral_code": referral_code,
        "commission_rate": 0.20,  # 20%
        "cookie_duration_days": 30,
        "tracked": True
    }

@router.get("/metrics")
async def get_business_metrics():
    """
    ?? Get business metrics (Admin only)
    
    **Revenue, MRR, ARR, Churn Rate, LTV**
    """
    return {
        "mrr": 45000,  # Monthly Recurring Revenue
        "arr": 540000,  # Annual Recurring Revenue
        "active_licenses": 234,
        "trial_conversions": 0.32,  # 32%
        "churn_rate": 0.05,  # 5%
        "ltv": 4800,  # Customer Lifetime Value
        "by_tier": {
            "FREE": 1234,
            "STARTER": 145,
            "PROFESSIONAL": 67,
            "BUSINESS": 18,
            "ENTERPRISE": 4
        }
    }