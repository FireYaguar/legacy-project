# Reengineering Plan: src/notify.py

**Варіант 3** (практична 8). Складено: __TIME__, до першого рядка коду.

## Baseline (стан «до»)

| Метрика | Значення |
|---|---|
| pylint score | 4.81 / 10 |
| Найскладніша функція (CC) | notify_user, CC = 4 (A) |
| LOC (SLOC) | 77 (39) |
| Функцій у файлі | 4 |
| Помилки E / попередження W | 0 / 9 |
| Coverage notify.py | 0 % |

## Антипатерни

1. Hardcoded credentials: SMTP_USER і SMTP_PASS записані у коді (рядки 12-13).
2. Magic numbers і ланцюжок if/elif: msg_type 1, 2, 3 (рядки 38-56).
3. Copy-paste: три майже однакові виклики send_email у notify_user (рядки 39-56).
4. Мертвий код і заглушки: закоментована реалізація send_email, невикористаний
   імпорт smtplib, заглушка log_notification, застарілі коментарі (рядки 3, 6-7, 17-32, 57-59, 75-77).

## To-Be архітектура

| Функція / модуль | Відповідальність | Очікуваний CC |
|---|---|---|
| MessageType (Enum) | Іменовані типи повідомлень замість чисел | 1 |
| MESSAGE_TEMPLATES | Тема й текст кожного типу в одному місці | 1 |
| SmtpConfig.from_env() | Налаштування SMTP із змінних середовища | 3 |
| build_message() | Побудувати (тема, текст) за типом | 2 |
| notify_user() | Оркестратор: побудувати і надіслати | 2 |
| send_email() | Надіслати лист (заглушка, як і раніше) | 1 |
| bulk_notify() | Розсилка зі лічильниками sent / failed | 3 |
| log_notification() | Місце для логування (без змін поведінки) | 1 |

## Послідовність перетворень

| Ітер. | Техніка | Що робимо | Критерій Done |
|---|---|---|---|
| 1 | Characterization tests | Тести поточної поведінки до змін | усі тести зелені на старому коді |
| 2 | Introduce Enum | MessageType замість 1, 2, 3 | тести зелені, чисел у notify_user немає |
| 3 | Consolidate Duplicates | Словник шаблонів і build_message замість if/elif | CC notify_user < 5, тести зелені |
| 4 | Credentials у env | SmtpConfig і змінні середовища, .env.example | пароля немає в коді, тести зелені |
| 5 | Remove dead code | Видалити закоментований код, імпорт, додати docstring | pylint > 7.0, тести зелені |

## Reengineering Plan Summary

| Параметр | Значення |
|---|---|
| Git-гілка | reengineering/notify-module |
| Scope (файли) | src/notify.py, tests/test_notify.py (новий), tests/test_shipping_fix.py (одна перевірка), .env.example, CHANGELOG.md |
| Головна техніка | Consolidate Duplicates + Introduce Enum |
| Зовнішній інтерфейс зміниться? | Ні: send_email, notify_user, bulk_notify, log_notification і SMTP_* зберігають імена та поведінку |
| Стратегія відкату | git revert до початкового стану гілки |
| Критерій Done | pylint > 7.0, CC < 10, coverage > 70 %, pytest зелений |
| Очікуваний час | 3-4 години |
