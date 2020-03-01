import asyncio
import functools
import logging
from typing import Optional

from blinker import signal
from discord.ext import commands

from riffbot.utils import checks
from riffbot.utils import converters
from riffbot.audio.player import Player
from riffbot.endpoints.endpoint import Endpoint
from riffbot.endpoints.youtube import YouTubeEndpoint

_logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!")

_player: Optional[Player] = None
_explicit_join = False


def _on_song_start(ctx: commands.Context, sender: Player, song: Endpoint):
    _logger.debug("Song start handler called")

    async def exec():
        await ctx.send(f"▶  {song.get_song_description()}")

    asyncio.ensure_future(exec())


def _on_song_stop(ctx: commands.Context, sender: Player, is_last: bool):
    _logger.debug("Song stop handler called")

    async def exec():
        if is_last and not _explicit_join:
            await leave_channel(ctx)

    asyncio.ensure_future(exec())


@bot.event
async def on_ready():
    _logger.info(f"Logged on as {bot.user} :)")


@bot.command(help="Join the issuer's voice channel.")
@commands.guild_only()
# @commands.bot_has_permissions(connect=True)
@checks.is_in_voice_channel()
async def join(ctx):
    global _explicit_join
    _logger.info(f"Received command \"join\" from {ctx.author.name}")
    _explicit_join = True
    await join_channel(ctx, send_info=True)


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    global _explicit_join
    _logger.info(f"Received command \"leave\" from {ctx.author.name}")
    _explicit_join = False
    await leave_channel(ctx, send_info=True)


@bot.command(help="Instruct the bot to stay in the channel after all songs have finished playing.")
@commands.guild_only()
async def stay(ctx):
    global _explicit_join
    _logger.info(f"Received command \"stay\" from {ctx.author.name}")
    if ctx.voice_client is not None:
        _explicit_join = True
        await ctx.send("I will now stay in the current voice channel :)")


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
async def play(ctx, *args):
    global _explicit_join
    _logger.info(f"Received command \"{' '.join(['play', *args])}\" from {ctx.author.name}")
    # Can't specify a converter directly for a variable number of arguments unfortunately
    youtube_id = converters.to_youtube_video(args)
    if youtube_id is None:
        # Resume paused song
        if _player:
            _player.play()
            endpoint = _player.get_current()
            if endpoint:
                await ctx.send(f"▶  {endpoint.get_song_description()}")
    else:
        if ctx.voice_client is None:
            _explicit_join = False
            await join_channel(ctx)
        endpoint = YouTubeEndpoint(youtube_id)
        song_queue = _player.get_queue()
        song_queue.enqueue(endpoint)
        if not _player.get_current():
            _player.play()
        if song_queue.size() > 0:
            await ctx.send(f"[{song_queue.size()}]  {endpoint.get_song_description()}")


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
async def pause(ctx):
    _logger.info(f"Received command \"pause\" from {ctx.author.name}")
    _player.pause()
    endpoint = _player.get_current()
    if endpoint:
        await ctx.send(f"⏸  {endpoint.get_song_description()}")


@bot.command(help="Seek to an approximate position in the current song.")
@commands.guild_only()
async def seek(ctx, position: converters.to_position):
    _logger.info(f"Received command \"seek {position}\" from {ctx.author.name}")
    # Seeking is not yet supported in the player/endpoints, so cancel early
    await ctx.send("Seeking is not yet supported, sorry!")
    return

    if not position:
        await ctx.send(f"Invalid position, use syntax 2:01 or 1:05:42 or similar.")
        return
    if _player:
        await ctx.send("Seeking …")
        (h, m, s) = position
        try:
            _player.seek(h * 3600 + m * 60 + s)
        except Exception:  # TODO: replace with specific exception
            await ctx.send("Position is out of bounds!")


@bot.command(help="Show the current contents of the queue.")
@commands.guild_only()
async def queue(ctx):
    _logger.info(f"Received command \"queue\" from {ctx.author.name}")
    songs = _player.get_queue().list()
    if len(songs) == 0:
        await ctx.send("No songs are currently enqueued!")
    else:
        string = functools.reduce(lambda acc, val: acc +
                                  f"\n[{val[0]+1}]  {val[1].get_song_description()}", enumerate(songs), "")
        await ctx.send(string)


@bot.command(help="Skip the current song.")
@commands.guild_only()
async def skip(ctx):
    _logger.info(f"Received command \"skip\" from {ctx.author.name}")
    if _player:
        current = _player.get_current()
        if current:
            await ctx.send(f"⏩  {current.get_song_description()}")
            _player.stop()


@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    _logger.info(f"Received command \"shutdown\" from {ctx.author.name}")
    await ctx.send("Shutting down, goodbye!")
    await leave_channel(ctx)
    await bot.close()


@bot.event
async def on_command_error(ctx, error):
    _logger.error(f"Exception occurred during command: {error}")
    await ctx.send(f"Error: {error}")


async def join_channel(ctx, *, send_info=False):
    global _player
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        _logger.debug(f"Joining channel {voice_channel.name}")
        voice_client = await voice_channel.connect()
        _player = Player(voice_client)
        signal("player_song_start").connect(functools.partial(_on_song_start, ctx), sender=_player, weak=False)
        signal("player_song_stop").connect(functools.partial(_on_song_stop, ctx), sender=_player, weak=False)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")
    elif voice_channel != ctx.voice_client.channel:
        _logger.debug(f"Moving to channel {voice_channel.name}")
        await ctx.voice_client.move_to(voice_channel)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")


async def leave_channel(ctx, *, send_info=False):
    global _player
    if ctx.voice_client and ctx.voice_client.is_connected():
        _logger.debug(f"Leaving channel {ctx.voice_client.channel.name}")
        _player = None
        await ctx.voice_client.disconnect()
        if send_info:
            await ctx.send(f"Disconnected from {ctx.voice_client.channel.name}!")
