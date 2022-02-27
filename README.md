# RiffBot – just another music bot for Discord

RiffBot aims to be a lightweight music bot that you can easily host yourself!

# Installation

```bash
# install required libs (e.g. for Debian and its derivatives):
sudo apt install python3-dev python3-pip libopus0 ffmpeg make git
# make a virtualenv somewhere and activate it
python3 -m venv ../venvs/riffbot
source ../venvs/riffbot/bin/activate
# install dependencies via make
make install
```

To install development tools, such as a Python Language Server, run
```bash
make install-dev
```

Alternatively, you can also run riffbot in a Docker container:

```bash
docker build --tag riffbot .
docker run -e DISCORD_TOKEN=<your_token_here> riffbot
```

Replace `<your_token_here>` with your Discord token. With the Docker variant, you do not need the `.env` file that is
described below.

## Adding the bot to your server

To run Riffbot, you need to register a bot with your Discord server first and obtain a token. Head over
[here](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) for a great rundown on
how this is done. The bot needs at permissions to view channels, manage the channel where it will receive commands, send
messages to that same channel, connect to voice, and speak.

The token is used by the bot to authenticate itself with Discord. Riffbot reads the token from the file `riffbot/.env`
that you'll have to create. Put the following contents into it:

```
DISCORD_TOKEN=<your_token>
```

and replace `<your_token>` with your personal token.

# Run the bot

You can run the bot using `make run`. If everything works, you should see the bot online in Discord shortly after. You
can also use `make run-debug` instead if you want debug logging on the console.

The bot is currently not suited for multi-server operation – one instance of the bot should only serve one Discord
guild.

## Run in background as a systemd service

If you want to run Riffbot unattended for a longer period of time, it is recommended to run it in the background, e.g.
as a systemd service. Riffbot can easily be installed as such a service. There are currently two variants:

* **User service**
Run `make service VENV=path/to/your/venv` as a non-root user with `VENV` pointing to the virtual environment that the
bot is supposed to run in. This will place a service file into `~/.config/systemd/user/`. Then, you can run
`systemctl --user start riffbot` to run the bot in the background as the current user.

**System-wide service**
Run `make service VENV=path/to/your/venv XUSER=username` as root with `VENV` representing the path of the virtual
environment (same as user service) and `XUSER` set to the username that the bot will run as. It is highly recommended to
use a dedicated, non-root user for `XUSER` for security reasons. Then, you can run `systemctl start riffbot` to run the
bot in the background and/or `systemctl enable riffbot` to have riffbot run automatically when the system boots.

# License

RiffBot is licensed under the terms of the GNU General Public License v3. For more information, please see
[LICENSE.md](LICENSE.md).
