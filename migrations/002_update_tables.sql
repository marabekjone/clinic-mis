-- ============================================
-- Миграция 002: Добавление новых полей и индексов
-- Дата: 2026-06-03
-- ============================================

USE clinic_db;
GO

-- Добавляем поле Email в Doctors
IF NOT EXISTS (SELECT * FROM sys.columns WHERE name = 'Email' AND object_id = OBJECT_ID('Doctors'))
BEGIN
    ALTER TABLE Doctors ADD Email NVARCHAR(100) NULL;
END
GO

-- Добавляем поле Description в Services
IF NOT EXISTS (SELECT * FROM sys.columns WHERE name = 'Description' AND object_id = OBJECT_ID('Services'))
BEGIN
    ALTER TABLE Services ADD Description NVARCHAR(500) NULL;
END
GO

-- Триггер для автоматического обновления UpdatedAt
CREATE OR ALTER TRIGGER trg_Services_UpdateTimestamp
ON Services
AFTER UPDATE
AS
BEGIN
    UPDATE Services
    SET UpdatedAt = GETDATE()
    FROM Services s
    INNER JOIN inserted i ON s.Id = i.Id
END
GO

PRINT 'Миграция 002 выполнена успешно!';
GO
