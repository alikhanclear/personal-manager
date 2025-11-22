"""
Data models for personal finance application.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4
import hashlib

from pydantic import BaseModel, Field, field_validator, model_validator


class Transaction(BaseModel):
    """Transaction record from bank statement."""

    id: str = ""  # Generated deterministically from transaction properties
    date: date
    description: str
    merchant: Optional[str] = None  # Cleaned/normalized merchant name
    amount: Decimal
    balance: Optional[Decimal] = None
    account_name: str
    account_number: str
    transaction_type: Optional[str] = None  # POS, DPC, BAC, etc.

    # AI categorization fields
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    category_confirmed: bool = False

    # Additional metadata
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('amount', 'balance', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert amount/balance to Decimal for precision."""
        if v is None:
            return v
        return Decimal(str(v))

    @model_validator(mode='after')
    def generate_id_if_empty(self):
        """Generate deterministic ID from transaction properties if not already set."""
        if not self.id:
            # Create unique string from transaction properties
            # Uses: date + description + amount + account_number
            unique_string = (
                f"{self.date.isoformat()}|"
                f"{self.description}|"
                f"{str(self.amount)}|"
                f"{self.account_number}"
            )
            # Generate MD5 hash (deterministic - same input = same output)
            self.id = hashlib.md5(unique_string.encode()).hexdigest()
        return self

    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }


class Category(BaseModel):
    """Spending category definition."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    parent_id: Optional[str] = None  # For hierarchical categories
    color: str = "#3498db"  # Default blue
    icon: str = "💰"  # Default money emoji
    budget_monthly: Optional[Decimal] = None

    @field_validator('budget_monthly', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert budget to Decimal for precision."""
        if v is None:
            return v
        return Decimal(str(v))


class Rule(BaseModel):
    """Categorization rule for automatic tagging."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    pattern: str  # Regex or keyword to match in description
    category_id: str
    priority: int = 0  # Higher priority rules applied first
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class PotentialDuplicate(BaseModel):
    """Potential duplicate transaction flagged during import."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_id: str  # ID of the duplicate transaction (same hash as original)

    # Store full transaction data as JSON
    date: date
    description: str
    amount: Decimal
    balance: Optional[Decimal] = None
    account_name: str
    account_number: str

    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolution: Optional[str] = None  # 'keep_both', 'keep_original', 'dismissed'
    resolved_at: Optional[datetime] = None

    @field_validator('amount', 'balance', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert amount/balance to Decimal for precision."""
        if v is None:
            return v
        return Decimal(str(v))

    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }
