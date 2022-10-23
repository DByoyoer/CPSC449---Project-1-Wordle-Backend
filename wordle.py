import dataclasses
import sqlite3
import textwrap
import random

import databases
import toml

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)


MAX_GUESSES = 6


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


@app.route("/", methods=["GET"])
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
            user,
        )

    except sqlite3.IntegrityError as e:
        abort(409, e)

    return {"Message": "User Successfully Created. Please create a game"}, 201


# Whether the guess was a valid word.
# If the guess was valid, whether the guess was correct (i.e. whether the guess was the secret word).
# The number of guesses remaining. (Only valid guesses should decrement this number.)
# Vaid but incorrect guesses should also return:
# The letters that are in the secret word and in the correct spot
# The letters that are in the secret word but in the wrong spot


@app.route("/games/<int:gameID>", methods=["POST"])
@validate_request(Guess)
async def create_guess(data, gameID):
    db = await _get_db()
    guess = data.guess
    isValid = False

    game = await db.fetch_one(
        "SELECT * FROM games WHERE gameID = :gameID AND isInProgress = true",
        {"gameID": gameID},
    )
    if game is None:
        return {"message": "Game not found or game finshed."}, 404
    game = dict(game)
    if validate_input(guess, db):
        isValid = True
        game["guessesMade"] += 1

        try:
            await db.execute(
                """
                UPDATE games SET guessesMade = guessesMade + 1 WHERE gameID = :gameID
                """,
                {"gameID": gameID},
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)
        try:
            await db.execute(
                """
                INSERT INTO guesses(gameID, guess, guessNumber ) values (:gameID, :guess, :guessNumber)
            """,
                {
                    "gameID": game["gameID"],
                    "guess": guess,
                    "guessNumber": game["guessesMade"],
                },
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)
        result, isSecret = await wordle(guess, game, db)

    guessesRemaining = MAX_GUESSES - game["guessesMade"]
    return {
        "isValid": isValid,
        "isSecret": isSecret,
        "result": result,
        "guessesRemaining": guessesRemaining,
    }, 201


# When supplied with an identifier for a game that is in progress, the user should receive the same values
# as an incorrect guess, except that the number of guesses should not be incremented. If the identifier corresponds
#  to a game that is finished, return only the number of guesses.
@app.route("/games/<int:gameID>", methods=["GET"])
async def getGameState(gameID):
    db = await _get_db()
    isValid = False

    game = await db.fetch_one(
        "SELECT * FROM games WHERE gameID = :gameID",
        {"gameID": gameID},
    )
    if game is None:
        return {"message": "Game not found."}, 404
    game = dict(game)
    if not game["isInProgress"]:
        return {"guessesMade": game["guessesMade"], "isWon": game["isWon"]}

    guesses = await db.fetch_all(
        """SELECT guess, guessNumber FROM guesses WHERE gameID = :gameID ORDER BY guessNumber""",
        {"gameID": gameID},
    )
    results = []
    for (guess, guessNum) in guesses:
        result, isSecret = await wordle(guess, game, db)
        results.append(
            {
                "guessNumber": guessNum,
                "isValid": isValid,
                "isSecret": isSecret,
                "result": result,
                "guessesRemaining": MAX_GUESSES - guessNum,
            }
        )

    return {"results": results}, 200


@app.route("/games", methods=["POST"])
async def createGame():
    db = await _get_db()
    userID = await check_user(db, request.authorization)
    secretWord = await getRandomWord(db)
    try:
        await db.execute(
            "INSERT into games(userID, secretWord) values(:userID, :secretWord)",
            {"userID": userID, "secretWord": secretWord},
        )
    except sqlite3.IntegrityError as e:
        abort(409, e)

    return {"Message": "Game Successfully Created."}, 201


@app.route("/games", methods=["GET"])
async def getGamesInProg():
    db = await _get_db()
    userID = await check_user(db, request.authorization)
    result = await db.fetch_all(
        "SELECT gameID FROM games WHERE userID = :userID AND isInProgress=true",
        {"userID": userID},
    )
    result = [r[0] for r in result]
    return {"inProgress": list(result)}, 200


async def wordle(guess, game, db):
    newSecretWord = secretWord = game["secretWord"]
    if guess == secretWord:
        try:
            await db.execute(
                """
                UPDATE games SET isInProgress = False AND isWon = True WHERE gameID = :gameID
            """,
                {"gameID": game["gameID"]},
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)
        return [2, 2, 2, 2, 2], True
    elif game["guessesMade"] >= 6:
        try:
            await db.execute(
                """
                UPDATE games SET isInProgress = False AND isWon = True WHERE gameID = :gameID
                """,
                {"gameID": game["gameID"]},
            )
        except sqlite3.IntegrityError as e:
            abort(409, e)
    result = [0] * 5
    for i, char in enumerate(guess):
        if char == secretWord[i]:
            result[i] = 2
            newSecretWord = secretWord.replace(char, "-")
    for i, char in enumerate(guess):
        if result[i] == 2:
            continue
        elif char in newSecretWord:
            result[i] = 1
        else:
            result[i] = 0

    return result, False


async def validate_input(guess, db):
    if len(guess) != 5:
        print("Error: Expected 5 letter word")
        return False
    if (
        await db.fetch_one("SELECT * FROM validGuesses WHERE word=(?)", (guess,))
        is None
    ):
        print("Error: Please enter a valid word")
        return False
    return True


async def check_user(db, auth):
    if auth is not None:
        print(auth.type + auth.username + auth.password)

    if auth is not None and auth.type == "basic":
        result = await db.fetch_one(
            "SELECT userID FROM users where name = :username and password =:password",
            values={"username": auth.username, "password": auth.password},
        )
        print("inside auth")
        app.logger.debug(type(result))
        if result:
            return result.userID
        else:
            print("inside abort")
            abort(401)
    else:
        abort(401)


async def getRandomWord(db):
    wordCount = await db.fetch_one("SELECT COUNT(*) from secretWords ")
    wordCount = wordCount[0]
    result = await db.fetch_one(
        "SELECT word from secretWords where rowid = :rowID",
        {"rowID": random.randint(1, wordCount)},
    )
    return result[0]
