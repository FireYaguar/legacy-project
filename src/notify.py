"""Система сповіщень: листи користувачам про події замовлень.

Публічний інтерфейс: send_email, notify_user, bulk_notify, log_notification
та константи SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
"""

import os
from dataclasses import dataclass
from enum import IntEnum

from dotenv import load_dotenv

# credentials are read from environment variables (see .env.example);
# load_dotenv() fills them from a local .env file that is not stored in git
load_dotenv()

BULK_SUBJECT = "Notification"


@dataclass(frozen=True)
class SmtpConfig:
    """Налаштування SMTP-сервера."""
    host: str
    port: int
    user: str
    password: str

    @classmethod
    def from_env(cls):
        """Читає налаштування зі змінних SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS."""
        return cls(
            host=os.getenv("SMTP_HOST") or "smtp.gmail.com",
            port=int(os.getenv("SMTP_PORT") or 587),
            user=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASS", ""),
        )


SMTP_CONFIG = SmtpConfig.from_env()
# module-level names are kept for backward compatibility
SMTP_HOST = SMTP_CONFIG.host
SMTP_PORT = SMTP_CONFIG.port
SMTP_USER = SMTP_CONFIG.user
SMTP_PASS = SMTP_CONFIG.password


class MessageType(IntEnum):
    """Типи повідомлень, які вміє надсилати notify_user()."""
    ORDER_CONFIRMED = 1
    PAYMENT_RECEIVED = 2
    ORDER_CANCELLED = 3


MESSAGE_TEMPLATES = {
    MessageType.ORDER_CONFIRMED: ("Order Confirmed",
                                  "Your order #{order_id} has been confirmed."),
    MessageType.PAYMENT_RECEIVED: ("Payment Received",
                                   "Payment of {amount} UAH received."),
    MessageType.ORDER_CANCELLED: ("Order Cancelled",
                                  "Your order #{order_id} was cancelled."),
}


def send_email(to, subj, body):  # pylint: disable=unused-argument
    """Заглушка відправки листа: лише друкує повідомлення і повертає True.

    Реальну відправку через SMTP не реалізовано; підпис збережено для
    сумісності з викликами notify_user() та bulk_notify().
    """
    print(f"[STUB] Would send email to {to}: {subj}")
    return True


def build_message(msg_type, data):
    """Повертає (тема, текст) для типу повідомлення або None, якщо тип невідомий."""
    template = MESSAGE_TEMPLATES.get(msg_type)
    if template is None:
        return None
    subject, body = template
    return subject, body.format(order_id=data.get('order_id'),
                                amount=data.get('amount'))


def notify_user(user_id, msg_type, data=None):  # pylint: disable=unused-argument
    """Надсилає користувачу лист за типом повідомлення (див. MessageType).

    Для невідомого типу нічого не робить. Адреса береться з data['email'].
    """
    message = build_message(msg_type, data)
    if message is None:
        return
    subject, body = message
    send_email(data.get('email', ''), subject, body)


def bulk_notify(users, msg):
    """Надсилає однаковий лист кожному користувачу зі списку.

    Повертає {"sent": N, "failed": M}; помилка одного отримувача
    не зупиняє розсилку.
    """
    sent = 0
    failed = 0
    for user in users:
        try:
            send_email(user.get('email', ''), BULK_SUBJECT, msg)
            sent += 1
        except Exception:  # pylint: disable=broad-exception-caught
            failed += 1
    return {"sent": sent, "failed": failed}


def log_notification(user_id, tp, status):  # pylint: disable=unused-argument
    """Місце для запису сповіщення в БД (поки що нічого не робить)."""
    return None
