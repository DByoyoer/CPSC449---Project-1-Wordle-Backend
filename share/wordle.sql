-- $ sqlite3 wordle.db < wordle.sql

PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    userID INTEGER primary key ASC,
    name VARCHAR,
    password VARCHAR
);
CREATE TABLE IF NOT EXISTS secretWords(word VARCHAR primary key);
CREATE TABLE IF NOT EXISTS validGuesses(word VARCHAR primary key);
CREATE TABLE IF NOT EXISTS games (
    gameID INTEGER primary key ASC,
    secretWord VARCHAR NOT NULL,
    guessesMade INTEGER DEFAULT 0,
    userID INTEGER NOT NULL,
    isInProgress BOOLEAN DEFAULT true,
    isWon BOOLEAN DEFAULT false,
    FOREIGN KEY(userID) references users(userID),
    FOREIGN KEY(secretWord) references secretWords(word)
);

CREATE TABLE IF NOT EXISTS guesses(
    guessID INTEGER primary key ASC,
    gameID INT,
    guess VARCHAR,
    guessNumber SMALLINT,
    FOREIGN KEY(gameID) references games(gameID),
    FOREIGN KEY(guess) references validGuesses(word),
    unique(gameID, guess, guessNumber)
);



