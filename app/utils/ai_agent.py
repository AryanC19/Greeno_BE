from ..database import db


async def assign_slot_to_appointment(patient_id: str, appointment_id: str, doctor_id: str) -> str:
    """
    Picks the first available slot from doctor availability
    and adds it to the appointment as proposed_slot.
    """
    
    CAREPLANS_COLL = "careplans"
    DOCTOR_AVAIL_COLL = "doctor_availability"

    # 1. Get doctor availability
    doc = await db[DOCTOR_AVAIL_COLL].find_one({"doctor_id": doctor_id})
    if not doc or not doc.get("available_slots"):
        return None
    available_slots = doc["available_slots"]

    # 2. Get current booked slots for patient
    careplan = await db[CAREPLANS_COLL].find_one({"patient_id": patient_id})
    booked_slots = [
        a.get("proposed_slot") for a in careplan.get("appointments", []) if a.get("proposed_slot")
    ]

    # 3. Find first free slot
    proposed_slot = None
    for slot in available_slots:
        if slot not in booked_slots:
            proposed_slot = slot
            break

    if not proposed_slot:
        return None

    # 4. Update appointment in careplan
    await db[CAREPLANS_COLL].update_one(
        {"patient_id": patient_id, "appointments.id": appointment_id},
        {"$set": {"appointments.$.proposed_slot": proposed_slot}}
    )

    return proposed_slot
