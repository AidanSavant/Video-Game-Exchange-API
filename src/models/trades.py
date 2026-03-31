import json
import typing
from logging import Logger
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from pymongo import MongoClient, ReturnDocument

import redis

from .users import Users
from .trade import Trade, TradeStatus

# NOTE: [AI CITATION] Redis caching layer was implemented with help from Claude Code
class Trades:
    MONGO_URI: typing.Final[str] = "mongodb://mongo:27017"
    REDIS_HOST: typing.Final[str] = "redis"
    CACHE_TTL: typing.Final[int] = 120

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

        client: MongoClient = MongoClient(self.MONGO_URI)
        self.trades: Collection = client["video_game_exchange"]["trades"]

        self.cache: redis.Redis = redis.Redis(host=self.REDIS_HOST, port=6379, decode_responses=True)

    def _trades_cache_key(self, email: str) -> str:
        return f"trades:{email}"

    def _invalidate_trades_cache(self, sender_email: str, receiver_email: str) -> None:
        self.cache.delete(self._trades_cache_key(sender_email))
        self.cache.delete(self._trades_cache_key(receiver_email))

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
            self._invalidate_trades_cache(trade.sender_email, trade.receiver_email)
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
        self._invalidate_trades_cache(trade.sender_email, trade.receiver_email)

    def reject_trade(self, trade_id: str) -> None:
        trade = self.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Trade '{trade_id}' does not exist!")

        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"Trade '{trade_id}' is not pending!")

        self._update_trade_status(trade_id, TradeStatus.REJECTED)
        self._invalidate_trades_cache(trade.sender_email, trade.receiver_email)

    def _get_incoming_for(self, email: str) -> list[Trade]:
        cursor = self.trades.find({"receiver_email": email})
        return [self._dict_to_trade(doc) for doc in cursor]

    def _get_outgoing_for(self, email: str) -> list[Trade]:
        cursor = self.trades.find({"sender_email": email})
        return [self._dict_to_trade(doc) for doc in cursor]

    def get_trades_for(self, email: str) -> dict[str, list[dict]]:
        cache_key: str = self._trades_cache_key(email)
        try:
            cached: str | None = self.cache.get(cache_key)
            if cached is not None:
                self.logger.info(f"Cache HIT for trades of '{email}'")
                return json.loads(cached)
        except redis.RedisError:
            self.logger.warning(f"Redis unavailable, falling back to MongoDB for trades of '{email}'")

        result: dict = {
            "incoming": [trade.to_dict() for trade in self._get_incoming_for(email)],
            "outgoing": [trade.to_dict() for trade in self._get_outgoing_for(email)]
        }

        try:
            self.cache.setex(cache_key, self.CACHE_TTL, json.dumps(result))
            self.logger.info(f"Cache MISS for trades of '{email}', cached result")
        except redis.RedisError:
            self.logger.warning(f"Failed to cache trades for '{email}'")

        return result

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


