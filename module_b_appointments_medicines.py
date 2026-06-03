# Модуль Б: Назначения и Лекарства (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="МИС - Назначения и Лекарства")

class Medicine(BaseModel):
    id: int
    name: str
    dosage: str
    price: int = 0

class Appointment(BaseModel):
    id: int
    patient_name: str
    doctor_name: str
    diagnosis: str = ""
    medicines: List[int] = []

medicines_db = [
    Medicine(id=1, name="Амоксициллин", dosage="500 мг", price=300),
    Medicine(id=2, name="Парацетамол", dosage="250 мг", price=150),
    Medicine(id=3, name="Нурофен", dosage="200 мг", price=200)
]

appointments_db = [
    Appointment(id=1, patient_name="Иван Петров", doctor_name="Смирнова А.И.", diagnosis="ОРВИ", medicines=[1, 2]),
    Appointment(id=2, patient_name="Мария Сидорова", doctor_name="Кузнецов В.П.", diagnosis="Гипертония", medicines=[3])
]

@app.get("/")
def root():
    return {"message": "МИС Модуль Б - Назначения и Лекарства"}

@app.get("/medicines")
def get_medicines():
    return medicines_db

@app.get("/appointments")
def get_appointments():
    return appointments_db

@app.post("/appointments/create")
def create_appointment(app: Appointment):
    appointments_db.append(app)
    return {"status": "created", "id": app.id, "message": "Назначение создано"}

if __name__ == "__main__":
    print("Модуль Б запущен на http://localhost:5002")
    print("Документация API: http://localhost:5002/docs")
    uvicorn.run(app, port=5002)