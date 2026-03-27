import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from fastapi import HTTPException

from commons.constants import SENDER_EMAIL, SENDER_PASSWORD
from commons.log_helper import get_logger
from models.users import Users
from services.qr_generator_service import generate_qr

_LOG = get_logger(__name__)


class EmailService:
    @staticmethod
    def _get_report_template(
        pass_id: str,
        user_name: str,
        guest_name: str,
        date_range: str,
        approved: bool,
        house_id: str,
        reason: str,
    ) -> str:
        """
        Generate HTML template for the review email.
        Loads template from file and replaces placeholders.
        """
        template_path = (
            Path(__file__).parent.parent / "templates" / "review_template.html"
        )
        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        return template.format(
            pass_id=pass_id,
            user_name=user_name,
            date_range=date_range,
            guest_name=guest_name,
            house_id=house_id,
            approved="Approved" if approved else "Rejected",
            reason=reason,
            qr_code='<p><img src="cid:qr_image" alt="QR Code" style="max-width:200px;" /></p>'
            if approved
            else "",
        )

    @staticmethod
    def send_review_email_via_smtp(
        pass_id: str,
        date_range: str,
        target_house: str,
        guest_name: str,
        approved: bool,
        reason: str = "No reason provided",
        subject: str = "Automated report for review of pass",
        smtp_server: str = "smtp.gmail.com",
        port: int = 465,
    ):
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            _LOG.warning(
                "Email credentials not set in environment variables. Skipping email sending."
            )
            return

        user_info = Users.objects(house_id=target_house).first()

        if not user_info:
            raise HTTPException(
                status_code=404, detail="Target user not found for the given house ID"
            )

        target_email = user_info.email

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email

        html_content = EmailService._get_report_template(
            pass_id,
            user_info.full_name,
            guest_name,
            date_range,
            approved,
            user_info.house_id,
            reason,
        )
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if approved:
            qr_jpg_bytes = generate_qr(pass_id, png_image=True)

            img = MIMEImage(qr_jpg_bytes, _subtype="jpeg")
            img.add_header("Content-ID", "<qr_image>")
            img.add_header("Content-Disposition", "inline; filename=qr_code.png")
            msg.attach(img)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            _LOG.info("Email sent successfully to %s", target_email)
        except Exception as e:
            _LOG.exception("Failed to send email: %s", e)
