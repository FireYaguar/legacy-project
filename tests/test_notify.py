"""Тести для src/notify.py: поведінка модуля, яку реінженерія не має змінити."""
import pytest

import src.notify as notify


@pytest.fixture
def sent(monkeypatch):
    """Підміняє send_email() і збирає аргументи всіх викликів."""
    calls = []

    def fake_send(to, subj, body):
        calls.append((to, subj, body))
        return True

    monkeypatch.setattr(notify, "send_email", fake_send)
    return calls


# --- send_email ---------------------------------------------------------

def test_send_email_returns_true(capsys):
    assert notify.send_email("a@b.c", "Hi", "text") is True
    assert "[STUB] Would send email to a@b.c: Hi" in capsys.readouterr().out


# --- notify_user: кожен тип повідомлення ---------------------------------

def test_notify_order_confirmed(sent):
    notify.notify_user(1, 1, {"email": "a@b.c", "order_id": 42})
    assert sent == [("a@b.c", "Order Confirmed",
                     "Your order #42 has been confirmed.")]


def test_notify_payment_received(sent):
    notify.notify_user(1, 2, {"email": "a@b.c", "amount": 150.5})
    assert sent == [("a@b.c", "Payment Received",
                     "Payment of 150.5 UAH received.")]


def test_notify_order_cancelled(sent):
    notify.notify_user(1, 3, {"email": "a@b.c", "order_id": 7})
    assert sent == [("a@b.c", "Order Cancelled",
                     "Your order #7 was cancelled.")]


@pytest.mark.parametrize("msg_type", [0, 4, 5, 99, -1, "1", None])
def test_notify_unknown_type_sends_nothing(sent, msg_type):
    assert notify.notify_user(1, msg_type, {"email": "a@b.c"}) is None
    assert sent == []


def test_notify_missing_email_uses_empty_recipient(sent):
    notify.notify_user(1, 1, {"order_id": 5})
    assert sent[0][0] == ""


def test_notify_missing_fields_are_rendered_as_none(sent):
    notify.notify_user(1, 1, {"email": "a@b.c"})
    notify.notify_user(1, 2, {"email": "a@b.c"})
    assert sent[0][2] == "Your order #None has been confirmed."
    assert sent[1][2] == "Payment of None UAH received."


def test_notify_sends_exactly_one_email(sent):
    notify.notify_user(1, 1, {"email": "a@b.c", "order_id": 1})
    assert len(sent) == 1


# --- bulk_notify -------------------------------------------------------

def test_bulk_notify_counts_sent(sent):
    users = [{"email": "a@b.c"}, {"email": "d@e.f"}, {}]
    assert notify.bulk_notify(users, "Promo") == {"sent": 3, "failed": 0}
    assert sent[0] == ("a@b.c", "Notification", "Promo")
    assert sent[2][0] == ""


def test_bulk_notify_empty_list(sent):
    assert notify.bulk_notify([], "Promo") == {"sent": 0, "failed": 0}
    assert sent == []


def test_bulk_notify_counts_failed(monkeypatch):
    def broken(to, subj, body):
        if to == "bad@x.y":
            raise RuntimeError("smtp down")
        return True

    monkeypatch.setattr(notify, "send_email", broken)
    users = [{"email": "ok@x.y"}, {"email": "bad@x.y"}, {"email": "ok2@x.y"}]
    assert notify.bulk_notify(users, "Promo") == {"sent": 2, "failed": 1}


# --- log_notification --------------------------------------------------

def test_log_notification_returns_none():
    assert notify.log_notification(1, "order", "sent") is None


# --- MessageType (ітерація 2) -------------------------------------------

def test_message_type_values_match_old_numbers():
    assert notify.MessageType.ORDER_CONFIRMED == 1
    assert notify.MessageType.PAYMENT_RECEIVED == 2
    assert notify.MessageType.ORDER_CANCELLED == 3


def test_notify_accepts_enum_members(sent):
    notify.notify_user(1, notify.MessageType.PAYMENT_RECEIVED,
                       {"email": "a@b.c", "amount": 10})
    assert sent == [("a@b.c", "Payment Received",
                     "Payment of 10 UAH received.")]


# --- MESSAGE_TEMPLATES і build_message (ітерація 3) ----------------------

def test_every_message_type_has_a_template():
    assert set(notify.MESSAGE_TEMPLATES) == set(notify.MessageType)


def test_build_message_known_type():
    assert notify.build_message(1, {"order_id": 9}) == (
        "Order Confirmed", "Your order #9 has been confirmed.")


def test_build_message_unknown_type_returns_none():
    assert notify.build_message(99, {}) is None
    assert notify.build_message(99, None) is None


def test_new_message_type_needs_only_a_template(sent, monkeypatch):
    monkeypatch.setitem(notify.MESSAGE_TEMPLATES, 10,
                        ("Shipped", "Order #{order_id} shipped."))
    notify.notify_user(1, 10, {"email": "a@b.c", "order_id": 3})
    assert sent == [("a@b.c", "Shipped", "Order #3 shipped.")]


# --- SmtpConfig: облікові дані з середовища (ітерація 4) ------------------

def test_smtp_config_reads_environment(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "robot@example.org")
    monkeypatch.setenv("SMTP_PASS", "s3cret")
    cfg = notify.SmtpConfig.from_env()
    assert (cfg.host, cfg.port, cfg.user, cfg.password) == (
        "smtp.example.org", 2525, "robot@example.org", "s3cret")


def test_smtp_config_defaults_without_environment(monkeypatch):
    for name in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.delenv(name, raising=False)
    cfg = notify.SmtpConfig.from_env()
    assert (cfg.host, cfg.port) == ("smtp.gmail.com", 587)
    assert cfg.user == "" and cfg.password == ""


def test_smtp_config_empty_values_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_PORT", "")
    cfg = notify.SmtpConfig.from_env()
    assert (cfg.host, cfg.port) == ("smtp.gmail.com", 587)


def test_smtp_constants_kept_for_compatibility():
    for name in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        assert hasattr(notify, name)


def test_no_hardcoded_password_in_source():
    with open(notify.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "qwerty123" not in source
    assert "system@company.com" not in source


def test_env_example_lists_smtp_variables_without_values():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, ".env.example"), encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    assert "SMTP_USER=" in lines
    assert "SMTP_PASS=" in lines
