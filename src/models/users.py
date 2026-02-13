# NOTE: [AI CITATION]: json db -> mongodb migration was mostly written by chatGPT (as I'm not familiar with mongo and need to focus on the main part of this lab)

import typing

from logging import Logger

from .user import User
from .game import Game

from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from pymongo import MongoClient, ReturnDocument

class Users:
    MONGO_URI: typing.Final[str] = "mongodb://mongo:27017"

    def __init__(self, logger: Logger) -> None:
        self.logger = logger

        client: MongoClient = MongoClient(self.MONGO_URI)

        self.users: Collection = client["video_game_exchange"]["users"]

    def add_user(self, user: User) -> None:
        if self._find_user(user.email) is not None:
            raise ValueError(f"User '{user.email}' already exists!")

        self._insert_user(user)

    def get_user(self, email: str) -> User | None:
        user_data: dict | None = self._find_user(email)
        if user_data is None:
            return None

        return self._dict_to_user(user_data)

    def update_user(
        self,
        email: str,
        name: str | None = None,
        password: str | None = None,
        street_address: str | None = None
    ) -> None:
        update_fields: dict = {}

        if name is not None:
            update_fields["name"] = name

        if password is not None:
            update_fields["password"] = password

        if street_address is not None:
            update_fields["street_address"] = street_address

        if update_fields:
            self._update(email, update_fields)

    def add_game(self, email: str, game: Game) -> None:
        self._update(email, {f"games.{game.name}": game.to_dict()})

    def get_game(self, email: str, game_name: str) -> Game | None:
        user_data: dict | None = self._find_user(email)
        if user_data is None:
            raise ValueError(f"User '{email}' does not exist!")

        game_data: dict | None = user_data.get("games", {}).get(game_name)
        if game_data is None:
            return None

        return Game.from_dict(game_name, game_data)

    def update_game(
        self,
        email: str,
        game_name: str,
        new_name: str | None = None,
        condition: str | None = None
    ) -> None:
        user_data: dict | None = self._find_user(email)
        if user_data is None:
            raise ValueError(f"User '{email}' does not exist!")

        game_data: dict | None = user_data.get("games", {}).get(game_name)
        if game_data is None:
            raise ValueError(f"Game '{game_name}' does not exist for user '{email}'!")

        if condition is not None:
            self._update(email, {f"games.{game_name}.condition": condition})

        if new_name is not None:
            self._update(email, {f"games.{game_name}": ""}, unset=True)

            game_data["name"] = new_name
            self._update(email, {f"games.{new_name}": game_data})

    def delete_game(self, email: str, game_name: str) -> None:
        user_data: dict | None = self._find_user(email)
        if user_data is None:
            raise ValueError(f"User '{email}' does not exist!")

        if game_name not in user_data.get("games", {}):
            raise ValueError(f"Game '{game_name}' does not exist for user '{email}'!")

        self._update(email, {f"games.{game_name}": ""}, unset=True)

    def exchange_games(
        self,
        sender_email: str,
        receiver_email: str,
        sender_game_name: str,
        receiver_game_name: str
    ) -> None:
        sender: dict | None = self._find_user(sender_email)
        receiver: dict | None = self._find_user(receiver_email)

        if sender is None:
            raise ValueError(f"Sender '{sender_email}' does not exist!")

        if receiver is None:
            raise ValueError(f"Receiver '{receiver_email}' does not exist!")

        sender_game: dict | None = sender.get("games", {}).get(sender_game_name)
        receiver_game: dict | None = receiver.get("games", {}).get(receiver_game_name)

        if sender_game is None:
            raise ValueError(f"Sender no longer has game '{sender_game_name}'!")

        if receiver_game is None:
            raise ValueError(f"Receiver no longer has game '{receiver_game_name}'!")

        self._update(sender_email, {f"games.{sender_game_name}": ""}, unset=True)
        self._update(receiver_email, {f"games.{receiver_game_name}": ""}, unset=True)

        self._update(sender_email, {f"games.{receiver_game_name}": receiver_game})
        self._update(receiver_email, {f"games.{sender_game_name}": sender_game})

    def _find_user(self, email: str) -> dict | None:
        try:
            return self.users.find_one({"_id": email})

        except PyMongoError as e:
            raise RuntimeError(f"Failed to query user '{email}': {e}")

    def _insert_user(self, user: User) -> None:
        try:
            self.users.insert_one({
                "_id": user.email,
                "name": user.name,
                "email": user.email,
                "password": user.password,
                "street_address": user.street_address,
                "games": {}
            })

        except PyMongoError as e:
            raise RuntimeError(f"Failed to insert user '{user.email}'! Reason: {str(e)}")

    def _update(self, email: str, fields: dict, unset: bool = False) -> dict:
        try:
            update_query: dict = {"$unset" : fields } if unset else {"$set" : fields}
            prev_user_state: dict | None = self.users.find_one_and_update(
                {"_id" : email},
                update_query,
                return_document=ReturnDocument.BEFORE
            )

            if prev_user_state is None:
                raise ValueError(f"User '{email}' does not exist!")

            return prev_user_state

        except PyMongoError as e:
            raise RuntimeError(f"Failed to update user '{email}': {e}")

    def _dict_to_user(self, data: dict) -> User:
        games: dict[str, Game] = {
            title: Game.from_dict(title, g)
            for title, g in data.get("games", {}).items()
        }

        return User(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            street_address=data["street_address"],
            games=games
        )

