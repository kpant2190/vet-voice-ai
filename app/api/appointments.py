"""Appointments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from ..core.database import get_db
from ..models.appointment import Appointment, AppointmentStatus, AppointmentType
from ..services.appointment_service import AppointmentService

router = APIRouter()


# Pydantic models for request/response
class AppointmentCreate(BaseModel):
    clinic_id: int
    pet_name: str
    pet_type: str
    owner_name: str
    owner_phone: str
    owner_email: Optional[str] = None
    appointment_date: datetime
    appointment_type: AppointmentType = AppointmentType.CHECKUP
    reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    clinic_id: int
    pet_name: str
    pet_type: str
    owner_name: str
    owner_phone: str
    owner_email: Optional[str]
    appointment_date: datetime
    appointment_type: AppointmentType
    status: AppointmentStatus
    reason: Optional[str]
    notes: Optional[str]
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    appointment_date: Optional[datetime] = None


class AvailableSlot(BaseModel):
    datetime: datetime
    available: bool


@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    clinic_id: Optional[int] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    owner_phone: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get appointments with optional filtering."""
    
    query = db.query(Appointment)
    
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if date_from:
        query = query.filter(Appointment.appointment_date >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(Appointment.appointment_date <= datetime.combine(date_to, datetime.max.time()))
    
    if owner_phone:
        query = query.filter(Appointment.owner_phone == owner_phone)
    
    appointments = query.order_by(Appointment.appointment_date.desc()).offset(skip).limit(limit).all()
    
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific appointment by ID."""
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new appointment."""
    
    appointment_service = AppointmentService(db)
    
    try:
        appointment = await appointment_service.create_appointment(
            clinic_id=appointment_data.clinic_id,
            pet_name=appointment_data.pet_name,
            pet_type=appointment_data.pet_type,
            owner_name=appointment_data.owner_name,
            owner_phone=appointment_data.owner_phone,
            appointment_date=appointment_data.appointment_date,
            appointment_type=appointment_data.appointment_type,
            reason=appointment_data.reason,
            owner_email=appointment_data.owner_email
        )
        
        return appointment
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating appointment: {str(e)}")


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing appointment."""
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update fields if provided
    if appointment_update.status is not None:
        appointment.status = appointment_update.status
    
    if appointment_update.notes is not None:
        appointment.notes = appointment_update.notes
    
    if appointment_update.appointment_date is not None:
        appointment.appointment_date = appointment_update.appointment_date
    
    try:
        db.commit()
        db.refresh(appointment)
        return appointment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating appointment: {str(e)}")


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """Delete an appointment."""
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        db.delete(appointment)
        db.commit()
        return {"message": "Appointment deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting appointment: {str(e)}")


@router.get("/clinic/{clinic_id}/available-slots")
async def get_available_slots(
    clinic_id: int,
    date: date = Query(..., description="Date to check for available slots"),
    db: Session = Depends(get_db)
):
    """Get available appointment slots for a specific clinic and date."""
    
    appointment_service = AppointmentService(db)
    
    try:
        # Convert date to datetime for the start of the day
        check_date = datetime.combine(date, datetime.min.time())
        
        available_slots = await appointment_service.get_available_slots(
            clinic_id=clinic_id,
            date=check_date
        )
        
        return {
            "date": date,
            "available_slots": [slot.isoformat() for slot in available_slots],
            "total_slots": len(available_slots)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching available slots: {str(e)}")


@router.get("/clinic/{clinic_id}/next-available")
async def get_next_available_slot(
    clinic_id: int,
    preferred_date: Optional[date] = Query(None, description="Preferred start date"),
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days to search ahead"),
    db: Session = Depends(get_db)
):
    """Get the next available appointment slot for a clinic."""
    
    appointment_service = AppointmentService(db)
    
    try:
        start_date = None
        if preferred_date:
            start_date = datetime.combine(preferred_date, datetime.min.time())
        
        next_slot = await appointment_service.find_next_available_slot(
            clinic_id=clinic_id,
            preferred_date=start_date,
            days_ahead=days_ahead
        )
        
        if next_slot:
            return {
                "next_available_slot": next_slot.isoformat(),
                "date": next_slot.date().isoformat(),
                "time": next_slot.time().isoformat()
            }
        else:
            return {
                "next_available_slot": None,
                "message": f"No available slots found in the next {days_ahead} days"
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error finding next available slot: {str(e)}")


@router.get("/search/by-phone")
async def search_appointments_by_phone(
    phone_number: str = Query(..., description="Phone number to search for"),
    clinic_id: Optional[int] = Query(None, description="Limit search to specific clinic"),
    db: Session = Depends(get_db)
):
    """Search for appointments by phone number."""
    
    query = db.query(Appointment).filter(Appointment.owner_phone == phone_number)
    
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    
    return {
        "phone_number": phone_number,
        "appointments": [AppointmentResponse.from_orm(apt) for apt in appointments],
        "total_found": len(appointments)
    }
