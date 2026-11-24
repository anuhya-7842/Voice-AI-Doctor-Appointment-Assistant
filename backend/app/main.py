
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db
from .doctors_data import initialize_database
from .models import Doctor
from .appointment_service import (
    check_doctor_availability,
    get_all_appointments
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Voice AI Doctor Appointment Assistant",
    description="Backend API for the voice-based doctor appointment system",
    version="1.0.0",
    lifespan=lifespan
)


# Allow frontend development servers to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():
    return {
        "message": "Voice AI Doctor Appointment Assistant API is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/api/doctors")
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()

    return [
        {
            "doctor_id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "experience": doctor.experience,
            "consultation_fee": doctor.consultation_fee
        }
        for doctor in doctors
    ]


@app.get("/api/availability")
def get_availability(
    specialty: str = Query(default=None),
    doctor_id: int = Query(default=None),
    appointment_date: str = Query(default=None),
    db: Session = Depends(get_db)
):
    return check_doctor_availability(
        db=db,
        specialty=specialty,
        doctor_id=doctor_id,
        appointment_date=appointment_date
    )


@app.get("/api/appointments")
def get_appointments(db: Session = Depends(get_db)):
    return get_all_appointments(db)
