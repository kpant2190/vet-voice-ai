"""Database models for the application."""

from .clinic import Clinic
from .appointment import Appointment
from .call_log import CallLog

__all__ = ["Clinic", "Appointment", "CallLog"]
