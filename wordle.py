import collections
import dataclasses
import sqlite3
import textwrap

import databases
import toml

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)

@dataclasses.dataclass
class Guess:
    guess: str

@dataclasses.dataclass
class User:
    username: str
    password: str
    
@dataclasses.dataclass
class Guess:
    Guess: str

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.route("/", methods =["GET"])
def index():
    return textwrap.dedent(
        """
        <h1>Wordle Game </h1>
        <p>A prototype API used to play multiple instances of the popular online game Wordle.</p>\n
        """
    )    

@app.route("/login", methods=["GET"])
async def login():
    db = await _get_db()
    await check_user(db, request.authorization)
    success_response = {"authenticated": True}
    return success_response, 200

@app.route("/users", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)

    try:
        await db.execute(
            """
                INSERT INTO users(name, password) values (:username, :password)
            """,
            user
        )

    except sqlite3.IntegrityError as e:
        abort(409, e)

    return {"Message": "User Successfully Created. Please create a game"}, 201

@app.route("/games/<int:gameID>", methods=["POST"])
@validate_request(Guess)
async def create_guess(data, gameID):
    db = await _get_db()
    guess = data
    try: 
        await db.execute(
        """
            UPDATE games SET guessesMade = guessesMade + 1 WHERE gameID = :gameID", VALUES (:gameID)
        """,
            gameID
        )
    except sqlite3.IntegrityError as e:
            abort(409, e)     

    game = dict(await db.fetch_one("SELECT * FROM games WHERE gameID = :gameID", values={"gameID": gameID}))
    if validate_input(guess, db):
        try: 
            await db.execute(
            """
                INSERT INTO guesses(guess), values (:guess, :guessNumber)
            """,
            guess, game.guessesMade
        )
        except sqlite3.IntegrityError as e:
            abort(409, e)    
        wordle(guess,game)

def wordle(guess, game):

    if guess == game.secretWord:
        #change inprogress to finished table, set is winner to true
    elif game.guessesMade == 6:
        #change inprogress to finished table
    result = []
    count = 0
    for char in guess:
        if char == game.secretWord[count]:
            result[count] = 2
        elif char in game.secretWord:
            result[count] = 1
        else:
            result[count] = 0
        count += 1
    print (result)

async def validate_input(guess, db):
    if len(guess) != 5:
        print("Error: Expected 5 letter word")
        return False   
    if not await db.fetch_one("SELECT * FROM validGuesses WHERE word=(?)", (guess,)) is None:
        print("Error: Please enter a valid word")
        return False
    return True

async def check_user(db, auth):
    if auth is not None:
        print(auth.type + auth.username + auth.password)

    if auth is not None and auth.type == 'basic':
        result = await db.fetch_one("SELECT userID FROM users where name = :username and password =:password",
                                    values={"username": auth.username, "password": auth.password})
        print('inside auth')
        app.logger.debug(type(result))
        if result:
            return result.userID
        else:
            print('inside abort')
            abort(401)
    else:
        abort(401)


