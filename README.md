# RiffBot – just another music bot for Discord

RiffBot aims to be a lightweight music bot that you can easily host yourself!

# Installation

```bash
# install required libs (e.g. for Debian and its derivatives):
sudo apt install python3-dev libopus0 ffmpeg
# make a virtualenv somewhere and activate it
python3 -m venv ../venvs/riffbot
source ../venvs/riffbot/bin/activate
# install via make
make install
```

To install development tools, such as a Python Language Server, run
```bash
make install-dev
```

# Adding the bot to your server

To run Riffbot, you need to register a bot with your Discord server first and obtain a token. Head over
[here](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) for a great rundown on
how this is done. The bot needs at least permissions to view channels, send messages, connect to voice, and speak.

The token is used by the bot to authenticate itself with Discord. Riffbot reads the token from the file `src/.env` that
you'll have to create. Put the following contents into it:

```
DISCORD_TOKEN=<your_token>
```

and replace `<your_token>` with your personal token.

# Run the bot

You can run the bot using `make run`. If everything works, a console message should appear after a short time that the
bot has logged on to Discord.

The bot is currently not suitable for multi-server operation – one instance of the bot should only serve one Discord
guild.

# License

RiffBot is licensed under the terms of the GNU General Public License v3. For more information, please see
[LICENSE.md](LICENSE.md).
