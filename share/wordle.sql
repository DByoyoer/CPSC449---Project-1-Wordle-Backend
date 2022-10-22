-- $ sqlite3 wordle.db < wordle.sql

PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    userID INT primary key,
    name VARCHAR,
    password VARCHAR
);
CREATE TABLE IF NOT EXISTS secretWords(word VARCHAR primary key);
CREATE TABLE IF NOT EXISTS validGuesses(word VARCHAR primary key);
CREATE TABLE IF NOT EXISTS games (
    gameID INT primary key,
    secretWord VARCHAR NOT NULL,
    guessesMade INT DEFAULT 0,
    userID INT NOT NULL,
    FOREIGN KEY(userID) references users(userID),
    FOREIGN KEY(secretWord) references secretWords(word)
);
CREATE TABLE IF NOT EXISTS inProgress(
    gameID INT primary key,
    FOREIGN KEY(gameID) references games(gameID)
);
CREATE TABLE IF NOT EXISTS inProgress(
    gameID INT primary key,
    isWinner BOOLEAN,
    FOREIGN KEY(gameID) references games(gameID)
);
CREATE TABLE IF NOT EXISTS guesses(
    guessID INT primary key,
    gameID INT,
    guess VARCHAR,
    guessNumber SMALLINT,
    FOREIGN KEY(gameID) references games(gameID),
    FOREIGN KEY(guess) references validGuesses(word),
    unique(gameID, guess, guessNumber)
);



