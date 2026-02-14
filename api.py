import logging
from typing import Any

# === Internal models and middleware(s) imports === #

from src.models.users import Users
from src.models.user  import User, Game

from src.models.trade  import Trade
from src.models.trades import Trades

from src.middleware.user_auth import UserAuth

from src.models.email_notif_producer import EmailNotifProducer

# === FastAPI imports === #

from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# === Logging initialization === #

# NOTE: [AI CITATION]: Logging setup help from chatGPT / stackoverflow
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="api.logs",
    filemode='a'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# === Application initialization setup === #

app: FastAPI = FastAPI()
bearer: HTTPBearer = HTTPBearer()

trades: Trades = Trades(logger)
users: Users = Users(logger)

auth_service: UserAuth = UserAuth(users)

email_notif_producer: EmailNotifProducer = EmailNotifProducer(users, trades)

# === Authentication === #

def auth_middleware(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> User | None:
    jwt: str = credentials.credentials

    try:
        jwt_payload: dict[str, Any] = auth_service.verify_jwt(jwt)

        user: User | None = auth_service.users.get_user(jwt_payload["sub"])
        if user is None:
            raise HTTPException(
                status_code=409,
                detail="Failed to auth user! User does not exist!"
            )

        return user

    except Exception:
        raise HTTPException(status_code=401, detail="Failed to auth user! Invalid JWT!")

# === User API === #
# NOTE: [AI CITATION] Partially generated with claude code

def _new_hateos_link(*link_info: tuple[str, str, str]) -> dict[str, dict[str, str]]:
    return {
        name: {"endpoint": endpoint, "method": method}
        for name, endpoint, method in link_info
    }

@app.post("/api/register")
def register(reg_body: dict[str, str]) -> JSONResponse:
    try:
        email: str = reg_body["email"]
        if users.get_user(email):
            raise HTTPException(
                status_code=400,
                detail="Email already registered!"
            )

        user: User = User(
            name=reg_body["name"],
            email=email,
            password=reg_body["password"],
            street_address=reg_body["street_address"],
        )

        users.add_user(user)
        user_email: str = user.email

        logging.info(f"User '{user_email}' successfully registered!")

        return JSONResponse(
            status_code=201,
            content={
                "links": _new_hateos_link(("login", "/api/login", "POST"))
            },
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logging.error(f"User '{user_email}' failed to register! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
def login(user: dict[str, str]) -> JSONResponse:
    # NOTE: Would definitely be better to have setting auth token in the cookies directly

    try:
        jwt: str = auth_service.auth(user["email"], user["password"])
        logging.info(f"User '{user['email']}' successfully logged in!")

        return JSONResponse(
            status_code=201,
            content={
                "jwt" : jwt,
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logging.error(f"User '{user['email']}' failed to login! Reason: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/self")
def get_self(authed_user: User = Depends(auth_middleware)) -> dict[str, str | dict]:
    return {
        "name": authed_user.name,
        "email": authed_user.email,
        "password" : authed_user.password,
        "street_address": authed_user.street_address,
        "games" : {
            name: game.to_dict()
            for name, game in authed_user.games.items()
        },
        "links": _new_hateos_link(("update_self", "/api/self", "PUT"))
    }

@app.put("/api/self")
def update_self(
    update_body: dict[str, str],
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        email: str = authed_user.email

        old_name: str = authed_user.name
        old_password: str = authed_user.password

        new_name: str | None = update_body.get("name")
        new_password: str | None = update_body.get("password")
        new_street_address: str | None = update_body.get("street_address")

        users.update_user(
            email=email,
            name=new_name,
            password=new_password,
            street_address=new_street_address
        )

        if new_password is not None:
            email_notif_producer.send_pw_update_notif(
                name=old_name,
                auth_combo=(email, old_password)
            )

        logging.info(f"Successfully updated user '{email}'!")

        return JSONResponse(
            status_code=200,
            content={
                "links": _new_hateos_link(("read_self", "/api/self", "GET"))
            },
        )

    except ValueError as e:
        logging.error(f"Failed to update user '{email}'! Reason: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

# === Game API === #

@app.post("/api/games")
def add_game(
    game_body: dict[str, str | int],
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        game: Game = Game(
            name=str(game_body["name"]),
            publisher=str(game_body["publisher"]),
            year=int(game_body["year"]),
            platform=str(game_body["platform"]),
            condition=str(game_body["condition"])
        )

        email: str = authed_user.email
        users.add_game(email, game)

        logging.info(f"Successfully added game '{game.name}' to user '{email}'s games!")

        return JSONResponse(
            status_code=201,
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logging.error(f"Failed to add game '{game_body['name']}' to {authed_user.email}'s games! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/games/{game_name}")
def get_game(
    game_name: str,
    authed_user: User = Depends(auth_middleware)
) -> dict[str, str | dict]:
    game: Game | None = authed_user.get_game(game_name)
    if game is None:
        raise HTTPException(status_code=404, detail="Failed to find game!")

    game_json: dict[str, str | dict] = game.to_dict()
    game_json.update({
        "links": _new_hateos_link(
            ("add_game", "/api/games/", "POST"),
            ("delete_game", "/api/games/{game_name}", "DELETE")
        )
    })

    return game_json

@app.put("/api/games/{game_name}")
def update_game(
    game_name: str,
    update_body: dict[str, str], 
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        users.update_game(
            email=authed_user.email,
            game_name=game_name,
            new_name=update_body.get("name"),
            condition=update_body.get("condition")
        )
        return JSONResponse(
            status_code=200,
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
        )

    except ValueError as e:
        logger.error(f"Failed to update game for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/games/{game_name}")
def delete_game(
    game_name: str,
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        users.delete_game(email=authed_user.email, game_name=game_name)
        logging.info(f"Successfully deleted game '{game_name}' from user '{authed_user.email}'s games!")

        return JSONResponse(
            status_code=200,
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
        )

    except ValueError as e:
        logger.error(f"Failed to delete game '{game_name}' for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/trades")
def init_trade_offer(
    trade_body: dict[str, str],
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    def _validate_trade_body(
        sender: User,
        receiver_email: str,
        offered_game: str,
        requested_game: str
    ) -> None:
        receiver: User | None = users.get_user(receiver_email)
        if receiver is None:
            raise ValueError(f"Receiver '{receiver}' does not exist!")

        if receiver.get_game(requested_game) is None:
            raise ValueError(f"User '{receiver}' does not have requested game '{requested_game}'!")

        if sender.get_game(offered_game) is None:
            raise ValueError(f"User '{sender.email}' does not have offered game '{offered_game}'!")

        if receiver == sender.email:
            raise ValueError("Cannot trade games with yourself!")

        if offered_game == requested_game:
            raise ValueError("Offered game and requested game cannot be the same!")

    try:
        sender_email: str = authed_user.email
        receiver_email: str = trade_body["receiver"]

        offered_game: str = trade_body["offered_game"]
        requested_game: str = trade_body["requested_game"]

        _validate_trade_body(authed_user, receiver_email, offered_game, requested_game)

        trade: Trade = Trade(
            sender_email=sender_email,
            receiver_email=receiver_email,
            offered_game=offered_game,
            requested_game=requested_game,
        )

        trade_id: str = trades.add_trade(trade)
        email_notif_producer.send_trade_offer_notif(trade_id=trade_id)

        logger.info(f"Trade request from {sender_email} to {receiver_email} successfully created!")

        return JSONResponse(
            status_code=201,
            content={
                "trade_id" : trade_id,
                "links": _new_hateos_link(
                    ("accept_trade", "/api/trades/accept/{trade_id}", "POST"),
                    ("reject_trade", "/api/trades/reject/{trade_id}", "POST")
                )
            },
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logger.error(f"Failed to initiate request between {sender_email} and {receiver_email}! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trades")
def get_trades(
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "trades": trades.get_trades_for(authed_user.email),
            "links": _new_hateos_link(("get_self", "/api/self", "GET"))
        },
    )

@app.post("/api/trades/accept/{trade_id}")
def accept_trade_offer(
    trade_id: str,
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        trade: Trade | None = trades.get_trade(trade_id)
        if trade is None:
            raise Exception("Trade does not exist!")

        email: str = authed_user.email
        if trade.receiver_email != email:
            raise Exception("User is not authorized to accept this trade!")

        trades.accept_trade(trade_id, users)
        email_notif_producer.send_trade_accepted_notif(trade_id=trade_id)

        logger.info(f"User '{email}' successfully accepted trade '{trade_id}'!")

        return JSONResponse(
            status_code=200,
            content={
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
        )

    except ValueError as e:
        logger.error(f"Failed to accept trade for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trades/reject/{trade_id}")
def reject_trade_offer(
    trade_id: str,
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        trade: Trade | None = trades.get_trade(trade_id)
        if trade is None:
            raise ValueError("Trade does not exist!")

        email: str = authed_user.email
        if trade.receiver_email != email:
            raise ValueError("User is not authorized to reject this trade!")

        trades.reject_trade(trade_id)

        email_notif_producer.send_trade_rejected_notif(trade_id=trade_id)

        logging.info(f"User '{email}' successfully rejected trade '{trade_id}'!")

        return JSONResponse(
            status_code=200,
            content={
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
        )

    except ValueError as e:
        logger.error(f"Failed to reject trade for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

