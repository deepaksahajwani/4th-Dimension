"""
Integrations Layer

This module provides a clean abstraction over third-party services.
All external API calls should go through this layer.
"""

from .twilio_service import TwilioService
from .sendgrid_service import SendGridService
from .notification_logger import NotificationLogger

__all__ = ['TwilioService', 'SendGridService', 'NotificationLogger']
