from typing import Dict

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


    def to_dict(self) -> Dict[str, str | dict]:
        return {
            "name"      : self.name,
            "publisher" : self.publisher,
            "year"      : str(self.year),
            "platform"  : self.platform,
            "condition" : self.condition
        }

    @staticmethod
    def from_dict(name: str, game: Dict[str, str | int]):
        return Game(
            name=name,
            publisher=str(game["publisher"]),
            year=int(game["year"]),
            platform=str(game["platform"]),
            condition=str(game["condition"])
        )

class User:
    def __init__(
        self, 
        name: str,
        email: str,
        password: str,
        street_address: str,
        games: Dict[str, Game] = {}
    ) -> None:
        self.name: str  = name
        self.email: str = email
        self.password: str = password
        self.street_address: str = street_address
        self.games: Dict[str, Game] = games

    def update_user(
        self,
        name: str | None, 
        street_address: str | None
    ) -> None:
        if name:
            self.name = name

        if street_address:
            self.street_address = street_address

    def add_game(self, game: Game) -> None:
        if self.has_game(game.name):
            return

        self.games[game.name] = game

    def get_game(self, name: str) -> Game | None:
        return self.games.get(name)

    def update_game(
        self, 
        name: str, 
        new_name:  str | None = None,
        condition: str | None = None
    ) -> None:
        game: Game | None = self.get_game(name)
        if not game:
            return

        if new_name and new_name != name:
            if self.has_game(new_name):
                raise ValueError("Game with new name already exists!")

            del self.games[name]

            game.name = new_name
            self.games[new_name] = game

        if condition:
            game.condition = condition

    def delete_game(self, name: str) -> None:
        if self.has_game(name):
            del self.games[name]

    def has_game(self, name: str) -> bool:
        return name in self.games.keys()

