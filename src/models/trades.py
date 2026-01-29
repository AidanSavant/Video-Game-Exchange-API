from .users import Users
from .trade import Trade, TradeStatus

"""
NOTE:I did use chatGPT to update my original (bad) idea of storing 
incoming/outgoing trade requests in theuser itself, but chatGPT 
recommended that I store this separately. Which I now agree with.
"""

class Trades:
    def __init__(self) -> None:
        self._trades: dict[str, Trade] = {}

    def add_trade(self, trade: Trade) -> None:
        self._trades[trade.id] = trade

    def get_trade(self, trade_id: str) -> Trade | None:
        return self._trades.get(trade_id)

    def accept_trade(self, trade_id: str, users: Users) -> None:
        trade: Trade | None = self.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Trade '{trade_id}' does not exist!")

        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"Trade '{trade_id}' is not pending!")

        users.exchange_games(
            sender_email=trade.sender,
            receiver_email=trade.receiver,
            sender_game_name=trade.offered_game,
            receiver_game_name=trade.requested_game
        )

        trade.status = TradeStatus.ACCEPTED

    def reject_trade(self, trade_id: str) -> None:
        trade: Trade | None = self.get_trade(trade_id)
        if trade is None:
            raise ValueError(f"Trade '{trade_id}' does not exist!")

        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"Trade '{trade_id}' is not pending!")

        trade.status = TradeStatus.REJECTED

    def _get_incoming_for(self, email: str) -> list[Trade]:
        return [
            trade for trade in self._trades.values()
            if email == trade.receiver
        ]
    
    def _get_outgoing_for(self, email: str) -> list[Trade]:
        return [
            trade for trade in self._trades.values()
            if email == trade.sender
        ]

    def get_trades_for(self, email: str) -> dict[str, list[dict]]:
        return {
            "incoming": [trade.to_dict() for trade in self._get_incoming_for(email)],
            "outgoing": [trade.to_dict() for trade in self._get_outgoing_for(email)]
        }
