# NOTE: [AI CITATION] Used chatGPT to introduce using email.message/smtplib, but all of the code is mine

import typing
import smtplib

from logging import Logger

from email.message import EmailMessage
from ssl import SSLContext, create_default_context

class Emailer:
    ETHEREAL_SMTP_SERVER: typing.Final[str] = "smtp.ethereal.email"
    ETHEREAL_SMTP_STARTTLS_PORT: typing.Final[int] = 587

    def __init__(self, logger: Logger) -> None:
        self.logger: Logger = logger
        self.ssl_ctx: SSLContext = create_default_context()

    def _send_notif_email(
        self,
        email: str,
        password: str,
        subject: str,
        body: str
    ) -> None:
        notif_msg: EmailMessage = EmailMessage()
        notif_msg["From"] = email
        notif_msg["To"]   = email
        notif_msg["Subject"] = subject
        notif_msg.set_content(body)

        with smtplib.SMTP(
            self.ETHEREAL_SMTP_SERVER,
            self.ETHEREAL_SMTP_STARTTLS_PORT
        ) as smtp_server:
            smtp_server.starttls(context=self.ssl_ctx)
            smtp_server.login(email, password)
            smtp_server.send_message(notif_msg)

    def send_pw_update(
        self,
        name: str,
        email: str,
        password: str
    ) -> None:
        body: str = (
            f"Hello, {name}!\n"
            "Your password has been successfully reset!\n"
            "If this was not you then contact support immediately!\n"
            "Sincerely, Notification Service"
        )

        self._send_notif_email(
            email=email,
            password=password,
            subject="Password Update",
            body=body
        )

    def send_trade_offer_init(
        self,
        trade_id: str,
        sender_info: tuple[str, str, str],
        receiver_info: tuple[str, str, str],
        games: tuple[str, str]
    ) -> None:
        sender_name, sender_email, sender_password = sender_info
        receiver_name, receiver_email, receiver_password = receiver_info
        offered_game, requested_game = games

        sender_body: str = (
            f"Hello, {sender_name}!\n"
            f"We have received your trade offer of {offered_game} for {requested_game} from {receiver_name} | {receiver_email}!\n"
            f"The trade ID of your trade offer is {trade_id}!\n"
            "Sincerely, I'm fucking tired of this bullshit\n"
        )

        self._send_notif_email(
            email=sender_email,
            password=sender_password,
            subject="Trade offer processed",
            body=sender_body
        )

        receiver_body: str = (
            f"Hello, {receiver_name}!\n"
            f"You have received a trade offer from '{sender_name}/{sender_email}'!\n"
            f"They have offered '{offered_game}' for '{requested_game}'!\n"
            f"Use this trade ID: '{trade_id}' to accept/reject the offer!\n"
            "Sincerely, yeah whatever"
        )

        self._send_notif_email(
            email=receiver_email,
            password=receiver_password,
            subject="Trade offer received",
            body=receiver_body
        )

    def send_trade_offer_accepted(
        self,
        sender_info: tuple[str, str, str],
        receiver_info: tuple[str, str, str],
        games: tuple[str, str]
    ) -> None:
        sender_name, sender_email, sender_password = sender_info
        receiver_name, receiver_email, receiver_password = receiver_info
        offered_game, requested_game = games

        sender_body: str = (
            f"Hello, {sender_name}!\n"
            f"Your trade offer of '{offered_game}' for '{requested_game}' from '{receiver_name}/{receiver_email}' was successfully accepted!\n"
            "Sincerely, yep yep yep\n"
        )

        self._send_notif_email(
            email=sender_email,
            password=sender_password,
            subject="Trade offer accepted",
            body=sender_body
        )

        receiver_body: str = (
            f"Hello, {receiver_name}!\n"
            f"The trade offer of '{requested_game}' for '{offered_game}' from '{sender_name}/{sender_email}' was successfully accepted!\n"
            "Sincerely, yep yep yep\n"
        )

        self._send_notif_email(
            email=receiver_email,
            password=receiver_password,
            subject="Trade offer accepted",
            body=receiver_body
        )

    def send_trade_offer_rejected(
        self,
        sender_info: tuple[str, str, str],
        receiver_info: tuple[str, str, str],
        games: tuple[str, str]
    ) -> None:
        sender_name, sender_email, sender_password = sender_info
        receiver_name, receiver_email, receiver_password = receiver_info
        offered_game, requested_game = games

        sender_body: str = (
            f"Hello, {sender_name}!\n"
            f"Your trade offer of '{offered_game}' for '{requested_game}' from '{receiver_name}/{receiver_email}' was unfortunately rejected :(!\n"
            "Sincerely, yep yep yep\n"
        )

        self._send_notif_email(
            email=sender_email,
            password=sender_password,
            subject="Trade offer rejected :(",
            body=sender_body
        )

        receiver_body: str = (
            f"Hello, {receiver_name}!\n"
            f"The trade offer of '{requested_game}' for '{offered_game}' from '{sender_name}/{sender_email}' was unfortunately rejected!\n"
            "Sincerely, yep yep yep\n"
        )

        self._send_notif_email(
            email=receiver_email,
            password=receiver_password,
            subject="Trade offer rejected",
            body=receiver_body
        )

