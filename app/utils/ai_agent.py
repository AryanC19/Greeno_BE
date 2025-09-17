from ..service.crud_doctor_availabilty import get_doctor_by_specialty
from ..database import db

CAREPLANS_COLL = "careplans"

async def assign_slot_to_appointment(patient_id: str, appointment_id: str, specialty: str):
    # 1️⃣ Get doctor by specialty
    doctor = await get_doctor_by_specialty(specialty)
    if not doctor or "available_slots" not in doctor or not doctor["available_slots"]:
        return None
    available_slots = doctor["available_slots"]

    # 2️⃣ Get current booked slots for patient
    careplan = await db[CAREPLANS_COLL].find_one({"patient_id": patient_id})
    booked_slots = [
        a.get("proposed_slot") for a in careplan.get("appointments", []) if a.get("proposed_slot")
    ]

    # 3️⃣ Find first free slot
    proposed_slot = None
    for slot in available_slots:
        if slot not in booked_slots:
            proposed_slot = slot
            break

    if not proposed_slot:
        return None

    # 4️⃣ Update appointment in careplan
    await db[CAREPLANS_COLL].update_one(
        {"patient_id": patient_id, "appointments.id": appointment_id},
        {"$set": {"appointments.$.proposed_slot": proposed_slot}}
    )

    return proposed_slot
