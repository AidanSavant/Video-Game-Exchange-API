import logging

from typing import Any

from src.models.users import Users
from src.models.user  import User, Game

from src.models.trade  import Trade
from src.models.trades import Trades

from src.middleware.user_auth import UserAuth

from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# === Application initialization === #

app: FastAPI = FastAPI()
bearer: HTTPBearer = HTTPBearer()

users: Users = Users()
trades: Trades = Trades()
auth_service: UserAuth = UserAuth(users)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="api_logs.log",
    filemode='a'
)

# NOTE: Got logging setup help from chatGPT / stackoverflow

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("api_logs.log", mode='a')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
# NOTE: Partially generated with claude code

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

        logging.info(f"User '{user.email}' successfully registered!")

        return JSONResponse(
            content={
                "links": _new_hateos_link(("login", "/api/login", "POST"))
            },
            status_code=201
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logging.error(f"User '{user.email}' failed to register! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
def login(user: dict[str, str]) -> JSONResponse:
    try:
        jwt: str = auth_service.auth(user["email"], user["password"])

        logging.info(f"User '{user['email']}' successfully logged in!")

        return JSONResponse(
            content={
                "jwt" : jwt,
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
            status_code=201
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
    user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        users.update_user(
            email=user.email,
            name=update_body.get("name"),
            street_address=update_body.get("street_address")
        )

        logging.info(f"Successfully updated user '{user.email}'!")

        return JSONResponse(
            content={
                "links": _new_hateos_link(("read_self", "/api/self", "GET"))
            },
            status_code=200
        )

    except ValueError as e:
        logging.error(f"Failed to update user '{user.email}'! Reason: {str(e)}")
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

        users.add_game(authed_user.email, game)

        logging.info(f"Successfully added game '{game.name}' to user '{authed_user.email}'s games!")

        return JSONResponse(
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
            status_code=201
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
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
            status_code=200
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
            content={
                "links": _new_hateos_link(("get_game", "/api/games/{game_name}", "GET"))
            },
            status_code=200
        )

    except ValueError as e:
        logger.error(f"Failed to delete game '{game_name}' for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/trades")
def trade_game(
    trade_body: dict[str, str],
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    def _validate_request_body(
        sender: User, 
        receiver: str, 
        offered_game: str, 
        requested_game: str
    ) -> None:
        receiver_user: User | None = users.get_user(receiver)
        if receiver_user is None:
            raise ValueError(f"Receiver '{receiver}' does not exist!")

        if receiver_user.get_game(requested_game) is None:
            raise ValueError(f"User '{receiver}' does not have requested game '{requested_game}'!")
        
        if sender.get_game(offered_game) is None:
            raise ValueError(f"User '{sender.email}' does not have offered game '{offered_game}'!")
        
        if receiver == sender.email:
            raise ValueError("Cannot trade games with yourself!")
        
        if offered_game == requested_game:
            raise ValueError("Offered game and requested game cannot be the same!")

    try:
        sender: str = authed_user.email
        receiver: str = trade_body["receiver"]

        offered_game: str = trade_body["offered_game"]
        requested_game: str = trade_body["requested_game"]

        _validate_request_body(authed_user, receiver, offered_game, requested_game)

        trade: Trade = Trade(
            sender=sender,
            receiver=receiver,
            offered_game=offered_game,
            requested_game=requested_game,
        )

        trades.add_trade(trade)
        logger.info(f"Trade request from {sender} to {receiver} successfully created!")

        return JSONResponse(
            content={
                "trade_id" : trade.id,
                "links": _new_hateos_link(
                    ("accept_trade", "/api/trades/accept/{trade_id}", "POST"),
                    ("reject_trade", "/api/trades/reject/{trade_id}", "POST")
                )
            },
            status_code=201
        )

    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"{e.args[0]} field is required in request body!"
        )

    except ValueError as e:
        logger.error(f"Failed to initiate request between {sender} and {receiver}! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trades")
def get_trades(
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    return JSONResponse(
        content={
            "trades": trades.get_trades_for(authed_user.email),
            "links": _new_hateos_link(("get_self", "/api/self", "GET"))
        },
        status_code=200
    )

@app.post("/api/trades/accept/{trade_id}")
def accept_trade(
    trade_id: str,
    authed_user: User = Depends(auth_middleware)
) -> JSONResponse:
    try:
        trade = trades.get_trade(trade_id)
        if trade is None:
            raise Exception("Trade does not exist!")
        
        if trade.receiver != authed_user.email:
            raise Exception("User is not authorized to accept this trade!")
        
        trades.accept_trade(trade_id, users)
        logger.info(f"User '{authed_user.email}' successfully accepted trade '{trade_id}'!")

        return JSONResponse(
            content={
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
            status_code=200
        )

    except ValueError as e:
        logger.error(f"Failed to accept trade for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trades/reject/{trade_id}")
def reject_trade(
    trade_id: str,
    authed_user: User = Depends(auth_middleware)
)-> JSONResponse:
    try:
        trade = trades.get_trade(trade_id)
        if trade is None:
            raise ValueError("Trade does not exist!")
        
        if trade.receiver != authed_user.email:
            raise ValueError("User is not authorized to reject this trade!")
        
        trades.reject_trade(trade_id)
        logging.info(f"User '{authed_user.email}' successfully rejected trade '{trade_id}'!")

        return JSONResponse(
            content={
                "links": _new_hateos_link(("get_self", "/api/self", "GET"))
            },
            status_code=200
        )

    except ValueError as e:
        logger.error(f"Failed to reject trade for user '{authed_user.email}'! Reason: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
