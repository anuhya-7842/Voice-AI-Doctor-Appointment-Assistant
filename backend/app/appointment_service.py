
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import Doctor, Slot, Appointment


def normalize_phone(phone: str) -> str:
    """Keep digits only from the spoken phone number."""
    return "".join(ch for ch in phone if ch.isdigit())


def check_doctor_availability(
    db: Session,
    specialty: str = None,
    doctor_id: int = None,
    appointment_date: str = None
):
    query = db.query(Doctor)

    if specialty:
        specialty = specialty.strip().lower()

    specialty_mapping = {
        "dermatologist": "Dermatology",
        "dermatology": "Dermatology",
        "cardiologist": "Cardiology",
        "cardiology": "Cardiology",
        "neurologist": "Neurology",
        "neurology": "Neurology",
        "general physician": "General Medicine",
        "general medicine": "General Medicine",
    }

    specialty = specialty_mapping.get(specialty, specialty)

    query = query.filter(
        Doctor.specialty.ilike(f"%{specialty}%")
    )

    if doctor_id:
        query = query.filter(Doctor.id == doctor_id)

    doctors = query.all()
    results = []

    for doctor in doctors:
        slots_query = db.query(Slot).filter(
            Slot.doctor_id == doctor.id,
            Slot.is_booked == 0
        )

        if appointment_date:
            slots_query = slots_query.filter(
                Slot.date == appointment_date
            )

        available_slots = slots_query.order_by(
            Slot.date,
            Slot.id
        ).all()

        slot_list = []

        for slot in available_slots:
            slot_list.append({
                "slot_id": slot.id,
                "date": slot.date,
                "time": slot.time
            })

        doctor_info = {
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "specialty": doctor.specialty,
            "experience": doctor.experience,
            "consultation_fee": doctor.consultation_fee,
            "available_slots": slot_list
        }

        results.append(doctor_info)

    return results

def book_appointment(
    db: Session,
    slot_id: int,
    patient_phone: str,
    phone_confirmed: bool = False,
):
    """Book a slot only after the patient confirms their phone number."""

    phone = normalize_phone(patient_phone)

    if not phone_confirmed:
        return {
            "success": False,
            "message": "Phone number must be confirmed before booking.",
        }

    if not 7 <= len(phone) <= 15:
        return {
            "success": False,
            "message": "Please provide a valid phone number.",
        }

    try:
        # Atomically claim the slot to prevent concurrent double-booking.
        claimed = (
            db.query(Slot)
            .filter(Slot.id == slot_id, Slot.is_booked == 0)
            .update({Slot.is_booked: 1}, synchronize_session=False)
        )

        if claimed != 1:
            db.rollback()
            return {
                "success": False,
                "message": "This slot is no longer available. Please select another slot.",
            }

        slot = db.query(Slot).filter(Slot.id == slot_id).first()

        # Check for an active appointment occupying the same slot.
        existing = db.query(Appointment).filter(
            Appointment.slot_id == slot_id,
            Appointment.status == "booked",
        ).first()

        if existing:
            db.rollback()
            return {
                "success": False,
                "message": "This slot is already booked.",
            }

        appointment = Appointment(
            slot_id=slot_id,
            patient_phone=phone,
            status="booked",
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        doctor = db.query(Doctor).filter(
            Doctor.id == slot.doctor_id
        ).first()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "doctor_name": doctor.name,
            "specialty": doctor.specialty,
            "date": slot.date,
            "time": slot.time,
            "patient_phone": phone,
            "message": "Appointment booked successfully.",
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Booking failed: {str(e)}",
        }


def cancel_appointment(
    db: Session,
    patient_phone: str,
    appointment_id: int = None,
    phone_confirmed: bool = False,
):
    """Cancel an active appointment belonging to the confirmed phone number."""

    phone = normalize_phone(patient_phone)

    if not phone_confirmed:
        return {
            "success": False,
            "message": "Phone number must be confirmed before cancellation.",
        }

    if not 7 <= len(phone) <= 15:
        return {
            "success": False,
            "message": "Please provide a valid phone number.",
        }

    query = db.query(Appointment).filter(
        Appointment.patient_phone == phone,
        Appointment.status == "booked",
    )

    if appointment_id is not None:
        query = query.filter(Appointment.id == appointment_id)

    appointment = query.order_by(Appointment.id).first()

    if not appointment:
        return {
            "success": False,
            "message": "No active appointment found for this phone number.",
        }

    try:
        slot = db.query(Slot).filter(
            Slot.id == appointment.slot_id
        ).first()

        doctor = db.query(Doctor).filter(
            Doctor.id == slot.doctor_id
        ).first()

        # Release slot and retain cancellation history.
        appointment.status = "cancelled"
        slot.is_booked = 0

        db.commit()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "doctor_name": doctor.name,
            "date": slot.date,
            "time": slot.time,
            "patient_phone": phone,
            "message": "Appointment cancelled successfully.",
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Cancellation failed: {str(e)}",
        }


def get_all_appointments(db: Session):
    """Return appointments for the dashboard."""

    appointments = db.query(Appointment).order_by(
        Appointment.id.desc()
    ).all()

    results = []

    for appointment in appointments:
        slot = db.query(Slot).filter(
            Slot.id == appointment.slot_id
        ).first()

        doctor = db.query(Doctor).filter(
            Doctor.id == slot.doctor_id
        ).first()

        results.append({
            "appointment_id": appointment.id,
            "patient_phone": appointment.patient_phone,
            "status": appointment.status,
            "doctor_name": doctor.name,
            "specialty": doctor.specialty,
            "date": slot.date,
            "time": slot.time,
        })

    return results
