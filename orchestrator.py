"""
Интеграционный сервис (Оркестратор) для МИС Clinic
Обеспечивает взаимодействие между модулями:
- Модуль А (Лицензии/Услуги)
- Модуль Б (Назначения/Лекарства)
- Модуль В (Счета)

Автор: marabekjone
Дата: 2026-06-03
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================
# 1. DTO (Data Transfer Objects) - Модели данных
# ============================================

@dataclass
class ServiceDto:
    """DTO для услуги из модуля А"""
    id: int
    name: str
    price: float

@dataclass
class MedicineDto:
    """DTO для лекарства из модуля Б"""
    id: int
    name: str
    dosage: str
    price: float

@dataclass
class AppointmentDto:
    """DTO для назначения из модуля Б"""
    id: int
    patient_name: str
    doctor_name: str
    diagnosis: str
    medicines: List[int]

@dataclass
class InvoiceLineDto:
    """DTO для строки счёта"""
    product_id: int
    product_name: str
    product_type: str  # 'service' или 'medicine'
    price: float
    quantity: int

@dataclass
class InvoiceRequestDto:
    """DTO для запроса на создание счёта"""
    patient_name: str
    service_ids: List[int]
    medicine_ids: List[int]
    appointment_id: Optional[int] = None

@dataclass
class InvoiceResponseDto:
    """DTO для ответа после создания счёта"""
    id: int
    patient: str
    total: float
    status: str
    items: List[Dict]
    created_at: str

@dataclass
class CompleteOrderRequest:
    """Полный запрос на создание заказа (сквозной)"""
    patient_name: str
    doctor_name: str
    diagnosis: str
    service_ids: List[int]
    medicine_ids: List[int]

@dataclass
class CompleteOrderResponse:
    """Полный ответ после создания заказа"""
    appointment_id: int
    invoice_id: int
    total_amount: float
    status: str
    message: str


# ============================================
# 2. Маппер (Mapper) - преобразование данных
# ============================================

class DataMapper:
    """Класс для маппинга данных между модулями"""
    
    @staticmethod
    def service_to_invoice_line(service: Dict) -> InvoiceLineDto:
        """Преобразует услугу в строку счёта"""
        return InvoiceLineDto(
            product_id=service['id'],
            product_name=service['name'],
            product_type='service',
            price=float(service['price']),
            quantity=1
        )
    
    @staticmethod
    def medicine_to_invoice_line(medicine: Dict) -> InvoiceLineDto:
        """Преобразует лекарство в строку счёта"""
        return InvoiceLineDto(
            product_id=medicine['id'],
            product_name=medicine['name'],
            product_type='medicine',
            price=float(medicine['price']),
            quantity=1
        )
    
    @staticmethod
    def to_invoice_request(
        patient_name: str,
        services: List[Dict],
        medicines: List[Dict]
    ) -> Dict:
        """Преобразует списки услуг и лекарств в запрос для модуля В"""
        return {
            "patient_name": patient_name,
            "service_ids": [s['id'] for s in services],
            "medicine_ids": [m['id'] for m in medicines]
        }
    
    @staticmethod
    def appointment_to_dict(appointment: AppointmentDto) -> Dict:
        """Преобразует назначение в словарь для API"""
        return {
            "id": appointment.id,
            "patient_name": appointment.patient_name,
            "doctor_name": appointment.doctor_name,
            "diagnosis": appointment.diagnosis,
            "medicines": appointment.medicines
        }


# ============================================
# 3. Адаптеры для каждого модуля
# ============================================

class ModuleAAdapter:
    """Адаптер для модуля А (Лицензии и Услуги)"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
    
    def get_services(self) -> List[Dict]:
        """Получить список всех услуг"""
        try:
            response = requests.get(f"{self.base_url}/services", timeout=5)
            response.raise_for_status()
            services = response.json()
            self.logger.info(f"Получено {len(services)} услуг из модуля А")
            return services
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении услуг: {e}")
            raise
    
    def get_service(self, service_id: int) -> Optional[Dict]:
        """Получить услугу по ID"""
        try:
            response = requests.get(f"{self.base_url}/services/{service_id}", timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Получена услуга {service_id}")
                return response.json()
            return None
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении услуги {service_id}: {e}")
            return None
    
    def get_licenses(self) -> List[Dict]:
        """Получить список лицензий"""
        try:
            response = requests.get(f"{self.base_url}/licenses", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении лицензий: {e}")
            raise


class ModuleBAdapter:
    """Адаптер для модуля Б (Назначения и Лекарства)"""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
    
    def get_medicines(self) -> List[Dict]:
        """Получить список всех лекарств"""
        try:
            response = requests.get(f"{self.base_url}/medicines", timeout=5)
            response.raise_for_status()
            medicines = response.json()
            self.logger.info(f"Получено {len(medicines)} лекарств из модуля Б")
            return medicines
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении лекарств: {e}")
            raise
    
    def get_appointments(self) -> List[Dict]:
        """Получить список назначений"""
        try:
            response = requests.get(f"{self.base_url}/appointments", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении назначений: {e}")
            raise
    
    def create_appointment(self, appointment: AppointmentDto) -> Dict:
        """Создать новое назначение"""
        try:
            payload = DataMapper.appointment_to_dict(appointment)
            response = requests.post(
                f"{self.base_url}/appointments/create",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self.logger.info(f"Создано назначение для пациента {appointment.patient_name}")
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при создании назначения: {e}")
            raise


class ModuleCAdapter:
    """Адаптер для модуля В (Счета)"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
    
    def create_invoice(self, request_data: Dict) -> Dict:
        """Создать счёт"""
        try:
            response = requests.post(
                f"{self.base_url}/invoices/create",
                json=request_data,
                timeout=5
            )
            response.raise_for_status()
            invoice = response.json()
            self.logger.info(f"Создан счёт #{invoice['id']} на сумму {invoice['total']} руб.")
            return invoice
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при создании счёта: {e}")
            raise
    
    def get_invoices(self) -> List[Dict]:
        """Получить все счета"""
        try:
            response = requests.get(f"{self.base_url}/invoices", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении счетов: {e}")
            raise
    
    def pay_invoice(self, invoice_id: int) -> Dict:
        """Оплатить счёт"""
        try:
            response = requests.post(f"{self.base_url}/invoices/{invoice_id}/pay", timeout=5)
            response.raise_for_status()
            self.logger.info(f"Оплачен счёт #{invoice_id}")
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при оплате счёта {invoice_id}: {e}")
            raise


# ============================================
# 4. Оркестратор (Интеграционный сервис)
# ============================================

class ClinicOrchestrator:
    """
    Оркестратор для управления клиникой
    Обеспечивает сквозные бизнес-процессы
    """
    
    def __init__(
        self,
        module_a_url: str = "http://localhost:5001",
        module_b_url: str = "http://localhost:5002",
        module_c_url: str = "http://localhost:3000"
    ):
        self.module_a = ModuleAAdapter(module_a_url)
        self.module_b = ModuleBAdapter(module_b_url)
        self.module_c = ModuleCAdapter(module_c_url)
        self.mapper = DataMapper()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Оркестратор инициализирован")
        self.logger.info(f"Модуль А: {module_a_url}")
        self.logger.info(f"Модуль Б: {module_b_url}")
        self.logger.info(f"Модуль В: {module_c_url}")
    
    def create_complete_order(self, request: CompleteOrderRequest) -> CompleteOrderResponse:
        """
        Сквозной процесс: создание полного заказа
        Шаги:
        1. Получаем услуги из модуля А
        2. Получаем лекарства из модуля Б
        3. Создаём назначение в модуле Б
        4. Создаём счёт в модуле В
        """
        self.logger.info(f"=== Начало создания заказа для пациента {request.patient_name} ===")
        
        # Шаг 1: Получаем услуги
        self.logger.info("Шаг 1: Получение услуг из модуля А...")
        all_services = self.module_a.get_services()
        selected_services = [s for s in all_services if s['id'] in request.service_ids]
        self.logger.info(f"Выбрано {len(selected_services)} услуг")
        
        # Шаг 2: Получаем лекарства
        self.logger.info("Шаг 2: Получение лекарств из модуля Б...")
        all_medicines = self.module_b.get_medicines()
        selected_medicines = [m for m in all_medicines if m['id'] in request.medicine_ids]
        self.logger.info(f"Выбрано {len(selected_medicines)} лекарств")
        
        # Шаг 3: Создаём назначение
        self.logger.info("Шаг 3: Создание назначения в модуле Б...")
        appointment = AppointmentDto(
            id=0,  # Будет присвоен автоматически
            patient_name=request.patient_name,
            doctor_name=request.doctor_name,
            diagnosis=request.diagnosis,
            medicines=request.medicine_ids
        )
        appointment_result = self.module_b.create_appointment(appointment)
        self.logger.info(f"Назначение создано: {appointment_result}")
        
        # Шаг 4: Создаём счёт
        self.logger.info("Шаг 4: Создание счёта в модуле В...")
        invoice_request = self.mapper.to_invoice_request(
            request.patient_name,
            selected_services,
            selected_medicines
        )
        invoice = self.module_c.create_invoice(invoice_request)
        self.logger.info(f"Счёт создан: #{invoice['id']}, сумма: {invoice['total']} руб.")
        
        # Подсчёт общей суммы
        total = sum(s['price'] for s in selected_services) + sum(m['price'] for m in selected_medicines)
        
        self.logger.info(f"=== Заказ для {request.patient_name} успешно создан ===")
        
        return CompleteOrderResponse(
            appointment_id=appointment_result.get('id', 0),
            invoice_id=invoice['id'],
            total_amount=total,
            status='completed',
            message='Заказ успешно создан'
        )
    
    def get_patient_bill(self, patient_name: str) -> Dict:
        """Получить счёт для пациента"""
        self.logger.info(f"Поиск счетов для пациента {patient_name}")
        
        invoices = self.module_c.get_invoices()
        patient_invoices = [i for i in invoices if i.get('patient') == patient_name]
        
        total_unpaid = sum(i['total'] for i in patient_invoices if i.get('status') == 'не оплачен')
        
        return {
            'patient': patient_name,
            'invoices': patient_invoices,
            'total_unpaid': total_unpaid,
            'invoices_count': len(patient_invoices)
        }
    
    def pay_all_invoices(self, patient_name: str) -> Dict:
        """Оплатить все счета пациента"""
        self.logger.info(f"Оплата всех счетов для {patient_name}")
        
        invoices = self.module_c.get_invoices()
        patient_invoices = [i for i in invoices if i.get('patient') == patient_name and i.get('status') == 'не оплачен']
        
        paid_invoices = []
        for inv in patient_invoices:
            result = self.module_c.pay_invoice(inv['id'])
            paid_invoices.append(result)
        
        return {
            'patient': patient_name,
            'paid_count': len(paid_invoices),
            'paid_invoices': paid_invoices
        }
    
    def get_clinic_summary(self) -> Dict:
        """Получить сводку по клинике"""
        self.logger.info("Получение сводки по клинике")
        
        services = self.module_a.get_services()
        medicines = self.module_b.get_medicines()
        appointments = self.module_b.get_appointments()
        invoices = self.module_c.get_invoices()
        
        total_revenue = sum(i['total'] for i in invoices if i.get('status') == 'оплачен')
        total_unpaid = sum(i['total'] for i in invoices if i.get('status') == 'не оплачен')
        
        return {
            'statistics': {
                'total_services': len(services),
                'total_medicines': len(medicines),
                'total_appointments': len(appointments),
                'total_invoices': len(invoices),
                'total_revenue': total_revenue,
                'total_unpaid': total_unpaid
            },
            'timestamp': datetime.now().isoformat()
        }


# ============================================
# 5. Настройка логгирования (Serilog-style)
# ============================================

def setup_logging(log_level: str = "INFO", log_file: str = "orchestrator.log"):
    """Настройка логгирования в стиле Serilog"""
    
    # Создаём форматтер с детальной информацией
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик (цветной)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Файловый обработчик (для сохранения логов)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Отдельный логгер для оркестратора
    orchestrator_logger = logging.getLogger(__name__)
    orchestrator_logger.info("Логгирование настроено")
    
    return orchestrator_logger


# ============================================
# 6. Пример использования и тестирование
# ============================================

def demo_orchestrator():
    """Демонстрация работы оркестратора"""
    
    print("=" * 70)
    print("ИНТЕГРАЦИОННЫЙ СЕРВИС (ОРКЕСТРАТОР) - ДЕМОНСТРАЦИЯ")
    print("=" * 70)
    
    # Настройка логгирования
    setup_logging(log_level="INFO", log_file="logs/orchestrator.log")
    logger = logging.getLogger(__name__)
    
    try:
        # Создаём оркестратор
        orchestrator = ClinicOrchestrator()
        
        print("\n📋 Получение сводки по клинике...")
        summary = orchestrator.get_clinic_summary()
        print(f"   Статистика: {json.dumps(summary['statistics'], indent=2, ensure_ascii=False)}")
        
        print("\n🔄 Создание полного заказа...")
        order_request = CompleteOrderRequest(
            patient_name="Тестовый Пациент",
            doctor_name="Иванов А.И.",
            diagnosis="Плановый осмотр",
            service_ids=[1, 2],  # Приём терапевта + УЗИ
            medicine_ids=[1, 2]   # Амоксициллин + Парацетамол
        )
        
        result = orchestrator.create_complete_order(order_request)
        print(f"   Результат: {json.dumps(asdict(result), indent=2, ensure_ascii=False)}")
        
        print("\n💰 Проверка счетов пациента...")
        bill = orchestrator.get_patient_bill("Тестовый Пациент")
        print(f"   Счета: {json.dumps(bill, indent=2, ensure_ascii=False)}")
        
        print("\n✅ Оплата всех счетов...")
        payment_result = orchestrator.pay_all_invoices("Тестовый Пациент")
        print(f"   Оплачено: {payment_result['paid_count']} счетов")
        
        print("\n📊 Итоговая сводка...")
        final_summary = orchestrator.get_clinic_summary()
        print(f"   Выручка: {final_summary['statistics']['total_revenue']} руб.")
        
        print("\n" + "=" * 70)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Ошибка в демонстрации: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("Убедитесь, что все модули запущены!")


if __name__ == "__main__":
    demo_orchestrator()
