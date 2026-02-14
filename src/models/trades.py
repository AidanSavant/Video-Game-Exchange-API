import typing
from logging import Logger
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from pymongo import MongoClient, ReturnDocument

from .users import Users
from .trade import Trade, TradeStatus

class Trades:
    MONGO_URI: typing.Final[str] = "mongodb://mongo:27017"

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

        client: MongoClient = MongoClient(self.MONGO_URI)
        self.trades: Collection = client["video_game_exchange"]["trades"]

    def add_trade(self, trade: Trade) -> str:
        try:
            self.trades.insert_one({
                "_id": trade.id,
                "sender_email": trade.sender_email,
                "receiver_email": trade.receiver_email,
                "offered_game": trade.offered_game,
                "requested_game": trade.requested_game,
                "status": trade.status.name
            })
            return trade.id
        except PyMongoError as e:
            raise RuntimeError(f"Failed to insert trade '{trade.id}': {e}")

    def get_trade(self, trade_id: str) -> Trade | None:
        trade_data: dict | None = self._find_trade(trade_id)
        if trade_data is None:
            return None
        return self._dict_to_trade(trade_data)

    def accept_trade(self, trade_id: str, users: Users) -> None:
        trade = self.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Trade '{trade_id}' does not exist!")

        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"Trade '{trade_id}' is not pending!")

        users.exchange_games(
            sender_email=trade.sender_email,
            receiver_email=trade.receiver_email,
            sender_game_name=trade.offered_game,
            receiver_game_name=trade.requested_game
        )

        self._update_trade_status(trade_id, TradeStatus.ACCEPTED)

    def reject_trade(self, trade_id: str) -> None:
        trade = self.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Trade '{trade_id}' does not exist!")

        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"Trade '{trade_id}' is not pending!")

        self._update_trade_status(trade_id, TradeStatus.REJECTED)

    def _get_incoming_for(self, email: str) -> list[Trade]:
        cursor = self.trades.find({"receiver_email": email})
        return [self._dict_to_trade(doc) for doc in cursor]

    def _get_outgoing_for(self, email: str) -> list[Trade]:
        cursor = self.trades.find({"sender_email": email})
        return [self._dict_to_trade(doc) for doc in cursor]

    def get_trades_for(self, email: str) -> dict[str, list[dict]]:
        return {
            "incoming": [trade.to_dict() for trade in self._get_incoming_for(email)],
            "outgoing": [trade.to_dict() for trade in self._get_outgoing_for(email)]
        }

    def _find_trade(self, trade_id: str) -> dict | None:
        try:
            return self.trades.find_one({"_id": trade_id})

        except PyMongoError as e:
            raise RuntimeError(f"Failed to query trade '{trade_id}': {e}")

    def _update_trade_status(self, trade_id: str, status: TradeStatus) -> None:
        try:
            result = self.trades.find_one_and_update(
                {"_id": trade_id},
                {"$set": {"status": status.name}},
                return_document=ReturnDocument.AFTER
            )

            if result is None:
                raise ValueError(f"Trade '{trade_id}' does not exist!")

        except PyMongoError as e:
            raise RuntimeError(f"Failed to update trade '{trade_id}': {e}")

    def _dict_to_trade(self, data: dict) -> Trade:
        return Trade(
            sender_email=data["sender_email"],
            receiver_email=data["receiver_email"],
            offered_game=data["offered_game"],
            requested_game=data["requested_game"],
            status=TradeStatus[data["status"]],
            id=data["_id"]
        )


