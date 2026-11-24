
from datetime import date, timedelta

from .database import Base, engine, SessionLocal
from .models import Doctor, Slot, Appointment


DOCTORS = [
    {
        "name": "Dr. Asha Sharma",
        "specialty": "Cardiology",
        "experience": 12,
        "consultation_fee": 700,
    },
    {
        "name": "Dr. Rahul Verma",
        "specialty": "Dermatology",
        "experience": 8,
        "consultation_fee": 500,
    },
    {
        "name": "Dr. Neha Reddy",
        "specialty": "Neurology",
        "experience": 10,
        "consultation_fee": 800,
    },
    {
        "name": "Dr. Kiran Rao",
        "specialty": "General Medicine",
        "experience": 15,
        "consultation_fee": 400,
    },
]

SLOT_TIMES = [
    "09:00 AM",
    "10:00 AM",
    "11:30 AM",
    "02:00 PM",
    "03:30 PM",
]


def initialize_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Seed doctors only if the table is empty
        if db.query(Doctor).count() == 0:
            for doctor_data in DOCTORS:
                doctor = Doctor(**doctor_data)
                db.add(doctor)

            db.commit()

        # Seed slots only if the table is empty
        if db.query(Slot).count() == 0:
            doctors = db.query(Doctor).all()

            for doctor in doctors:
                for day_offset in range(3):
                    appointment_date = (
                        date.today() + timedelta(days=day_offset)
                    ).isoformat()

                    for slot_time in SLOT_TIMES:
                        slot = Slot(
                            doctor_id=doctor.id,
                            date=appointment_date,
                            time=slot_time,
                            is_booked=0,
                        )
                        db.add(slot)

            db.commit()

        print("Database initialized successfully!")
        print(f"Doctors available: {db.query(Doctor).count()}")
        print(f"Slots created: {db.query(Slot).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
