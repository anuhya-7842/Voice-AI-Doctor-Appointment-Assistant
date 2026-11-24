
from backend.app.database import SessionLocal
from backend.app.models import Doctor, Slot, Appointment
from backend.app.appointment_service import (
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
    get_all_appointments
)


def run_tests():
    db = SessionLocal()

    try:
        print("\nRunning appointment service tests...\n")

        # Test 1: Check doctor availability
        availability = check_doctor_availability(
            db,
            specialty="Cardiology"
        )
        assert len(availability) > 0
        print("TEST 1 PASSED: Doctor availability")

        # Test 2: Reject unconfirmed phone number
        available_slot = (
            db.query(Slot)
            .filter(Slot.is_booked == 0)
            .first()
        )

        result = book_appointment(
            db,
            available_slot.id,
            "9876543210",
            phone_confirmed=False
        )
        assert result["success"] is False
        print("TEST 2 PASSED: Unconfirmed phone rejected")

        # Test 3: Book an available slot
        result = book_appointment(
            db,
            available_slot.id,
            "9876543210",
            phone_confirmed=True
        )
        assert result["success"] is True
        appointment_id = result["appointment_id"]
        print("TEST 3 PASSED: Appointment booking")

        # Test 4: Prevent duplicate booking
        duplicate = book_appointment(
            db,
            available_slot.id,
            "9123456780",
            phone_confirmed=True
        )
        assert duplicate["success"] is False
        print("TEST 4 PASSED: Duplicate booking prevented")

        # Test 5: Cancel the appointment
        cancellation = cancel_appointment(
            db,
            "9876543210",
            appointment_id=appointment_id,
            phone_confirmed=True
        )
        assert cancellation["success"] is True
        print("TEST 5 PASSED: Appointment cancellation")

        # Test 6: Confirm slot is available again
        db.refresh(available_slot)
        assert available_slot.is_booked == 0
        print("TEST 6 PASSED: Cancelled slot released")

        # Test 7: Check appointment history
        history = get_all_appointments(db)
        cancelled = [
            item for item in history
            if item["appointment_id"] == appointment_id
        ]
        assert len(cancelled) == 1
        assert cancelled[0]["status"] == "cancelled"
        print("TEST 7 PASSED: Appointment history")

        print("\nALL TESTS PASSED!")

    except Exception as error:
        db.rollback()
        print("\nTEST FAILED:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
