#!/usr/bin/env python3
"""
Запуск оркестратора с проверкой доступности модулей
"""

import sys
import time
import requests
import logging
from orchestrator import ClinicOrchestrator, setup_logging, CompleteOrderRequest

def check_module_health(module_name: str, url: str) -> bool:
    """Проверка доступности модуля"""
    try:
        response = requests.get(url, timeout=3)
        if response.status_code in [200, 404]:  # 404 тоже означает, что сервер отвечает
            print(f"   ✅ {module_name} доступен")
            return True
    except requests.RequestException:
        pass
    print(f"   ❌ {module_name} недоступен")
    return False

def main():
    print("=" * 60)
    print("ЗАПУСК ИНТЕГРАЦИОННОГО ОРКЕСТРАТОРА")
    print("=" * 60)
    
    # Настройка логгирования
    setup_logging(log_level="INFO", log_file="orchestrator.log")
    logger = logging.getLogger(__name__)
    
    # Проверка доступности модулей
    print("\n🔍 Проверка доступности модулей...")
    modules_available = {
        'Модуль А': check_module_health("Модуль А", "http://localhost:5001/health"),
        'Модуль Б': check_module_health("Модуль Б", "http://localhost:5002/medicines"),
        'Модуль В': check_module_health("Модуль В", "http://localhost:3000/health")
    }
    
    # Если модули недоступны, ждём или выходим
    if not any(modules_available.values()):
        print("\n⚠️ Внимание: Модули недоступны!")
        print("   Запустите модули перед использованием оркестратора:")
        print("   - python module_a_licenses_services.py")
        print("   - python module_b_appointments_medicines.py")
        print("   - python module_c_invoices.py")
        
        response = input("\nПродолжить без модулей? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Создаём оркестратор
    try:
        orchestrator = ClinicOrchestrator()
        
        print("\n" + "=" * 60)
        print("МЕНЮ ОРКЕСТРАТОРА")
        print("=" * 60)
        print("1. Получить сводку по клинике")
        print("2. Создать полный заказ")
        print("3. Найти счета пациента")
        print("4. Оплатить счета пациента")
        print("5. Интерактивный режим")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            summary = orchestrator.get_clinic_summary()
            print(f"\n📊 Сводка: {summary}")
            
        elif choice == "2":
            patient = input("Имя пациента: ")
            doctor = input("Имя врача: ")
            diagnosis = input("Диагноз: ")
            
            print("\nДоступные услуги (ID: название):")
            for s in orchestrator.module_a.get_services():
                print(f"   {s['id']}: {s['name']} - {s['price']} руб.")
            
            service_ids = input("ID услуг (через запятую): ")
            service_ids = [int(x.strip()) for x in service_ids.split(",")]
            
            print("\nДоступные лекарства:")
            for m in orchestrator.module_b.get_medicines():
                print(f"   {m['id']}: {m['name']} - {m['price']} руб.")
            
            medicine_ids = input("ID лекарств (через запятую): ")
            medicine_ids = [int(x.strip()) for x in medicine_ids.split(",")]
            
            request = CompleteOrderRequest(
                patient_name=patient,
                doctor_name=doctor,
                diagnosis=diagnosis,
                service_ids=service_ids,
                medicine_ids=medicine_ids
            )
            
            result = orchestrator.create_complete_order(request)
            print(f"\n✅ Результат: {result}")
            
        elif choice == "3":
            patient = input("Имя пациента: ")
            bill = orchestrator.get_patient_bill(patient)
            print(f"\n💰 Счета для {patient}:")
            for inv in bill['invoices']:
                print(f"   #{inv['id']}: {inv['total']} руб. - {inv['status']}")
            print(f"   Итого к оплате: {bill['total_unpaid']} руб.")
            
        elif choice == "4":
            patient = input("Имя пациента: ")
            result = orchestrator.pay_all_invoices(patient)
            print(f"\n✅ Оплачено {result['paid_count']} счетов")
            
        elif choice == "5":
            print("\n🔄 Интерактивный режим...")
            from orchestrator import demo_orchestrator
            demo_orchestrator()
            
        else:
            print("До свидания!")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
