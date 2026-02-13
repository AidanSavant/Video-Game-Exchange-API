from .game import Game

class User:
    def __init__(
        self, 
        name: str,
        email: str,
        password: str,
        street_address: str,
        games: dict[str, Game] = {},
    ) -> None:
        self.name: str = name
        self.email: str = email
        self.password: str = password
        self.street_address: str = street_address
        self.games: dict[str, Game] = games

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
            raise ValueError(f"Game '{game.name}' already exists!")

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
        if game is None:
            raise ValueError(f"Game '{name}' does not exist!")

        if new_name and new_name != name:
            if self.has_game(new_name):
                raise ValueError(f"Game '{new_name}' already exists!")

            del self.games[name]

            game.name = new_name
            self.games[new_name] = game

        if condition:
            game.condition = condition

    def delete_game(self, name: str) -> None:
        if not self.has_game(name):
            raise ValueError(f"Game '{name}' does not exist!")

        del self.games[name]

    def has_game(self, name: str) -> bool:
        return name in self.games.keys()

