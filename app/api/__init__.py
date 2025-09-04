"""API routes for the Vet Voice AI application."""

from .voice import router as voice_router
from .appointments import router as appointments_router
from .clinics import router as clinics_router

__all__ = ["voice_router", "appointments_router", "clinics_router"]
