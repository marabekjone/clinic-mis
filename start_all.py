# Скрипт для запуска всех модулей (поочерёдно)
import subprocess
import sys
import os

def run_module(name, command):
    print(f"\n🚀 Запуск {name}...")
    return subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    print("=" * 50)
    print("Запуск МИС (Управление клиникой)")
    print("=" * 50)
    
    processes = []
    
    # Модуль А
    processes.append(run_module("Модуль А (Лицензии/Услуги)", "python module_a_licenses_services.py"))
    
    # Модуль Б
    processes.append(run_module("Модуль Б (Назначения/Лекарства)", "python module_b_appointments_medicines.py"))
    
    # Модуль В
    processes.append(run_module("Модуль В (Счета)", "python module_c_invoices.py"))
    
    print("\n✅ Все модули запущены!")
    print("\nАдреса:")
    print("  Модуль А: http://localhost:5001")
    print("  Модуль Б: http://localhost:5002")
    print("  Модуль В: http://localhost:3000")
    print("\nНажмите Ctrl+C для остановки всех модулей\n")
    
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n🛑 Остановка всех модулей...")
        for p in processes:
            p.terminate()