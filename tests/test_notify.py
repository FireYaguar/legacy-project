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
