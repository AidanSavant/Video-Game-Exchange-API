import json
import typing

from .user import User
from .users import Users

from .trade import Trade
from .trades import Trades

from kafka import KafkaProducer
from kafka.errors import KafkaError

class EmailNotifProducer:
    TOPIC: typing.Final[str] = "email-notifs"
    BOOTSTRAP_SERVERS: typing.Final[str] = "kafka:9092"

    def __init__(self, users: Users, trades: Trades) -> None:
        self.users:  Users  = users
        self.trades: Trades = trades

        self.producer: KafkaProducer = KafkaProducer(
            bootstrap_servers=self.BOOTSTRAP_SERVERS,
            value_serializer=lambda msg: json.dumps(msg).encode("utf-8")
        )

    # NOTE: An enum should be preferred over str for the 'type' value
    def send_pw_update_notif(self, name: str, auth_combo: tuple[str, str]) -> None:
        self._publish_notif({
            "type"       : "pw_update",
            "name"       : name,
            "auth_combo" : auth_combo
        })

    def send_trade_offer_notif(self, trade_id: str) -> None:
        self._build_trade_notif(type="trade_offer_init", trade_id=trade_id)

    def send_trade_accepted_notif(self, trade_id: str) -> None:
        self._build_trade_notif(type="trade_offer_accepted", trade_id=trade_id)

    def send_trade_rejected_notif(self, trade_id: str) -> None:
        self._build_trade_notif(type="trade_offer_rejected", trade_id=trade_id)

    def _build_trade_notif(self, type: str, trade_id: str) -> None:
        sender_info, receiver_info, games = self._get_traders_info(trade_id)

        self._publish_notif({
            "type"          : type,
            "trade_id"      : trade_id,
            "sender_info"   : sender_info,
            "receiver_info" : receiver_info,
            "games"         : games,
        })

    # NOTE: I'm not type annotating that god forsaken abomination of a return type
    def _get_traders_info(self, trade_id: str):
        trade: Trade | None = self.trades.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Failed to get trade info! Reason: {trade_id} does not point to a valid trade!")

        sender_user: User | None = self.users.get_user(trade.sender_email)
        if sender_user is None:
            raise ValueError(f"Failed to get user '{trade.sender_email}'! Reason: not a valid email!")

        receiver_user: User | None = self.users.get_user(trade.receiver_email)
        if receiver_user is None:
            raise ValueError(f"Failed to get user '{trade.receiver_email}'! Reason: not a valid email!")

        return (
            (sender_user.name, sender_user.email, sender_user.password),
            (receiver_user.name, receiver_user.email, receiver_user.password),
            (trade.offered_game, trade.requested_game)
        )

    def _publish_notif(self, value: dict) -> None:
        try:
            self.producer.send(self.TOPIC, value=value)
            self.producer.flush()

        except KafkaError as e:
            raise ValueError(f"Failed to send notification due to a kafka error! Reason: {str(e)}")

        except Exception as e:
            raise ValueError(f"Failed to send notification due to an unexpected error! Reason: {str(e)}")        

