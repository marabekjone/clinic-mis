#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stage 7: End-to-End Business Process - Order Management
With Saga Pattern for distributed transactions
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

# ============================================
# State Machine for Order
# ============================================

class OrderState(Enum):
    NEW = "NEW"
    VALIDATING = "VALIDATING"
    RESERVING_STOCK = "RESERVING_STOCK"
    STOCK_RESERVED = "STOCK_RESERVED"
    CREATING_INVOICE = "CREATING_INVOICE"
    INVOICE_CREATED = "INVOICE_CREATED"
    PROCESSING_PAYMENT = "PROCESSING_PAYMENT"
    PAID = "PAID"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPENSATING = "COMPENSATING"

# ============================================
# Stock Service (Inventory check)
# ============================================

class StockService:
    def __init__(self):
        self.stock = {1: 100, 2: 200, 3: 50}
        self.reserved = {}
        self.logger = logging.getLogger(__name__)
    
    def check_stock(self, items: List[Dict]) -> tuple:
        self.logger.info(f"Checking stock for items: {items}")
        
        required = {}
        for item in items:
            item_id = item['id']
            qty = item.get('quantity', 1)
            required[item_id] = required.get(item_id, 0) + qty
        
        available = True
        shortages = []
        
        for item_id, qty in required.items():
            if item_id in self.stock:
                if self.stock[item_id] >= qty:
                    self.logger.info(f"Item {item_id}: OK")
                else:
                    available = False
                    shortages.append({'item_id': item_id, 'available': self.stock[item_id], 'required': qty})
            else:
                available = False
                shortages.append({'item_id': item_id, 'available': 0, 'required': qty})
        
        return available, {'required': required, 'shortages': shortages}
    
    def reserve_stock(self, items: List[Dict], transaction_id: str) -> bool:
        self.logger.info(f"Reserving stock for transaction {transaction_id}")
        
        available, _ = self.check_stock(items)
        if not available:
            return False
        
        if transaction_id not in self.reserved:
            self.reserved[transaction_id] = []
        
        for item in items:
            item_id = item['id']
            qty = item.get('quantity', 1)
            self.stock[item_id] -= qty
            self.reserved[transaction_id].append({'item_id': item_id, 'quantity': qty})
            self.logger.info(f"Reserved {qty} of item {item_id}. Remaining: {self.stock[item_id]}")
        
        return True
    
    def release_stock(self, transaction_id: str):
        self.logger.info(f"Releasing stock for transaction {transaction_id}")
        
        if transaction_id in self.reserved:
            for item in self.reserved[transaction_id]:
                self.stock[item['item_id']] += item['quantity']
                self.logger.info(f"Released {item['quantity']} of item {item['item_id']}")
            del self.reserved[transaction_id]


# ============================================
# Payment Service
# ============================================

class PaymentService:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.processed = []
        self.logger = logging.getLogger(__name__)
    
    def process_payment(self, amount: float, order_id: int) -> tuple:
        self.logger.info(f"Processing payment of ${amount} for order {order_id}")
        time.sleep(0.5)
        
        if self.should_fail or amount > 10000:
            self.logger.error(f"Payment failed for order {order_id}")
            return False, "Insufficient funds"
        
        self.logger.info(f"Payment successful for order {order_id}")
        self.processed.append({'order_id': order_id, 'amount': amount, 'timestamp': datetime.now()})
        return True, "Payment approved"
    
    def refund_payment(self, order_id: int, amount: float) -> bool:
        self.logger.info(f"Refunding ${amount} for order {order_id}")
        self.processed = [p for p in self.processed if p['order_id'] != order_id]
        return True


# ============================================
# Invoice Service
# ============================================

class InvoiceService:
    def __init__(self):
        self.invoices = {}
        self.next_id = 1
        self.logger = logging.getLogger(__name__)
    
    def create_invoice(self, order_data: Dict) -> Dict:
        self.logger.info(f"Creating invoice for order: {order_data['order_id']}")
        
        invoice = {
            'invoice_id': self.next_id,
            'order_id': order_data['order_id'],
            'patient_name': order_data['patient_name'],
            'amount': order_data['total_amount'],
            'items': order_data['items'],
            'status': 'unpaid',
            'created_at': datetime.now()
        }
        
        self.invoices[self.next_id] = invoice
        self.next_id += 1
        self.logger.info(f"Invoice created with ID: {invoice['invoice_id']}")
        return invoice
    
    def mark_as_paid(self, invoice_id: int) -> bool:
        if invoice_id in self.invoices:
            self.invoices[invoice_id]['status'] = 'paid'
            self.logger.info(f"Invoice {invoice_id} marked as paid")
            return True
        return False


# ============================================
# Order State Machine
# ============================================

class OrderStateMachine:
    def __init__(self, order_id: int, data: Dict):
        self.order_id = order_id
        self.data = data
        self.state = OrderState.NEW
        self.history = []
        self.compensation_actions = []
        self.logger = logging.getLogger(__name__)
        
        self.stock_service = StockService()
        self.payment_service = PaymentService()
        self.invoice_service = InvoiceService()
        
        self._log_state_change(None, self.state)
    
    def _log_state_change(self, from_state, to_state):
        self.history.append({
            'timestamp': datetime.now(),
            'from': from_state.value if from_state else None,
            'to': to_state.value,
            'order_id': self.order_id
        })
    
    def _transition(self, new_state: OrderState):
        self._log_state_change(self.state, new_state)
        self.state = new_state
        self.logger.info(f"Order {self.order_id} transitioned to {new_state.value}")
    
    def _add_compensation(self, action: str, params: Dict):
        self.compensation_actions.append({'action': action, 'params': params})
    
    def _compensate(self) -> Dict:
        self.logger.warning(f"Starting compensation for order {self.order_id}")
        self._transition(OrderState.COMPENSATING)
        
        for action in reversed(self.compensation_actions):
            self.logger.info(f"Executing compensation: {action['action']}")
            if action['action'] == 'release_stock':
                self.stock_service.release_stock(action['params']['transaction_id'])
            elif action['action'] == 'refund_payment':
                self.payment_service.refund_payment(action['params']['order_id'], action['params']['amount'])
        
        self._transition(OrderState.CANCELLED)
        return {"success": False, "state": self.state.value, "message": "Order cancelled due to failure"}
    
    def _validate_order(self) -> bool:
        required_fields = ['patient_name', 'items', 'total_amount']
        for field in required_fields:
            if field not in self.data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        if not self.data['items']:
            self.logger.error("No items in order")
            return False
        
        if self.data['total_amount'] <= 0:
            self.logger.error(f"Invalid amount: {self.data['total_amount']}")
            return False
        
        self.logger.info(f"Order {self.order_id} validated successfully")
        return True
    
    def _handle_failure(self, error_message: str) -> Dict:
        self.logger.error(f"Order {self.order_id} failed: {error_message}")
        self._transition(OrderState.FAILED)
        return self._compensate()
    
    def process(self) -> Dict:
        # Step 1: Validate
        self._transition(OrderState.VALIDATING)
        if not self._validate_order():
            return self._handle_failure("Order validation failed")
        
        # Step 2: Reserve stock
        self._transition(OrderState.RESERVING_STOCK)
        transaction_id = f"txn_{self.order_id}_{int(time.time())}"
        
        available, stock_info = self.stock_service.check_stock(self.data['items'])
        if not available:
            return self._handle_failure(f"Stock insufficient: {stock_info['shortages']}")
        
        stock_reserved = self.stock_service.reserve_stock(self.data['items'], transaction_id)
        if not stock_reserved:
            return self._handle_failure("Failed to reserve stock")
        
        self._add_compensation('release_stock', {'transaction_id': transaction_id})
        self._transition(OrderState.STOCK_RESERVED)
        
        # Step 3: Create invoice
        self._transition(OrderState.CREATING_INVOICE)
        invoice = self.invoice_service.create_invoice({
            'order_id': self.order_id,
            'patient_name': self.data['patient_name'],
            'total_amount': self.data['total_amount'],
            'items': self.data['items']
        })
        
        if not invoice:
            return self._handle_failure("Failed to create invoice")
        
        self._transition(OrderState.INVOICE_CREATED)
        
        # Step 4: Process payment
        self._transition(OrderState.PROCESSING_PAYMENT)
        payment_success, payment_message = self.payment_service.process_payment(
            self.data['total_amount'], self.order_id
        )
        
        if not payment_success:
            self._add_compensation('refund_payment', {
                'order_id': self.order_id,
                'amount': self.data['total_amount']
            })
            return self._handle_failure(f"Payment failed: {payment_message}")
        
        self._transition(OrderState.PAID)
        
        # Step 5: Mark invoice as paid
        self.invoice_service.mark_as_paid(invoice['invoice_id'])
        
        # Step 6: Complete
        self._transition(OrderState.COMPLETED)
        
        return {
            "success": True,
            "order_id": self.order_id,
            "state": self.state.value,
            "invoice_id": invoice['invoice_id'],
            "total_amount": self.data['total_amount'],
            "message": "Order completed successfully"
        }
    
    def get_state_history(self) -> List[Dict]:
        return self.history


# ============================================
# Order Orchestrator
# ============================================

class OrderOrchestrator:
    def __init__(self):
        self.orders = {}
        self.next_order_id = 1
        self.logger = logging.getLogger(__name__)
    
    def create_order(self, patient_name: str, items: List[Dict]) -> Dict:
        total = sum(item['price'] * item.get('quantity', 1) for item in items)
        
        order_data = {
            'patient_name': patient_name,
            'items': items,
            'total_amount': total,
            'created_at': datetime.now()
        }
        
        order_id = self.next_order_id
        self.next_order_id += 1
        
        self.logger.info(f"Creating new order {order_id} for patient {patient_name}")
        self.logger.info(f"Total amount: ${total}")
        
        sm = OrderStateMachine(order_id, order_data)
        result = sm.process()
        
        self.orders[order_id] = {
            'data': order_data,
            'result': result,
            'history': sm.get_state_history()
        }
        
        return result


# ============================================
# Logging setup
# ============================================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    file_handler = logging.FileHandler('e2e_process.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
    logging.getLogger().addHandler(file_handler)
    return logging.getLogger(__name__)


# ============================================
# Demo execution
# ============================================

def demo_successful_order():
    print("\n" + "="*60)
    print("DEMO 1: SUCCESSFUL ORDER")
    print("="*60)
    
    orchestrator = OrderOrchestrator()
    
    items = [
        {'id': 1, 'name': 'Amoxicillin', 'price': 300, 'quantity': 2},
        {'id': 2, 'name': 'Paracetamol', 'price': 150, 'quantity': 1},
        {'id': 3, 'name': 'Consultation', 'price': 1500, 'quantity': 1}
    ]
    
    result = orchestrator.create_order("Ivan Petrov", items)
    
    print(f"\nRESULT:")
    print(f"  Success: {result['success']}")
    print(f"  Order ID: {result['order_id']}")
    print(f"  State: {result['state']}")
    print(f"  Invoice ID: {result.get('invoice_id', 'N/A')}")
    print(f"  Total: ${result['total_amount']}")
    print(f"  Message: {result['message']}")


def demo_failed_order_stock():
    print("\n" + "="*60)
    print("DEMO 2: FAILED ORDER - INSUFFICIENT STOCK")
    print("="*60)
    
    orchestrator = OrderOrchestrator()
    
    items = [{'id': 1, 'name': 'Amoxicillin', 'price': 300, 'quantity': 200}]
    result = orchestrator.create_order("Petr Ivanov", items)
    
    print(f"\nRESULT:")
    print(f"  Success: {result['success']}")
    print(f"  State: {result['state']}")
    print(f"  Message: {result['message']}")


def demo_failed_order_payment():
    print("\n" + "="*60)
    print("DEMO 3: FAILED ORDER - PAYMENT FAILED (WITH COMPENSATION)")
    print("="*60)
    
    order_data = {
        'patient_name': "Payment Test",
        'items': [{'id': 1, 'name': 'Amoxicillin', 'price': 300, 'quantity': 1}],
        'total_amount': 15000
    }
    
    sm = OrderStateMachine(999, order_data)
    sm.payment_service.should_fail = True
    
    result = sm.process()
    
    print(f"\nRESULT:")
    print(f"  Success: {result['success']}")
    print(f"  State: {result['state']}")
    print(f"  Message: {result['message']}")
    
    print(f"\nCOMPENSATION ACTIONS EXECUTED:")
    for action in sm.compensation_actions:
        print(f"  - {action['action']}")


def show_diagram():
    print("""
================================================================================
                    STATE MACHINE DIAGRAM - ORDER PROCESS
================================================================================

    START --> NEW --> VALIDATING
                          |
            +-------------+-------------+
            |                           |
            v                           v
    VALIDATION_SUCCESS           VALIDATION_FAILED
            |                           |
            v                           v
    RESERVING_STOCK                  FAILED
            |                           |
            v                           |
    STOCK_RESERVED                      |
            |                           |
            v                           |
    CREATING_INVOICE                    |
            |                           |
            v                           |
    INVOICE_CREATED                     |
            |                           |
            v                           |
    PROCESSING_PAYMENT                  |
            |                           |
    +-------+-------+                   |
    |               |                   |
    v               v                   |
   PAID       PAYMENT_FAILED            |
    |               |                   |
    v               v                   |
 COMPLETED      COMPENSATING            |
                    |                   |
                    v                   |
                CANCELLED <-------------+
                    |
                    v
                   END

================================================================================
SAGA COMPENSATION PATTERN:
================================================================================
  If step fails: execute reverse actions:
    1. FAILED at STOCK_RESERVED  -> release_stock
    2. FAILED at INVOICE_CREATED -> release_stock
    3. FAILED at PAYMENT_FAILED  -> release_stock + refund_payment
================================================================================
""")


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    setup_logging()
    
    print("\n" + "="*60)
    print("STAGE 7: E2E BUSINESS PROCESS WITH SAGA PATTERN")
    print("="*60)
    
    show_diagram()
    
    demo_successful_order()
    demo_failed_order_stock()
    demo_failed_order_payment()
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("Check e2e_process.log for details")
    print("="*60)
