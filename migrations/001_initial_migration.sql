-- ============================================
-- Миграция 001: Начальная схема базы данных
-- Дата: 2026-06-03
-- Проект: МИС Клиника (Clinic MIS)
-- ============================================

USE clinic_db;
GO

-- 1. Таблица лицензий
CREATE TABLE IF NOT EXISTS Licenses (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Status NVARCHAR(50) DEFAULT 'активна',
    LicenseNumber NVARCHAR(100) NOT NULL UNIQUE,
    IssueDate DATE NOT NULL,
    ExpiryDate DATE NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- 2. Таблица услуг
CREATE TABLE IF NOT EXISTS Services (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Category NVARCHAR(100),
    DurationMinutes INT DEFAULT 30,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- 3. Таблица лекарств
CREATE TABLE IF NOT EXISTS Medicines (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Dosage NVARCHAR(100) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    StockQuantity INT DEFAULT 0,
    RequiresPrescription BIT DEFAULT 1,
    Manufacturer NVARCHAR(200),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- 4. Таблица пациентов
CREATE TABLE IF NOT EXISTS Patients (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    Phone NVARCHAR(20),
    Email NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- 5. Таблица врачей
CREATE TABLE IF NOT EXISTS Doctors (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    Specialization NVARCHAR(200),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- 6. Таблица назначений
CREATE TABLE IF NOT EXISTS Appointments (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    PatientId INT NOT NULL,
    DoctorId INT NOT NULL,
    ServiceId INT,
    AppointmentDate DATETIME2 NOT NULL,
    Diagnosis NVARCHAR(500),
    Status NVARCHAR(50) DEFAULT 'назначен',
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (PatientId) REFERENCES Patients(Id),
    FOREIGN KEY (DoctorId) REFERENCES Doctors(Id),
    FOREIGN KEY (ServiceId) REFERENCES Services(Id)
);
GO

-- 7. Таблица назначенных лекарств
CREATE TABLE IF NOT EXISTS AppointmentMedicines (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    AppointmentId INT NOT NULL,
    MedicineId INT NOT NULL,
    Quantity INT DEFAULT 1,
    FOREIGN KEY (AppointmentId) REFERENCES Appointments(Id) ON DELETE CASCADE,
    FOREIGN KEY (MedicineId) REFERENCES Medicines(Id)
);
GO

-- 8. Таблица счетов
CREATE TABLE IF NOT EXISTS Invoices (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    PatientId INT NOT NULL,
    AppointmentId INT,
    InvoiceNumber NVARCHAR(50) NOT NULL UNIQUE,
    TotalAmount DECIMAL(10,2) NOT NULL,
    Status NVARCHAR(50) DEFAULT 'не оплачен',
    PaymentDate DATETIME2,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (PatientId) REFERENCES Patients(Id),
    FOREIGN KEY (AppointmentId) REFERENCES Appointments(Id)
);
GO

-- 9. Таблица строк счетов
CREATE TABLE IF NOT EXISTS InvoiceItems (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceId INT NOT NULL,
    ItemType NVARCHAR(50) NOT NULL,
    ItemId INT NOT NULL,
    ItemName NVARCHAR(200) NOT NULL,
    Quantity INT DEFAULT 1,
    UnitPrice DECIMAL(10,2) NOT NULL,
    TotalPrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (InvoiceId) REFERENCES Invoices(Id) ON DELETE CASCADE
);
GO

-- Индексы
CREATE INDEX idx_appointments_patient ON Appointments(PatientId);
CREATE INDEX idx_appointments_doctor ON Appointments(DoctorId);
CREATE INDEX idx_invoices_patient ON Invoices(PatientId);
CREATE INDEX idx_invoices_status ON Invoices(Status);
GO

-- Начальные данные
INSERT INTO Services (Name, Price, Category, DurationMinutes) VALUES
('Приём терапевта', 1500.00, 'Консультация', 30),
('УЗИ', 2500.00, 'Диагностика', 45),
('Анализ крови', 800.00, 'Лаборатория', 15);
GO

INSERT INTO Medicines (Name, Dosage, Price, StockQuantity) VALUES
('Амоксициллин', '500 мг', 300.00, 100),
('Парацетамол', '250 мг', 150.00, 200);
GO

INSERT INTO Doctors (FirstName, LastName, Specialization) VALUES
('Анна', 'Смирнова', 'Терапевт'),
('Иван', 'Кузнецов', 'Кардиолог');
GO

PRINT 'Миграция 001 выполнена успешно!';
GO
