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


#@app.route("/guess/", methods=["POST"])
#async def create_guess(guess):
    


def wordle():
    print("Welcome to Wordle! The goal is to correctly guess a five letter word. You will have 6 attempts. Each correct letter that is in the correct place in the secret word will be marked with green text. Each letter that is present in the secret word but in the incorrect place will be marked with yellow text. Letters not in the secret word will be marked with black text. Good luck!")
    for i in range (0, 6):
        print("Guesses left: ", 6 - i)
        guess = user_input()
        if guess == word:
            print("You did it!")
            break
        result = ""
        if not done:
            count = 0
            for char in guess:
                if char == word[count]:
                    result = result + "\033[1;32;40m" + char + "\033[0;37;40m"
                elif char in word:
                    result = result + "\033[1;33;40m" + char + "\033[0;37;40m"
                else:
                    result = result + char
                count +=1
            print (result)

def user_input():
    valid = False
    while not valid:
        guess = input("Guess the word!  ")
        if len(guess) != 5:
            print("Guess must be 5 letters, please try again")
    return guess

