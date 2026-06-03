\# Clinic Management System (МИС)



\[!\[CI/CD](https://github.com/marabekjone/clinic-mis/actions/workflows/ci.yml/badge.svg)](https://github.com/marabekjone/clinic-mis/actions)

\[!\[Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)

\[!\[Flask](https://img.shields.io/badge/Flask-3.0-red.svg)](https://flask.palletsprojects.com)

\[!\[FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)

\[!\[Docker](https://img.shields.io/badge/Docker-24.0-blue.svg)](https://docker.com)



\## О проекте



Clinic Management System - микросервисное приложение для управления клиникой.



\## Архитектура

Frontend (8080) ---> Module A (5001) - Services

|

\---> Module B (5002) - Medicines

|

\---> Module C (3000) - Invoices



\## Модули



| Модуль | Порт | Фреймворк | Описание |

|--------|------|-----------|----------|

| Module A | 5001 | Flask | Услуги и лицензии |

| Module B | 5002 | FastAPI | Лекарства |

| Module C | 3000 | Flask | Счета |

| Frontend | 8080 | Flask | UI |



\## Быстрый старт



\### Локальный запуск



```bash

\# Установить зависимости

pip install -r requirements.txt



\# Запустить модули

python module\_a\_simple.py      # Терминал 1

python module\_b\_simple.py      # Терминал 2

python module\_c\_simple.py      # Терминал 3

python frontend\_server.py      # Терминал 4



\# Открыть в браузере

http://localhost:8080

