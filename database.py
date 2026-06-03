import pyodbc
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost,1433',
    'database': 'clinic_db',
    'uid': 'sa',
    'pwd': 'MyPass123'
}

def get_connection_string() -> str:
    return f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['uid']};PWD={DB_CONFIG['pwd']}"

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pyodbc.connect(get_connection_string(), timeout=10)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

class ServiceRepository:
    @staticmethod
    def get_all() -> List[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Price, Category FROM Services")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'Id': row[0],
                    'Name': row[1],
                    'Price': float(row[2]),
                    'Category': row[3] if row[3] else ''
                })
            return result
    
    @staticmethod
    def get_by_id(service_id: int) -> Optional[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Price, Category FROM Services WHERE Id = ?", (service_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'Id': row[0],
                    'Name': row[1],
                    'Price': float(row[2]),
                    'Category': row[3] if row[3] else ''
                }
            return None

class LicenseRepository:
    @staticmethod
    def get_all() -> List[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Status, LicenseNumber FROM Licenses")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'Id': row[0],
                    'Name': row[1],
                    'Status': row[2] if row[2] else 'active',
                    'LicenseNumber': row[3] if row[3] else ''
                })
            return result

class MedicineRepository:
    @staticmethod
    def get_all() -> List[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name, Dosage, Price FROM Medicines")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'Id': row[0],
                    'Name': row[1],
                    'Dosage': row[2] if row[2] else '',
                    'Price': float(row[3])
                })
            return result

class PatientRepository:
    @staticmethod
    def get_or_create(first_name: str, last_name: str) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id FROM Patients WHERE FirstName = ? AND LastName = ?", (first_name, last_name))
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute(
                "INSERT INTO Patients (FirstName, LastName) OUTPUT INSERTED.Id VALUES (?, ?)",
                (first_name, last_name)
            )
            return cursor.fetchone()[0]

class InvoiceRepository:
    @staticmethod
    def create(patient_id: int, total_amount: float) -> int:
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Invoices (PatientId, InvoiceNumber, TotalAmount) OUTPUT INSERTED.Id VALUES (?, ?, ?)",
                (patient_id, invoice_number, total_amount)
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def add_item(invoice_id: int, item_type: str, item_id: int, item_name: str, price: float):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO InvoiceItems (InvoiceId, ItemType, ItemId, ItemName, UnitPrice, TotalPrice) VALUES (?, ?, ?, ?, ?, ?)",
                (invoice_id, item_type, item_id, item_name, price, price)
            )
    
    @staticmethod
    def get_all() -> List[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.Id, i.InvoiceNumber, p.FirstName + ' ' + p.LastName as PatientName,
                       i.TotalAmount, i.Status, i.CreatedAt
                FROM Invoices i
                JOIN Patients p ON i.PatientId = p.Id
            """)
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'Id': row[0],
                    'InvoiceNumber': row[1],
                    'PatientName': row[2],
                    'TotalAmount': float(row[3]),
                    'Status': row[4],
                    'CreatedAt': str(row[5]) if row[5] else ''
                })
            return result
    
    @staticmethod
    def pay(invoice_id: int):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Invoices SET Status = 'paid', PaymentDate = GETDATE() WHERE Id = ?",
                (invoice_id,)
            )

def init_database():
    logger.info("Initializing database...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'Services')
                CREATE TABLE Services (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Name NVARCHAR(200) NOT NULL,
                    Price DECIMAL(10,2) NOT NULL,
                    Category NVARCHAR(100)
                )
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'Licenses')
                CREATE TABLE Licenses (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Name NVARCHAR(200) NOT NULL,
                    Status NVARCHAR(50),
                    LicenseNumber NVARCHAR(100)
                )
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'Medicines')
                CREATE TABLE Medicines (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Name NVARCHAR(200) NOT NULL,
                    Dosage NVARCHAR(100),
                    Price DECIMAL(10,2) NOT NULL
                )
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'Patients')
                CREATE TABLE Patients (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    FirstName NVARCHAR(100) NOT NULL,
                    LastName NVARCHAR(100) NOT NULL,
                    Phone NVARCHAR(20)
                )
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'Invoices')
                CREATE TABLE Invoices (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    PatientId INT NOT NULL,
                    InvoiceNumber NVARCHAR(50) NOT NULL UNIQUE,
                    TotalAmount DECIMAL(10,2) NOT NULL,
                    Status NVARCHAR(50) DEFAULT 'unpaid',
                    PaymentDate DATETIME2,
                    CreatedAt DATETIME2 DEFAULT GETDATE(),
                    FOREIGN KEY (PatientId) REFERENCES Patients(Id)
                )
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'InvoiceItems')
                CREATE TABLE InvoiceItems (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    InvoiceId INT NOT NULL,
                    ItemType NVARCHAR(50) NOT NULL,
                    ItemId INT NOT NULL,
                    ItemName NVARCHAR(200) NOT NULL,
                    Quantity INT DEFAULT 1,
                    UnitPrice DECIMAL(10,2) NOT NULL,
                    TotalPrice DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (InvoiceId) REFERENCES Invoices(Id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("SELECT COUNT(*) FROM Services")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO Services (Name, Price, Category) VALUES ('Therapist Consultation', 1500, 'Consultation')")
                cursor.execute("INSERT INTO Services (Name, Price, Category) VALUES ('Ultrasound', 2500, 'Diagnostics')")
                cursor.execute("INSERT INTO Services (Name, Price, Category) VALUES ('Blood Test', 800, 'Laboratory')")
                cursor.execute("INSERT INTO Medicines (Name, Dosage, Price) VALUES ('Amoxicillin', '500 mg', 300)")
                cursor.execute("INSERT INTO Medicines (Name, Dosage, Price) VALUES ('Paracetamol', '250 mg', 150)")
                cursor.execute("INSERT INTO Patients (FirstName, LastName) VALUES ('Test', 'Patient')")
                logger.info("Initial data added")
        
        logger.info("Database ready")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    init_database()
    print("Database ready!")
