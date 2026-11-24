
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    experience = Column(Integer, nullable=False)
    consultation_fee = Column(Integer, nullable=False)

    slots = relationship("Slot", back_populates="doctor")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    is_booked = Column(Integer, default=0, nullable=False)

    doctor = relationship("Doctor", back_populates="slots")
    appointments = relationship("Appointment", back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    patient_phone = Column(String, nullable=False)
    status = Column(String, default="booked", nullable=False)

    slot = relationship("Slot", back_populates="appointments")
