#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stage 9: Logging, Monitoring and Error Handling
- Structured logging (JSON format)
- Retry pattern with exponential backoff
- Circuit Breaker pattern
- File + Console logging
"""

import json
import logging
import logging.handlers
import time
import random
from datetime import datetime
from functools import wraps
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import threading

# ============================================
# Structured Logging (JSON format)
# ============================================

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'order_id'):
            log_entry["order_id"] = record.order_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'service_name'):
            log_entry["service_name"] = record.service_name
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", log_to_file: bool = True):
    """Setup structured logging with console and file output"""
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler (JSON format)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/clinic_mis.log',
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(JsonFormatter())
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    # Separate error log file
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    logger.addHandler(error_handler)
    
    return logger


# ============================================
# Retry Pattern with Exponential Backoff
# ============================================

class RetryPolicy:
    """Retry pattern with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, 
                 backoff_factor: float = 2.0, retry_on_exceptions: tuple = (Exception,)):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.retry_on_exceptions = retry_on_exceptions
        self.logger = logging.getLogger(__name__)
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Log attempt
                self.logger.info(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} for {func.__name__}",
                    extra={'service_name': func.__name__}
                )
                
                result = func(*args, **kwargs)
                
                # Success
                self.logger.info(
                    f"Success on attempt {attempt + 1} for {func.__name__}",
                    extra={'service_name': func.__name__}
                )
                return result
                
            except self.retry_on_exceptions as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}",
                    extra={'service_name': func.__name__, 'attempt': attempt + 1}
                )
                
                if attempt == self.max_retries:
                    self.logger.error(
                        f"All {self.max_retries + 1} attempts failed for {func.__name__}",
                        extra={'service_name': func.__name__}
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = self.initial_delay * (self.backoff_factor ** attempt)
                self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
        
        raise last_exception


def retry(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator for retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            policy = RetryPolicy(max_retries, initial_delay, backoff_factor)
            return policy.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# Circuit Breaker Pattern
# ============================================

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, requests blocked
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """Circuit Breaker pattern to prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0,
                 half_open_max_calls: int = 1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        with self.lock:
            # Check current state
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.logger.info("Circuit breaker transitioning from OPEN to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    wait_time = self.recovery_timeout - (time.time() - self.last_failure_time)
                    self.logger.warning(
                        f"Circuit breaker OPEN - request rejected. Wait {wait_time:.1f}s",
                        extra={'circuit_state': 'OPEN'}
                    )
                    raise Exception(f"Circuit breaker is OPEN. Please wait {wait_time:.1f} seconds")
            
            # Allow call in HALF_OPEN state (limited)
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    self.logger.warning("Circuit breaker HALF_OPEN - request rejected (limit reached)")
                    raise Exception("Circuit breaker is HALF_OPEN - limited calls exceeded")
                self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            
            with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.logger.info("Circuit breaker test call succeeded - transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                else:
                    # Success in CLOSED state - reset failure count
                    self.failure_count = 0
                    self.logger.debug(f"Call succeeded, failure count reset to 0")
            
            return result
            
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                self.logger.warning(
                    f"Call failed. Failure count: {self.failure_count}/{self.failure_threshold}",
                    extra={'failure_count': self.failure_count, 'error': str(e)}
                )
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.logger.error(
                        f"Circuit breaker OPENING after {self.failure_count} failures",
                        extra={'circuit_state': 'OPEN'}
                    )
            
            raise
    
    def get_state(self) -> str:
        return self.state.value
    
    def get_stats(self) -> Dict:
        with self.lock:
            return {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'last_failure_time': self.last_failure_time,
                'recovery_timeout': self.recovery_timeout
            }


# ============================================
# Circuit Breaker Decorator
# ============================================

def circuit_breaker(failure_threshold: int = 3, recovery_timeout: float = 30.0):
    """Decorator for circuit breaker pattern"""
    def decorator(func):
        breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        wrapper.get_breaker_state = breaker.get_state
        wrapper.get_breaker_stats = breaker.get_stats
        return wrapper
    return decorator


# ============================================
# Mock Services for Demonstration
# ============================================

class UnreliablePaymentService:
    """Mock payment service that fails randomly"""
    
    def __init__(self, failure_rate: float = 0.5):
        self.failure_rate = failure_rate
        self.call_count = 0
        self.logger = logging.getLogger(__name__)
    
    @retry(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def process_payment(self, amount: float, order_id: int) -> Dict:
        """Process payment with retry logic"""
        self.call_count += 1
        
        self.logger.info(
            f"Processing payment for order {order_id}, amount: ${amount}",
            extra={'order_id': order_id, 'amount': amount, 'call_count': self.call_count}
        )
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Random failure simulation
        if random.random() < self.failure_rate:
            self.logger.error(
                f"Payment failed for order {order_id}",
                extra={'order_id': order_id, 'reason': 'insufficient_funds'}
            )
            raise Exception(f"Payment failed: insufficient funds for order {order_id}")
        
        self.logger.info(
            f"Payment successful for order {order_id}",
            extra={'order_id': order_id, 'amount': amount}
        )
        return {
            "success": True,
            "transaction_id": f"TXN-{order_id}-{int(time.time())}",
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }


class UnreliableStockService:
    """Mock stock service with circuit breaker"""
    
    def __init__(self):
        self.failure_count = 0
        self.logger = logging.getLogger(__name__)
    
    @circuit_breaker(failure_threshold=2, recovery_timeout=10.0)
    def check_stock(self, product_id: int, quantity: int) -> Dict:
        """Check stock with circuit breaker"""
        self.failure_count += 1
        
        self.logger.info(
            f"Checking stock for product {product_id}, quantity: {quantity}",
            extra={'product_id': product_id, 'quantity': quantity}
        )
        
        # Simulate intermittent failures
        if self.failure_count % 3 == 0:
            self.logger.info(f"Stock available for product {product_id}")
            return {"available": True, "stock": 100}
        else:
            self.logger.error(f"Stock service unavailable for product {product_id}")
            raise Exception("Stock service temporarily unavailable")
    
    def reset(self):
        self.failure_count = 0


# ============================================
# Logging Examples
# ============================================

def demonstrate_logging():
    """Demonstrate structured logging"""
    
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*70)
    print("DEMO 1: STRUCTURED LOGGING")
    print("="*70)
    
    # Success log
    logger.info(
        "Order created successfully",
        extra={'order_id': 12345, 'user_id': 'patient_001'}
    )
    
    # Warning log
    logger.warning(
        "Low stock alert",
        extra={'product_id': 101, 'current_stock': 5, 'threshold': 10}
    )
    
    # Error log with context
    try:
        1 / 0
    except Exception as e:
        logger.error(
            "Division by zero error",
            extra={'order_id': 12345, 'operation': 'calculate_total'},
            exc_info=True
        )
    
    print("Logs written to: logs/clinic_mis.log and logs/errors.log")
    print("Check the files for JSON formatted logs")


# ============================================
# Retry Pattern Demonstration
# ============================================

def demonstrate_retry():
    """Demonstrate retry pattern"""
    
    print("\n" + "="*70)
    print("DEMO 2: RETRY PATTERN WITH EXPONENTIAL BACKOFF")
    print("="*70)
    
    payment_service = UnreliablePaymentService(failure_rate=0.7)  # 70% failure rate
    
    try:
        result = payment_service.process_payment(amount=1500, order_id=1001)
        print(f"✅ Payment successful: {result}")
    except Exception as e:
        print(f"❌ Payment failed after all retries: {e}")
    
    # Show retry timing
    print("\nRetry pattern explanation:")
    print("  Attempt 1: immediate")
    print("  Attempt 2: after 1 second")
    print("  Attempt 3: after 2 seconds")
    print("  Attempt 4: after 4 seconds")


# ============================================
# Circuit Breaker Demonstration
# ============================================

def demonstrate_circuit_breaker():
    """Demonstrate circuit breaker pattern"""
    
    print("\n" + "="*70)
    print("DEMO 3: CIRCUIT BREAKER PATTERN")
    print("="*70)
    
    stock_service = UnreliableStockService()
    
    print("\nMaking calls to stock service...")
    
    for i in range(1, 7):
        try:
            print(f"\nCall #{i}:")
            result = stock_service.check_stock(product_id=101, quantity=5)
            print(f"  ✅ Success: {result}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
        
        # Show circuit breaker state
        if hasattr(stock_service.check_stock, 'get_breaker_stats'):
            stats = stock_service.check_stock.get_breaker_stats()
            print(f"  Circuit state: {stats['state']}")
            print(f"  Failure count: {stats['failure_count']}")


# ============================================
# BPMN Error Handling Diagram
# ============================================

def show_bpmn_diagram():
    """Print BPMN error handling diagram as text"""
    
    diagram = """
================================================================================
                    BPMN DIAGRAM - ERROR HANDLING FLOW
================================================================================

    ┌─────────────┐
    │    START    │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │  Receive    │
    │   Order     │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │  Validate   │
    │   Order     │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │             │
    v             v
┌───────┐    ┌───────────┐
│Valid  │    │ Invalid   │
└───┬───┘    └─────┬─────┘
    │              │
    v              v
┌───────┐    ┌───────────┐
│Check  │    │ Log Error │
│Stock  │    └─────┬─────┘
└───┬───┘          │
    │              v
    v         ┌───────────┐
┌───────┐     │ Notify    │
│Stock  │     │  User     │
│Available?│   └─────┬─────┘
└───┬───┘          │
    │              v
┌───┴───┐     ┌───────────┐
│ Yes   │     │  Cancel   │
└───┬───┘     │  Order    │
    │         └─────┬─────┘
    v              │
┌───────┐          │
│Process│          │
│Payment│          │
└───┬───┘          │
    │              │
    v              v
┌───────────┐ ┌───────────┐
│ Payment   │ │ Compensa- │
│ Successful│ │   tion    │
└───┬───────┘ │  (Release │
    │         │   Stock)  │
    v         └─────┬─────┘
┌───────┐          │
│Create │          │
│Invoice│          │
└───┬───┘          │
    │              │
    v              v
┌───────┐     ┌───────────┐
│ Send  │     │  Notify   │
│Email  │     │  Failure  │
└───┬───┘     └─────┬─────┘
    │              │
    v              v
┌───────┐     ┌───────────┐
│  END  │     │    END    │
└───────┘     └───────────┘

================================================================================
                    ERROR HANDLING TYPES
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. VALIDATION ERROR                                                         │
│    └──> Log error → Notify user → Cancel order                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. STOCK UNAVAILABLE                                                        │
│    └──> Log warning → Notify user → Cancel order                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. PAYMENT FAILURE (with Retry)                                             │
│    └──> Retry (3 attempts, exponential backoff)                            │
│         └──> Success → Continue                                            │
│         └──> Failed → Compensate (release stock) → Notify → Cancel         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. SERVICE UNAVAILABLE (Circuit Breaker)                                    │
│    └──> Circuit OPEN after 3 failures                                      │
│         └──> Block requests for 30 seconds                                 │
│         └──> HALF_OPEN test call                                           │
│              └──> Success → Close circuit                                  │
│              └──> Failed → Keep OPEN                                       │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                    COMPENSATION ACTIONS
================================================================================

  Payment Failure ──► Release Stock ──► Refund Payment (if needed)
  
  Stock Error ──────► Cancel Order ──► Notify User
  
  Validation Error ──► Log Error ──► Return to User

================================================================================
"""
    print(diagram)


# ============================================
# Complete Error Handling Demo
# ============================================

def demonstrate_complete_error_handling():
    """Complete demo with all error handling patterns"""
    
    print("\n" + "="*70)
    print("DEMO 4: COMPLETE ERROR HANDLING FLOW")
    print("="*70)
    
    logger = logging.getLogger(__name__)
    
    # Simulate order processing with all error types
    scenarios = [
        ("Valid order", {"order_id": 2001, "amount": 100, "valid": True, "stock": True}),
        ("Invalid order", {"order_id": 2002, "amount": -50, "valid": False, "stock": True}),
        ("Out of stock", {"order_id": 2003, "amount": 100, "valid": True, "stock": False}),
        ("Payment failure", {"order_id": 2004, "amount": 100, "valid": True, "stock": True, "payment_fail": True}),
    ]
    
    for scenario_name, data in scenarios:
        print(f"\n{'='*50}")
        print(f"Scenario: {scenario_name}")
        print(f"{'='*50}")
        
        order_id = data['order_id']
        
        # Step 1: Validate order
        logger.info(f"Validating order {order_id}", extra={'order_id': order_id})
        if not data['valid']:
            logger.error(f"Order {order_id} validation failed", extra={'order_id': order_id})
            print(f"❌ Order {order_id} cancelled: Invalid data")
            continue
        
        # Step 2: Check stock (with circuit breaker)
        logger.info(f"Checking stock for order {order_id}", extra={'order_id': order_id})
        stock_service = UnreliableStockService()
        
        try:
            stock_result = stock_service.check_stock(product_id=101, quantity=1)
            if not data['stock']:
                print(f"❌ Order {order_id} cancelled: Out of stock")
                continue
        except Exception as e:
            print(f"❌ Order {order_id} failed: Stock service error - {e}")
            continue
        
        # Step 3: Process payment (with retry)
        logger.info(f"Processing payment for order {order_id}", extra={'order_id': order_id})
        payment_service = UnreliablePaymentService(failure_rate=0.8 if data.get('payment_fail') else 0)
        
        try:
            payment_result = payment_service.process_payment(amount=data['amount'], order_id=order_id)
            print(f"✅ Order {order_id} completed successfully!")
        except Exception as e:
            print(f"❌ Order {order_id} failed after retries: {e}")
            # Compensation action
            logger.info(f"Compensating: releasing stock for order {order_id}", extra={'order_id': order_id})
            print(f"  ↳ Compensation: Stock released for order {order_id}")


# ============================================
# Main Execution
# ============================================

if __name__ == "__main__":
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    logger = setup_logging(log_level="DEBUG")
    
    print("\n" + "="*70)
    print("STAGE 9: LOGGING, MONITORING AND ERROR HANDLING")
    print("="*70)
    
    # Show BPMN diagram
    show_bpmn_diagram()
    
    # Demo 1: Structured logging
    demonstrate_logging()
    
    # Demo 2: Retry pattern
    demonstrate_retry()
    
    # Demo 3: Circuit breaker
    demonstrate_circuit_breaker()
    
    # Demo 4: Complete flow
    demonstrate_complete_error_handling()
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nLog files created:")
    print("  - logs/clinic_mis.log (all logs in JSON format)")
    print("  - logs/errors.log (error-only logs)")
    print("\nCheck the logs for structured JSON output")
