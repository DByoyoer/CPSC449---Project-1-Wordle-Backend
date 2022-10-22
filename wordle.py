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

#@app.route("/guess/", methods=["POST"])
#@validate_request(Guess)
#async def create_guess(data):
    #db = await _get_db()
    #if validate_input(data, db):
        

    


def wordle(guess, word):
    print("Welcome to Wordle! The goal is to correctly guess a five letter word. You will have 6 attempts. Each correct letter that is in the correct place in the secret word will be marked with green text. Each letter that is present in the secret word but in the incorrect place will be marked with yellow text. Letters not in the secret word will be marked with black text. Good luck!")
    done = False
    for i in range (0, 6):
        print("Guesses left: ", 6 - i)
        if guess == word:
            print("You did it!")
            break
        result = ""
        if not done:
            count = 0
            for char in guess:
                if char == word[count]:
                    result = result + char + "\033[0;37;40m"
                elif char in word:
                    result = result + "\033[1;33;40m" + char + "\033[0;37;40m"
                else:
                    result = result + char
                count +=1
            print (result)

def validate_input(guess, db):
    if len(guess) != 5:
        print("Error: Expected 5 letter word")
        return False   
    if not db.fetch_one("SELECT * FROM validGuesses WHERE word=(?)", (guess,)) is None:
        print("Error: Please enter a valid word")
    return guess

async def check_user(db, auth):
    if auth is not None:
        print(auth.type + auth.username + auth.password)

    if auth is not None and auth.type == 'basic':
        result = await db.fetch_one("SELECT user_id FROM users where username = :username and password =:password",
                                    values={"username": auth.username, "password": auth.password})
        print('inside auth')
        app.logger.debug(type(result))
        if result:
            return result.user_id
        else:
            print('inside abort')
            abort(401)
    else:
        abort(401)


