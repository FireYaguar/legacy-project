# notify.py
# Notification system
# DEPRECATED - use new_notify.py (which doesn't exist yet)
# kept for reference

import os
import smtplib
from dataclasses import dataclass
from enum import IntEnum

from dotenv import load_dotenv
# from email.mime.text import MIMEText  # commented out - breaks on server

# credentials are read from environment variables (see .env.example);
# load_dotenv() fills them from a local .env file that is not stored in git
load_dotenv()


@dataclass(frozen=True)
class SmtpConfig:
    """Налаштування SMTP-сервера."""
    host: str
    port: int
    user: str
    password: str

    @classmethod
    def from_env(cls):
        """Читає налаштування зі змінних середовища (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS)."""
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


def send_email(to, subj, body):
    # TODO: implement properly
    # old implementation below was removed because it broke prod
    # try:
    #     msg = MIMEText(body)
    #     msg['Subject'] = subj
    #     msg['From'] = SMTP_USER
    #     msg['To'] = to
    #     s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    #     s.starttls()
    #     s.login(SMTP_USER, SMTP_PASS)
    #     s.send_message(msg)
    #     s.quit()
    #     return True
    # except Exception as e:
    #     print("email error:", e)
    #     return False
    print(f"[STUB] Would send email to {to}: {subj}")
    return True


MESSAGE_TEMPLATES = {
    MessageType.ORDER_CONFIRMED: ("Order Confirmed",
                                  "Your order #{order_id} has been confirmed."),
    MessageType.PAYMENT_RECEIVED: ("Payment Received",
                                   "Payment of {amount} UAH received."),
    MessageType.ORDER_CANCELLED: ("Order Cancelled",
                                  "Your order #{order_id} was cancelled."),
}


def build_message(msg_type, data):
    """Повертає (тема, текст) для типу повідомлення або None, якщо тип невідомий."""
    template = MESSAGE_TEMPLATES.get(msg_type)
    if template is None:
        return None
    subject, body = template
    return subject, body.format(order_id=data.get('order_id'),
                                amount=data.get('amount'))


def notify_user(user_id, msg_type, data=None):
    message = build_message(msg_type, data)
    if message is None:
        return
    subject, body = message
    send_email(data.get('email', ''), subject, body)
    # type 4 was removed but code wasn't cleaned up
    # elif msg_type == 4:
    #     send_sms(...)


def bulk_notify(users, msg):
    # used once in 2021 for promo campaign, kept just in case
    sent = 0
    failed = 0
    for u in users:
        try:
            send_email(u.get('email', ''), "Notification", msg)
            sent += 1
        except Exception:
            failed += 1
    return {"sent": sent, "failed": failed}


def log_notification(user_id, tp, status):
    # TODO: write to DB (never implemented)
    pass
