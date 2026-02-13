class Game:
    def __init__(
        self,
        name: str,
        publisher: str,
        year: int,
        platform: str,
        condition: str
    ) -> None:
        self.name: str      = name
        self.publisher: str = publisher
        self.year: int      = year
        self.platform: str  = platform
        self.condition: str = condition


    def to_dict(self) -> dict[str, str | dict]:
        return {
            "name"      : self.name,
            "publisher" : self.publisher,
            "year"      : str(self.year),
            "platform"  : self.platform,
            "condition" : self.condition
        }

    @staticmethod
    def from_dict(name: str, game: dict[str, str | int]):
        return Game(
            name=name,
            publisher=str(game["publisher"]),
            year=int(game["year"]),
            platform=str(game["platform"]),
            condition=str(game["condition"])
        )

