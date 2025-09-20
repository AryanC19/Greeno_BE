# app/models.py
from typing import List, Optional , Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str


class User(BaseModel):
    id: Optional[str] = None
    email: str
    password: str   # store hashed, not plain text
    name: Optional[str] = None


class MedicationSchedule(BaseModel):
    time: str                     # e.g. "morning", "evening"
    taken: Optional[bool] = None  # None = not decided ye     



class Medication(BaseModel):
    id: Optional[str] = None
    name: str
    dose: Optional[str] = None
    schedule: List[MedicationSchedule] = Field(default_factory=list)  
    duration: Optional[str] = None  # e.g. "7 days"


class Appointment(BaseModel):
    id: Optional[str] = None
    type: str
    status: str = "pending"      # pending / confirmed / declined

class ReminderSlot(BaseModel):
    time: Optional[str] = None   # HH:mm



class CarePlanCreate(BaseModel):
    patient_id: str
    medications: List[Medication] = Field(default_factory=list)
    appointments: List[Appointment] = Field(default_factory=list)
    reminder_slots: Dict[str, ReminderSlot] = Field(default_factory=lambda: {
        "morning": ReminderSlot(),
        "afternoon": ReminderSlot(),
        "evening": ReminderSlot(),
        "night": ReminderSlot()
    })
    medical_history: Optional[str] = None  # <--- add this

class CarePlanInDB(CarePlanCreate):
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorAvailability(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: Optional[str] = None
    available_slots: List[datetime]  # e.g. ["2025-09-17T10:30:00", "2025-09-18T14:00:00"]
