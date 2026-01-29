import jwt

from src.models.user import User
from src.models.users import Users

from typing import Any
from datetime import datetime, timedelta

class UserAuth:
    SECRET_KEY = "secret_jwt_key123321!"

    def __init__(self, users: Users) -> None:
        self.users: Users = users

    def register(
        self,
        name: str,
        email: str,
        password: str,
        street_address: str
    ) -> None:
        user = User(
            name=name,
            email=email,
            password=password,
            street_address=street_address,
            games={}
        )

        self.users.add_user(user)

    def auth(self, email: str, password: str) -> str:
        user: User | None = self.users.get_user(email)
        if not user or user.password != password:
            raise ValueError("Failed to authenticate user! Invalid credentials!")

        return self._create_jwt(user)

    def _create_jwt(self, user: User) -> str:
        payload: dict[str, str | datetime] = {
            "sub": user.email,
            "exp": datetime.utcnow() + timedelta(minutes=9999999)
        }

        return jwt.encode(payload, self.SECRET_KEY, algorithm="HS256")

    def verify_jwt(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
