import uuid

from enum import Enum, auto
from dataclasses import dataclass, field

class TradeStatus(Enum):
    PENDING = auto()
    ACCEPTED = auto()
    REJECTED = auto()

@dataclass
class Trade:
    sender: str
    receiver: str

    offered_game: str
    requested_game: str

    status: TradeStatus = TradeStatus.PENDING

    # NOTE: Only needs to be initialize upon first contruction
    # of Trade. No need to create a ctor, just a default factory
    id: str = field(default_factory=lambda: str(uuid.uuid1()))

    def to_dict(self) -> dict[str, str]:
        return {
            "id"             : self.id,
            "sender"         : self.sender,
            "receiver"       : self.receiver,
            "status"         : self.status.name,
            "offered_game"   : self.offered_game,
            "requested_game" : self.requested_game,
        }

