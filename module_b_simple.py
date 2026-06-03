from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Clinic MIS - Module B")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Medicine(BaseModel):
    id: int
    name: str
    dosage: str
    price: float

medicines = [
    Medicine(id=1, name="Amoxicillin", dosage="500 mg", price=300),
    Medicine(id=2, name="Paracetamol", dosage="250 mg", price=150),
    Medicine(id=3, name="Nurofen", dosage="200 mg", price=200),
]

@app.get("/")
def root():
    return {"message": "Clinic MIS Module B"}

@app.get("/medicines")
def get_medicines():
    return [m.dict() for m in medicines]

@app.get("/health")
def health():
    return {"status": "ok", "module": "B"}

if __name__ == "__main__":
    print("Module B running on http://0.0.0.0:5002")
    uvicorn.run(app, host="0.0.0.0", port=5002)
