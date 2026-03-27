import smtplib
from unittest.mock import MagicMock, mock_open, patch

import pytest
from fastapi import HTTPException

import services.email_service as email_service_module
from services.email_service import EmailService

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_user(
    email="owner@example.com",
    full_name="John Doe",
    house_id="MS1",
):
    user = MagicMock()
    user.email = email
    user.full_name = full_name
    user.house_id = house_id
    return user


FAKE_TEMPLATE = (
    "Hello {user_name}, pass {pass_id}, guest {guest_name}, "
    "dates {date_range}, house {house_id}, status {approved}, "
    "reason {reason}, qr {qr_code}"
)


# ─── _get_report_template ─────────────────────────────────────────────────────


class TestGetReportTemplate:
    def test_returns_rendered_string(self):
        with patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)):
            result = EmailService._get_report_template(
                pass_id="P1",
                user_name="John Doe",
                guest_name="Jane",
                date_range="2025-01-01 / 2025-01-05",
                approved=True,
                house_id="MS1",
                reason="All good",
            )

        assert "P1" in result
        assert "John Doe" in result
        assert "Jane" in result
        assert "MS1" in result
        assert "All good" in result

    def test_approved_includes_qr_img_tag(self):
        with patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)):
            result = EmailService._get_report_template(
                pass_id="P1",
                user_name="John",
                guest_name="Jane",
                date_range="2025-01-01",
                approved=True,
                house_id="MS1",
                reason="OK",
            )

        assert "cid:qr_image" in result

    def test_rejected_excludes_qr_img_tag(self):
        with patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)):
            result = EmailService._get_report_template(
                pass_id="P1",
                user_name="John",
                guest_name="Jane",
                date_range="2025-01-01",
                approved=False,
                house_id="MS1",
                reason="Denied",
            )

        assert "cid:qr_image" not in result

    def test_approved_label_when_true(self):
        template = "status={approved}"
        with patch("builtins.open", mock_open(read_data=template)):
            result = EmailService._get_report_template(
                pass_id="P1",
                user_name="John",
                guest_name="Jane",
                date_range="",
                approved=True,
                house_id="MS1",
                reason="",
            )

        assert "Approved" in result

    def test_rejected_label_when_false(self):
        template = "status={approved}"
        with patch("builtins.open", mock_open(read_data=template)):
            result = EmailService._get_report_template(
                pass_id="P1",
                user_name="John",
                guest_name="Jane",
                date_range="",
                approved=False,
                house_id="MS1",
                reason="",
            )

        assert "Rejected" in result


# ─── send_review_email_via_smtp ───────────────────────────────────────────────


class TestSendReviewEmailViaSmtp:
    # ── not credentials ──────────────────────────────────────────────────

    def test_skips_when_no_credentials(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "")

        mock_users = MagicMock()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        # No debe lanzar excepción ni intentar conectar
        EmailService.send_review_email_via_smtp(
            pass_id="P1",
            date_range="2025-01-01",
            target_house="MS1",
            guest_name="Jane",
            approved=True,
        )

        mock_users.objects.assert_not_called()

    # ── user not found ──────────────────────────────────────────────────

    def test_raises_404_when_user_not_found(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = None
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="NOPE",
                guest_name="Jane",
                approved=True,
            )

        assert exc_info.value.status_code == 404

    # ── approved flow ─────────────────────────────────────────────────────────

    def test_approved_attaches_qr_image(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = make_mock_user()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        monkeypatch.setattr(
            email_service_module, "generate_qr", lambda *a, **kw: b"\xff\xd8fake_jpg"
        )

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch("smtplib.SMTP_SSL") as mock_smtp_cls,
        ):
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server

            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=True,
            )

        mock_server.send_message.assert_called_once()
        sent_msg = mock_server.send_message.call_args[0][0]
        content_ids = [part.get("Content-ID", "") for part in sent_msg.walk()]
        assert any("qr_image" in cid for cid in content_ids)

    def test_rejected_does_not_attach_qr_image(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = make_mock_user()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        mock_generate_qr = MagicMock()
        monkeypatch.setattr(email_service_module, "generate_qr", mock_generate_qr)

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch("smtplib.SMTP_SSL") as mock_smtp_cls,
        ):
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server

            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=False,
            )

        mock_generate_qr.assert_not_called()

    # ── SMTP correctly configured ─────────────────────────────────────────

    def test_smtp_login_called_with_credentials(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = make_mock_user()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        monkeypatch.setattr(
            email_service_module, "generate_qr", lambda *a, **kw: b"\xff\xd8fake"
        )

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch("smtplib.SMTP_SSL") as mock_smtp_cls,
        ):
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server

            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=True,
            )

        mock_server.login.assert_called_once_with("sender@example.com", "secret")

    def test_email_headers_set_correctly(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        user = make_mock_user(email="owner@example.com")
        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = user
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        monkeypatch.setattr(
            email_service_module, "generate_qr", lambda *a, **kw: b"\xff\xd8fake"
        )

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch("smtplib.SMTP_SSL") as mock_smtp_cls,
        ):
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server

            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=True,
                subject="Custom Subject",
            )

        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "owner@example.com"
        assert sent_msg["From"] == "sender@example.com"
        assert sent_msg["Subject"] == "Custom Subject"

    def test_uses_custom_smtp_server_and_port(self, monkeypatch):
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = make_mock_user()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        monkeypatch.setattr(
            email_service_module, "generate_qr", lambda *a, **kw: b"\xff\xd8fake"
        )

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch("smtplib.SMTP_SSL") as mock_smtp_cls,
        ):
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server

            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=False,
                smtp_server="smtp.custom.com",
                port=587,
            )

        call_args = mock_smtp_cls.call_args
        assert call_args[0][0] == "smtp.custom.com"
        assert call_args[0][1] == 587

    # ── handling SMTP errors ────────────────────────────────────────────────

    def test_smtp_exception_does_not_propagate(self, monkeypatch):
        """The service logs the exception but does not re-raise it."""
        monkeypatch.setattr(email_service_module, "SENDER_EMAIL", "sender@example.com")
        monkeypatch.setattr(email_service_module, "SENDER_PASSWORD", "secret")

        mock_users = MagicMock()
        mock_users.objects.return_value.first.return_value = make_mock_user()
        monkeypatch.setattr(email_service_module, "Users", mock_users)

        monkeypatch.setattr(
            email_service_module, "generate_qr", lambda *a, **kw: b"\xff\xd8fake"
        )

        with (
            patch("builtins.open", mock_open(read_data=FAKE_TEMPLATE)),
            patch(
                "smtplib.SMTP_SSL",
                side_effect=smtplib.SMTPException("Connection failed"),
            ),
        ):
            EmailService.send_review_email_via_smtp(
                pass_id="P1",
                date_range="2025-01-01",
                target_house="MS1",
                guest_name="Jane",
                approved=True,
            )
