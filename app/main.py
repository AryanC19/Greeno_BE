# app/main.py
from fastapi import FastAPI

from .routes import (
    careplan,
    appointments,
    doctors,
    reminders,
    medications,
    exercise,
    chat
)

app = FastAPI(title="GPP CarePlan Parser")

# Routers with prefixes + tags for Swagger
app.include_router(careplan.router, prefix="/api/careplans", tags=["CarePlans"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
#app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])
app.include_router(exercise.router, prefix="/api/exercise", tags=["Exercise & Diet"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])  # applies globally
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])  