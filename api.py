from typing import Dict, Any

from users import Users
from user import User, Game
from user_auth import UserAuth

from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
bearer = HTTPBearer()

users = Users()
auth_service = UserAuth(users)

def auth_middleware(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> User:
    jwt: str = credentials.credentials

    try:
        jwt_payload: Dict[str, Any] = auth_service.verify_jwt(jwt)

        user: User | None = auth_service.users.get_user(jwt_payload["sub"])
        if not user:
            raise HTTPException(
                status_code=409,
                detail="Failed to auth user! User does not exist!"
            )

        return user

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Failed to auth user! Invalid JWT!"
        )

# === User API === #
# NOTE: Could have a table/list of endpoints to not hardcode API endpoints

@app.post("/api/register")
def register(reg_body: Dict[str, str]) -> Dict[str, bool]:
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

    return JSONResponse(
        content={
            "links": {
                "next" : "/api/login",
            }
        },
        status_code=201
    )

@app.post("/api/login")
def login(user: Dict[str, str]) -> Dict[str, str]:
    try:
        jwt: str = auth_service.auth(user["email"], user["password"])
        return { "jwt" : jwt }

    except ValueError as e:
        detail: str = str(e)
        raise HTTPException(status_code=401, detail=detail)

@app.get("/api/self")
def get_self(authed_user: User = Depends(auth_middleware)) -> Dict[str, str | dict]:
    return {
        "name": authed_user.name,
        "email": authed_user.email,
        "street_address": authed_user.street_address,
        "games" : {
            name: game.to_dict()
            for name, game in authed_user.games.items()
        },
        "links" : {
            "update_self" : { 
                "endpoint": "/api/self",
                "method"  : "PUT"
             }
        }
    }

@app.put("/api/self")
def update_self(
    update_body: Dict[str, str], 
    user: User = Depends(auth_middleware)
) -> Dict[str, bool]:
    try:
        users.update_user(
            email=user.email,
            name=update_body.get("name"),
            street_address=update_body.get("street_address")
        )
    
    except Exception:
        raise HTTPException(status_code=404, detail="Failed to find game!")

    return JSONResponse(
        content={
            "links" : {
                "read_self" : {
                    "endpoint" : "/api/self",
                    "method"   : "GET"
                }
            }  
        },
        status_code=200
    )

# === Game API === #

@app.post("/api/games")
def add_game(
    game_body: Dict[str, str | int],
    authed_user: User = Depends(auth_middleware)
) -> Dict[str, bool]:
    try:
        game: Game = Game(
            name=str(game_body["name"]),
            publisher=str(game_body["publisher"]),
            year=int(game_body["year"]),
            platform=str(game_body["platform"]),
            condition=str(game_body["condition"])
        )

        users.add_game(authed_user.email, game)

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return JSONResponse(
        content={
            "links" : {
                "get_game" : {
                    "endpoint" : "/api/games/{game_name}",
                    "method"   : "GET"
                }
            }
        },
        status_code=201
    )

@app.get("/api/games/{game_name}")
def get_game(
    game_name: str,
    authed_user: User = Depends(auth_middleware)
) -> Dict[str, str | dict]:
    game: Game | None = authed_user.get_game(game_name)
    if not game:
        raise HTTPException(status_code=404, detail="Failed to find game!")

    game_json: Dict[str, str | dict] = game.to_dict()
    game_json.update({
        "links" : {
            "add_game" : {
                "endpoint" : "/api/games/",
                "method" : "POST"
            },
            "delete_game" : {
                "endpoint" : "/api/games/{game_name}",
                "method" : "DELETE"
            }
        }                      
    })

    return game_json

@app.put("/api/games/{game_name}")
def update_game(
    game_name: str,
    update_body: dict[str, str], 
    authed_user: User = Depends(auth_middleware)
) -> Dict[str, bool]:
    try:
        users.update_game(
            email=authed_user.email,
            game_name=game_name,
            new_name=update_body.get("name"),
            condition=update_body.get("condition")
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return JSONResponse(
        content={
            "links" : {
                "get_game" : {
                    "endpoint" : "/api/games/{game_name}",
                    "method" : "GET"
                }
            }
        },
        status_code=200
    )

@app.delete("/api/games/{game_name}")
def delete_game(
    game_name: str, 
    authed_user: User = Depends(auth_middleware)
) -> Dict[str, bool]:
    try:
        users.delete_game(email=authed_user.email, game_name=game_name)

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return JSONResponse(
        content={
            "links" : {
                "get_game" : {
                    "endpoint" : "/api/games/{game_name}",
                    "method" : "GET"
                }
            }
        },
        status_code=200
    )

