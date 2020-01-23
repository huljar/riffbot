# RiffBot – just another music bot for Discord

RiffBot aims to be a lighweight music bot that you can easily host yourself!

# Installation

```bash
# make a virtualenv somewhere
python3 -m venv /path/to/venv/riffbot
source /path/to/venv/riffbot/bin/activate
# install wheel, then requirements
pip3 install -U wheel
pip3 install -U -r requirements.txt  # or 'make install'
```

The `ringbuffer` dependency can't be installed by pip unfortunately. You need to manually download it from [here](https://github.com/bslatkin/ringbuffer/blob/898c893c1a6944a999919a69d1f9527cb2af096b/ringbuffer.py) and place it in
`src/deps/`.

To install development tools, such as a Python Language Server, run
```bash
pip3 install -U -r requirements-dev.txt  # or 'make install-dev'
```

# Run the bot
You can run the bot using `make run`. If everything works, a console message should appear after a short time that the
bot has logged on to Discord.

# License

RiffBot is licensed under the terms of the GNU General Public License v3. For more information, please see
[LICENSE.md](LICENSE.md).
