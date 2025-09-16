# app/main.py
from fastapi import FastAPI


from .routes import careplan, appointments,doctors , reminders

app = FastAPI(title="GPP CarePlan Parser")

app.include_router(careplan.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")  # include doctor availability endpoints too
app.include_router(doctors.router, prefix="/api")  # include doctor availability endpoints too
app.include_router(reminders.router, prefix="/api")
