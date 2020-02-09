# RiffBot – just another music bot for Discord

RiffBot aims to be a lighweight music bot that you can easily host yourself!

# Installation

```bash
# make a virtualenv somewhere and activate it
python3 -m venv ../venvs/riffbot
source ../venvs/riffbot/bin/activate
# install via make
make install
# install required libs
sudo apt install libopus0 ffmpeg
```

To install development tools, such as a Python Language Server, run
```bash
make install-dev
```

# Run the bot

You can run the bot using `make run`. If everything works, a console message should appear after a short time that the
bot has logged on to Discord.

# License

RiffBot is licensed under the terms of the GNU General Public License v3. For more information, please see
[LICENSE.md](LICENSE.md).
