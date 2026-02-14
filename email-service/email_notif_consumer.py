import json
import typing

from emailer import Emailer
from logging import Logger

from kafka import KafkaConsumer
from kafka.errors import KafkaError

class EmailNotifConsumer:
    TOPIC: typing.Final[str] = "email-notifs"
    BOOTSTRAP_SERVERS: typing.Final[str] = "kafka:9092"

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.emailer = Emailer(logger)

        self.consumer: KafkaConsumer = KafkaConsumer(
            self.TOPIC,
            bootstrap_servers=self.BOOTSTRAP_SERVERS,
            value_deserializer=lambda msg: json.loads(msg.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="email-notif-stream"
        )

        self.notif_handlers: dict = {
            "pw_update"            : self._handle_pw_update,
            "trade_offer_init"     : self._handle_trade_offer_init,
            "trade_offer_accepted" : self._handle_trade_offer_accepted,
            "trade_offer_rejected" : self._handle_trade_offer_rejected,
        }

    def start_consuming_notifs(self) -> None:
        while True:
            try:
                for notif in self.consumer:
                    self._handle_notif(notif.value)
                    self.consumer.commit()

            except KafkaError as e:
                raise ValueError(f"Failed to start consuming due to a kafka error! Reason: {str(e)}")

            except Exception as e:
                raise ValueError(f"Failed to start consuming due to an unexpected error! Reason: {str(e)}")

    def _handle_notif(self, notif: dict) -> None:
        notif_type = notif.get("type")
        notif_handler = self.notif_handlers.get(notif_type)
        if notif_handler is None:
            raise ValueError(f"Failed to find handler for unexpected notification type: {notif_type}!")

        notif_handler(notif)

    def _handle_pw_update(self, notif: dict) -> None:
        self.logger.info(notif)

        self.emailer.send_pw_update(
            notif["name"],
            *notif["auth_combo"]
        )

    def _handle_trade_offer_init(self, notif: dict) -> None:
        self.logger.info(notif)

        trade_id: str = notif["trade_id"]

        sender_info: tuple[str, str, str] = tuple(notif["sender_info"])
        receiver_info: tuple[str, str, str] = tuple(notif["receiver_info"])

        games: tuple[str, str] = tuple(notif["games"])

        self.emailer.send_trade_offer_init(
            trade_id=trade_id,
            sender_info=sender_info,
            receiver_info=receiver_info,
            games=games
        )

    def _handle_trade_offer_accepted(self, notif: dict) -> None:
        self.logger.info(notif)

        sender_info: tuple[str, str, str] = tuple(notif["sender_info"])
        receiver_info: tuple[str, str, str] = tuple(notif["receiver_info"])

        games: tuple[str, str] = tuple(notif["games"])

        self.emailer.send_trade_offer_accepted(
            sender_info=sender_info,
            receiver_info=receiver_info,
            games=games
        )

    def _handle_trade_offer_rejected(self, notif: dict) -> None:
        self.logger.info(notif)

        sender_info: tuple[str, str, str] = tuple(notif["sender_info"])
        receiver_info: tuple[str, str, str] = tuple(notif["receiver_info"])

        games: tuple[str, str] = tuple(notif["games"])

        self.emailer.send_trade_offer_rejected(
            sender_info=sender_info,
            receiver_info=receiver_info,
            games=games
        )

