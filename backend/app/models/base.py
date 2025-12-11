"""
SQLAlchemy base model and mixins.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Adds `is_deleted` and `deleted_at` columns to models.
    Use this for tables where data retention is important.
    
    Usage:
        class Order(Base, SoftDeleteMixin):
            __tablename__ = "orders"
            ...
    
    Query active records:
        session.query(Order).filter(Order.is_deleted == False)
    
    Soft delete:
        order.is_deleted = True
        order.deleted_at = datetime.utcnow()
    """
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True,
        comment="Whether this record has been soft deleted"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        comment="Timestamp when the record was soft deleted"
    )
    
    def soft_delete(self) -> None:
        """Mark this record as soft deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class TimestampMixin:
    """
    Mixin for standard timestamp fields.
    
    Adds `created_at` and `updated_at` columns to models using server-side defaults.
    
    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_models"
            ...
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )
