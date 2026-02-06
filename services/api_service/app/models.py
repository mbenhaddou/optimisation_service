import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from .db import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String, default="owner", nullable=False)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, nullable=False, index=True)
    request = Column(JSON, nullable=False)
    result = Column(JSON)
    error = Column(Text)
    node_count = Column(Integer)
    usage_units = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True, index=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    node_count = Column(Integer)
    usage_units = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_name = Column(String, default="free", nullable=False)
    status = Column(String, default="trialing", nullable=False)
    free_tier_units = Column(Integer, nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
