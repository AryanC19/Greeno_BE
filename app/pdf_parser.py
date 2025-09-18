# app/pdf_parser.py
import pdfplumber
import re
import uuid
from typing import List
from app.models import CarePlanCreate, Medication, Appointment, MedicationSchedule

_HEADING_MATCH_FLAGS = re.IGNORECASE | re.MULTILINE

def _find_section(full_text: str, heading: str, next_headings: List[str]) -> str:
    if not full_text:
        return ""
    pattern = re.compile(rf"^\s*{re.escape(heading)}\s*:?\s*$", _HEADING_MATCH_FLAGS)
    m = pattern.search(full_text)
    if not m:
        return ""
    start = m.end()
    end = len(full_text)
    for nh in next_headings:
        if nh.lower() == heading.lower():
            continue
        p = re.compile(rf"^\s*{re.escape(nh)}\s*:?\s*$", _HEADING_MATCH_FLAGS)
        mm = p.search(full_text, start)
        if mm and mm.start() < end:
            end = mm.start()
    return full_text[start:end].strip()


def _split_to_blocks(section_text: str) -> List[str]:
    if not section_text:
        return []
    lines = section_text.splitlines()
    blocks: List[List[str]] = []
    current: List[str] = []

    for ln in lines:
        s = ln.strip()
        if not s:
            if current:
                blocks.append(current)
                current = []
            continue
        if re.match(r'^[-•\*\u2022]\s+|^\d+\.\s+', s):
            if current:
                blocks.append(current)
            current = [s]
        else:
            if current:
                current.append(s)
            else:
                current = [s]
    if current:
        blocks.append(current)
    return ["\n".join(b) for b in blocks]


def _clean_bullet_prefix(text: str) -> str:
    return re.sub(r'^\s*[-•\*\u2022]?\s*\d*\.?\s*[:\-–—\s]*', '', text).strip()


def parse_medications_section(text: str) -> List[Medication]:
    meds: List[Medication] = []
    blocks = _split_to_blocks(text)
    for blk in blocks:
        blk_norm = _clean_bullet_prefix(blk.strip())
        if not blk_norm:
            continue

        name = None
        dose = None
        schedule: List[MedicationSchedule] = []   # fixed initialization
        duration = None

        # Extract name
        m_name = re.search(r'(?:Medicine|Medication|Name)\s*[:\-]\s*(.+)', blk_norm, re.IGNORECASE)
        if m_name:
            name = m_name.group(1).strip().splitlines()[0]
        else:
            first_line = blk_norm.splitlines()[0]
            first_line = re.sub(r'^(?:Medicine|Medication|Name)\s*[:\-]?\s*', '', first_line, flags=re.IGNORECASE)
            first_line = re.split(r'\bDose\b|\bDose:\b', first_line, flags=re.IGNORECASE)[0]
            name = first_line.strip()

        # Extract dose
        d = re.search(r'Dose\s*[:\-]\s*([^\n]+)', blk_norm, re.IGNORECASE)
        if d:
            dose = d.group(1).strip()

        # Extract timing -> now schedule
        t = re.search(r'(?:Time|When to take|Timing|Frequency)\s*[:\-]\s*([^\n]+)', blk_norm, re.IGNORECASE)
        if t:
            timing_raw = t.group(1).strip()
            timing_list = [x.strip().lower() for x in re.split(r'[;,/]+', timing_raw) if x.strip()]
            schedule = [MedicationSchedule(time=tm, taken=None) for tm in timing_list]
        else:
            # fallback if no timing in PDF
            schedule = [MedicationSchedule(time="unspecified", taken=None)]

        # Extract duration
        dur = re.search(r'(?:Duration|For how long|Days|Weeks|Months)\s*[:\-]\s*([^\n]+)', blk_norm, re.IGNORECASE)
        if dur:
            duration = dur.group(1).strip()

        meds.append(Medication(
            id=str(uuid.uuid4()),
            name=name,
            dose=dose,
            schedule=schedule,  # now using MedicationSchedule
            duration=duration
        ))
    return meds



def parse_appointments_section(text: str) -> List[Appointment]:
    appts: List[Appointment] = []
    blocks = _split_to_blocks(text)
    if not blocks and text:
        blocks = [l.strip() for l in text.splitlines() if l.strip()]

    for blk in blocks:
        blk_norm = _clean_bullet_prefix(blk)
        if not blk_norm:
            continue
        appts.append(Appointment(
            id=str(uuid.uuid4()),
            type=blk_norm,
            status="pending"
        ))
    return appts


def parse_pdf(file_path: str, patient_id: str) -> CarePlanCreate:
    """Parse PDF and return a CarePlanCreate object ready for Mongo insertion."""
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
    full_text = "\n".join(pages_text)
    meds_text = _find_section(full_text, "Medications", ["Appointments", "Notes", "Care Plan", "Medical History"])
    appt_text = _find_section(full_text, "Appointments", ["Medications", "Notes", "Care Plan", "Medical History"])
    history_text = _find_section(full_text, "Medical History", ["Medications", "Appointments", "Notes", "Care Plan"])

    medications = parse_medications_section(meds_text) if meds_text else []
    appointments = parse_appointments_section(appt_text) if appt_text else []

    return CarePlanCreate(
        patient_id=patient_id,
        medications=medications,
        appointments=appointments,
        medical_history=history_text if history_text else None
    )

