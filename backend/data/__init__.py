"""
Data Access Layer

This module provides a clean abstraction over database operations.
All MongoDB operations should go through this layer.
"""

from .repositories import (
    UserRepository,
    ProjectRepository,
    NotificationRepository,
    DrawingRepository
)

__all__ = [
    'UserRepository',
    'ProjectRepository', 
    'NotificationRepository',
    'DrawingRepository'
]
