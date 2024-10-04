from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Union, Optional
from bson import ObjectId
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize FastAPI
app = FastAPI()

# MongoDB Connection Configuration

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]

MONGO_DETAILS = os.environ["MONGO_DETAILS"]
DATABEASE = os.environ["DATABEASE"]

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client[DATABEASE]

# Define collections for users and games
users_collection = db["user"]
games_collection = db["game"]

# CORS Middleware (Optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 for Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper class to validate ObjectId (MongoDB _id)
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# User Models
class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


# Game Models
class Game(BaseModel):
    _id: Union[PyObjectId, None] = None
    id: Union[str, None] = None
    bopsPromoCalloutSearchTile: Optional[str] = None
    bopsPromoCalloutSearchTileAlternate: Optional[str] = None
    price: Optional[dict] = None
    bopsPromoAlternate: Optional[str] = None
    image: Optional[dict] = None
    marketPrice: Optional[float] = None
    releaseDate: Optional[str] = None
    ratings: Optional[dict] = None
    availability: Optional[dict] = None
    url: Optional[str] = None
    name: str
    productPlatform: Optional[list] = None
    providerGrade: Optional[str] = None
    mapProPrice: Optional[float] = None
    badge: Optional[str] = None
    gradingProvider: Optional[str] = None


class UpdateGameModel(BaseModel):
    id: Union[str, None] = None
    bopsPromoCalloutSearchTile: Optional[str] = None
    bopsPromoCalloutSearchTileAlternate: Optional[str] = None
    price: Optional[dict] = None
    bopsPromoAlternate: Optional[str] = None
    image: Optional[dict] = None
    marketPrice: Optional[float] = None
    releaseDate: Optional[str] = None
    ratings: Optional[dict] = None
    availability: Optional[dict] = None
    url: Optional[str] = None
    name: Optional[str] = None
    productPlatform: Optional[list] = None
    providerGrade: Optional[str] = None
    mapProPrice: Optional[float] = None
    badge: Optional[str] = None
    gradingProvider: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


# Helper Functions for Passwords
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# User Authentication and Database Interactions
async def authenticate_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return UserInDB(**user)


async def get_user(username: str):
    user = await users_collection.find_one({"username": username})
    if user:
        return UserInDB(**user)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# User Routes
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# Game Routes
@app.post("/games/", response_model=Game, status_code=201)
async def create_game(game: Game):
    game_dict = game.dict()
    game_dict["_id"] = PyObjectId()
    new_game = await games_collection.insert_one(game_dict)
    created_game = await games_collection.find_one({"_id": new_game.inserted_id})
    return created_game


@app.get("/games/", response_model=List[Game])
async def list_games(
    limit: Optional[int] = Query(None, description="Limit the number of games returned"),
    sort_by: Optional[str] = Query(None, description="Sort by 'price', 'name', or 'ratings'"),
    sort_order: Optional[str] = Query("asc", description="Sort order: 'asc' for ascending or 'desc' for descending")
):
    # Create sort dictionary based on the sort_by parameter
    sort_dict = []
    if sort_by == "price":
        sort_dict = [("price.base", 1 if sort_order == "asc" else -1)]
    elif sort_by == "name":
        sort_dict = [("name", 1 if sort_order == "asc" else -1)]
    elif sort_by == "ratings":
        sort_dict = [("ratings.percentage", -1 if sort_order == "asc" else 1)]  # Reverse for ratings

    # Use default sorting if no sort_by parameter is provided
    if not sort_dict:
        # Optionally set a default sort, e.g., by name in ascending order
        sort_dict = [("_id", 1)]

    games = []
    async for game in games_collection.find().sort(sort_dict).limit(limit or 0):
        games.append(Game(**game))
    
    return games



@app.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    if not ObjectId.is_valid(game_id):
        raise HTTPException(status_code=400, detail="Invalid game ID")
    game = await games_collection.find_one({"_id": ObjectId(game_id)})
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.put("/games/{game_id}", response_model=Game)
async def update_game(game_id: str, game: UpdateGameModel):
    if not ObjectId.is_valid(game_id):
        raise HTTPException(status_code=400, detail="Invalid game ID")
    update_data = {k: v for k, v in game.dict().items() if v is not None}
    if update_data:
        await games_collection.update_one({"_id": ObjectId(game_id)}, {"$set": update_data})
    updated_game = await games_collection.find_one({"_id": ObjectId(game_id)})
    if updated_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return updated_game


@app.delete("/games/{game_id}")
async def delete_game(game_id: str):
    if not ObjectId.is_valid(game_id):
        raise HTTPException(status_code=400, detail="Invalid game ID")
    result = await games_collection.delete_one({"_id": ObjectId(game_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"message": "Game deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
