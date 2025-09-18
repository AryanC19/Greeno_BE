# app/main.py
from fastapi import FastAPI


from .routes import careplan, appointments,doctors , reminders , medications

app = FastAPI(title="GPP CarePlan Parser")

app.include_router(careplan.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")  # include doctor availability endpoints too
app.include_router(doctors.router, prefix="/api")  # include doctor availability endpoints too
app.include_router(reminders.router, prefix="/api")
app.include_router(medications.router, prefix="/api")
