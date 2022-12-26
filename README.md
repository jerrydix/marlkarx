# Marl Karx
A simple Discord bot that likes communism

The Bot is currently only optimized to run on my friend's server, but you can use most of the features on your own server, too.

## Setup
For setting up the bot and getting the ping, imagine and complete commands up to work you will have to create a config.json with the following form:

``` 
"token": "YOUR_TOKEN",
"openai_key": "YOUR_OPENAI_KEY",
"games": [
{
  "name": "GAME_NAME",
  "players": [
    DISCORD_ID_PLAYER1,
    DISCORD_ID_PLAYER2,
    ...
  ]
},
...
]
