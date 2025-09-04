"""Clinics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from ..core.database import get_db
from ..models.clinic import Clinic

router = APIRouter()


# Pydantic models for request/response
class ClinicCreate(BaseModel):
    name: str
    phone_number: str
    email: EmailStr
    address: Optional[str] = None
    business_hours: Optional[str] = None
    ai_enabled: bool = True
    auto_booking_enabled: bool = True
    voice_id: Optional[str] = None
    voice_greeting: Optional[str] = None
    llm_provider: str = "openai"
    system_prompt: Optional[str] = None


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    business_hours: Optional[str] = None
    ai_enabled: Optional[bool] = None
    auto_booking_enabled: Optional[bool] = None
    voice_id: Optional[str] = None
    voice_greeting: Optional[str] = None
    llm_provider: Optional[str] = None
    system_prompt: Optional[str] = None


class ClinicResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    email: str
    address: Optional[str]
    business_hours: Optional[str]
    ai_enabled: bool
    auto_booking_enabled: bool
    voice_id: Optional[str]
    voice_greeting: Optional[str]
    llm_provider: str
    system_prompt: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


from datetime import datetime


@router.get("/", response_model=List[ClinicResponse])
async def get_clinics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name or phone number"),
    db: Session = Depends(get_db)
):
    """Get all clinics with optional search."""
    
    query = db.query(Clinic)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Clinic.name.ilike(search_term)) |
            (Clinic.phone_number.ilike(search_term))
        )
    
    clinics = query.offset(skip).limit(limit).all()
    return clinics


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific clinic by ID."""
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    return clinic


@router.get("/by-phone/{phone_number}", response_model=ClinicResponse)
async def get_clinic_by_phone(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Get a clinic by phone number."""
    
    clinic = db.query(Clinic).filter(Clinic.phone_number == phone_number).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    return clinic


@router.post("/", response_model=ClinicResponse)
async def create_clinic(
    clinic_data: ClinicCreate,
    db: Session = Depends(get_db)
):
    """Create a new clinic."""
    
    # Check if phone number or email already exists
    existing_clinic = db.query(Clinic).filter(
        (Clinic.phone_number == clinic_data.phone_number) |
        (Clinic.email == clinic_data.email)
    ).first()
    
    if existing_clinic:
        raise HTTPException(
            status_code=400,
            detail="A clinic with this phone number or email already exists"
        )
    
    try:
        clinic = Clinic(
            name=clinic_data.name,
            phone_number=clinic_data.phone_number,
            email=clinic_data.email,
            address=clinic_data.address,
            business_hours=clinic_data.business_hours,
            ai_enabled=clinic_data.ai_enabled,
            auto_booking_enabled=clinic_data.auto_booking_enabled,
            voice_id=clinic_data.voice_id,
            voice_greeting=clinic_data.voice_greeting,
            llm_provider=clinic_data.llm_provider,
            system_prompt=clinic_data.system_prompt
        )
        
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        
        return clinic
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating clinic: {str(e)}")


@router.put("/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(
    clinic_id: int,
    clinic_update: ClinicUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing clinic."""
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # Check for duplicate phone/email if they're being updated
    if clinic_update.phone_number or clinic_update.email:
        existing_query = db.query(Clinic).filter(Clinic.id != clinic_id)
        
        if clinic_update.phone_number:
            existing_query = existing_query.filter(Clinic.phone_number == clinic_update.phone_number)
        
        if clinic_update.email:
            existing_query = existing_query.filter(Clinic.email == clinic_update.email)
        
        if existing_query.first():
            raise HTTPException(
                status_code=400,
                detail="A clinic with this phone number or email already exists"
            )
    
    # Update fields if provided
    update_data = clinic_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clinic, field, value)
    
    try:
        db.commit()
        db.refresh(clinic)
        return clinic
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating clinic: {str(e)}")


@router.delete("/{clinic_id}")
async def delete_clinic(
    clinic_id: int,
    db: Session = Depends(get_db)
):
    """Delete a clinic."""
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    try:
        db.delete(clinic)
        db.commit()
        return {"message": "Clinic deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting clinic: {str(e)}")


@router.get("/{clinic_id}/stats")
async def get_clinic_stats(
    clinic_id: int,
    db: Session = Depends(get_db)
):
    """Get statistics for a clinic."""
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # Get appointment counts
    from ..models.appointment import Appointment, AppointmentStatus
    from ..models.call_log import CallLog
    from sqlalchemy import func
    
    total_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.clinic_id == clinic_id
    ).scalar()
    
    pending_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.status == AppointmentStatus.PENDING
    ).scalar()
    
    confirmed_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.status == AppointmentStatus.CONFIRMED
    ).scalar()
    
    total_calls = db.query(func.count(CallLog.id)).filter(
        CallLog.clinic_id == clinic_id
    ).scalar()
    
    ai_created_appointments = db.query(func.count(CallLog.id)).filter(
        CallLog.clinic_id == clinic_id,
        CallLog.appointment_created == True
    ).scalar()
    
    return {
        "clinic_id": clinic_id,
        "clinic_name": clinic.name,
        "total_appointments": total_appointments or 0,
        "pending_appointments": pending_appointments or 0,
        "confirmed_appointments": confirmed_appointments or 0,
        "total_calls": total_calls or 0,
        "ai_created_appointments": ai_created_appointments or 0,
        "ai_booking_rate": (ai_created_appointments / total_calls * 100) if total_calls > 0 else 0
    }
