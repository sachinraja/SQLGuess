# SQLGuess
Practice SQL queries against your friends in a game to find the location in the database using hints.

## Game
  * Hosts create rooms that have a unique room id and code.
  * Hosts can share that room code and allow other users to join the room.
  * During each round, users try to guess the location name using hints provided on a set interval.
  * They can query the database using the information in the hints to narrow down options for the location.
  * Once the round is over, a board is displayed with the users, sorted by number of queries from least to greatest and if they successfully guessed or not.
  * The host can then choose to continue to the next round or simply end the game, which closes the room and allows the room id/code to be chosen again.

## Database (Postgres)
There is a special schema called "game" that the readonly connection to the database is restricted to. 
This prevents users from potentially querying for and reading sensitive data.
Each transaction is rolled back after the user's query to prevent any permanent changes from being made (however, no rows can be inserted the connection only has readonly access).
