import json

from typing import Dict

from .user import User
from .game import Game

class Users:
    DB_PATH = "db/db.json"

    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self._load_users()

    def _load_users(self) -> None:
        with open(self.DB_PATH, 'r') as db_handle:
            user_json: Dict[str, dict] = json.load(db_handle)

        for email, user_data in user_json.items():
            games: Dict[str, Game] = {
                title: Game.from_dict(title, game)
                for title, game in user_data["games"].items()
            }

            self.users[email] = User(
                name=user_data["name"],
                email=email,
                password=user_data["password"],
                street_address=user_data["street_address"],
                games=games
            )

    def _save_users(self) -> None:
        user_data: Dict[str, dict] = {}
        for email, user in self.users.items():
            user_data[email] = {
                "name"     : user.name,
                "email"    : user.email,
                "password" : user.password,
                "street_address" : user.street_address,
                "games" : { 
                    title: game.to_dict()
                    for title, game in user.games.items()
                }
            }

        with open(self.DB_PATH, 'w') as db_handle:
            json.dump(user_data, db_handle, indent=4)

    def add_user(self, user: User) -> None:
        if user.email in self.users:
            raise ValueError(f"User '{user.email}' already exists!")

        self.users[user.email] = user
        self._save_users()

    def get_user(self, email: str) -> User | None:
        return self.users.get(email)

    def update_user(
        self,
        email: str,
        name: str | None = None,
        street_address: str | None = None
    ) -> None:
        user: User | None = self.get_user(email)
        if user is None:
            raise ValueError("Failed to find user!")

        user.update_user(name, street_address)
        self._save_users()

    def add_game(self, email: str, game: Game) -> None:
        user: User | None = self.get_user(email)
        if user is None:
            raise ValueError("Failed to find user!")

        user.add_game(game)
        self._save_users()

    def get_game(self, email: str, game_name: str) -> Game | None:
        user: User | None = self.get_user(email)
        if user is None:
            raise ValueError("Failed to find user!")

        return user.get_game(game_name)

    def update_game(
        self,
        email: str,
        game_name: str,
        new_name: str | None = None,
        condition: str | None = None
    ) -> None:
        user: User | None = self.get_user(email)
        if user is None:
            raise ValueError("Failed to find user!")

        user.update_game(game_name, new_name, condition)
        self._save_users()

    def delete_game(self, email: str, game_name: str) -> None:
        user: User | None = self.get_user(email)
        if user is None:
            raise ValueError("Failed to find user!")

        user.delete_game(game_name)
        self._save_users()

    def exchange_games(
        self,
        sender_email: str,
        receiver_email: str,
        sender_game_name: str,
        receiver_game_name: str
    ) -> None:
        sender:   User | None = self.get_user(sender_email)
        receiver: User | None = self.get_user(receiver_email)

        if sender is None:
            raise ValueError(f"Sender '{sender_email}' does not exist!")

        if receiver is None:
            raise ValueError(f"Receiver '{receiver_email}' does not exist!")

        sender_game:   Game | None = sender.get_game(sender_game_name)
        receiver_game: Game | None = receiver.get_game(receiver_game_name)

        if sender_game is None:
            raise ValueError(f"Sender no longer has game '{sender_game_name}'!")

        if receiver_game is None:
            raise ValueError(f"Receiver no longer has game '{receiver_game_name}'!")

        sender.delete_game(sender_game_name)
        receiver.delete_game(receiver_game_name)

        sender.add_game(receiver_game)
        receiver.add_game(sender_game)

        self._save_users()
