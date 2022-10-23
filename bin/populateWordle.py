from itertools import zip_longest
import json
import sqlite3


def populate():
    with open("correct.json") as file:
        secretWordList = json.load(file)

    with open("valid.json") as file:
        validGuessList = json.load(file)

# Hardcoded :(
    con = sqlite3.connect("./var/wordle.db")

    cur = con.cursor()

    if cur.execute("SELECT count(word) FROM secretWords").fetchone()[0] != 0:
        print("ERROR some secret words are already in the database")
        return 

    if cur.execute("SELECT count(word) FROM validGuesses").fetchone()[0] != 0:
        print("ERROR some valid guesses are already in the database")
        return 

    secretWordList = [(word,) for word in secretWordList]
    validGuessList = [(word,) for word in validGuessList]

    cur.executemany("INSERT INTO secretWords values(?)", secretWordList)
    cur.executemany("INSERT INTO validGuesses values(?)", validGuessList)
    con.commit()

  

    
if __name__ == "__main__":
    populate()
