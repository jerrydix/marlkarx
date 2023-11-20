# Marl Karx
A simple Discord.py bot that has neat unique features and music functionality 

The Bot is currently only optimized to run on my friend's server, but you can use most of the features on your own server, too.

This bot supports slash commands and can be used as a music bot.

## Setup
For setting up the bot and getting the ping, imagine, complete and music commands up to work you will have to create a config.json with the following form:

``` 
"token": "YOUR_TOKEN",
"openai_key": "YOUR_OPENAI_KEY",
"games": [],
"playlists": [],
"reminders": []
```
Furthermore, you have to create a role named "DJ" on your server and assign it to people who are supposed to be able to use the fskip, fremove, and stop commands. 

Currently, the docker file is out of date, so you will have to install the needed dependencies via pip yourself.

To launch the bot after setting up the config.json simply execute main.py
