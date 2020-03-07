import asyncio
import functools
import logging
from typing import Optional

from blinker import signal
from discord.ext import commands

from riffbot.audio.player import Player
from riffbot.endpoints.endpoint import Endpoint
from riffbot.endpoints.youtube import YouTubeEndpoint
from riffbot.utils import checks, converters
from riffbot.utils.timer import Timer

_logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!")

_player: Optional[Player] = None
_leave_timer: Optional[Timer] = None


def _on_song_start(ctx: commands.Context, sender: Player, song: Endpoint):
    _logger.debug("Song start handler called")

    async def exec():
        await ctx.send(f"▶  {song.get_song_description()}")

    asyncio.ensure_future(exec())


def _on_song_stop(ctx: commands.Context, sender: Player, is_last: bool):
    global _leave_timer
    _logger.debug("Song stop handler called")
    if is_last:
        if _leave_timer:
            _leave_timer.reset_timeout()
        else:
            _leave_timer = Timer(120, leave_channel, ctx)  # 2 minutes until bot leaves the channel


@bot.event
async def on_ready():
    _logger.info(f"Logged on as {bot.user} :)")


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    _logger.info(f"Received command \"leave\" from {ctx.author.name}")
    if _leave_timer:
        _leave_timer.cancel()
    await leave_channel(ctx, send_info=True)


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
@checks.is_in_voice_channel()
async def play(ctx, *args):
    _logger.info(f"Received command \"{' '.join(['play', *args])}\" from {ctx.author.name}")
    if _leave_timer:
        _leave_timer.cancel()
    # Can't specify a converter directly for a variable number of arguments unfortunately
    videos = converters.to_youtube_videos(args)
    if videos is None:
        # Resume paused song
        if _player:
            _player.play()
            endpoint = _player.get_current()
            if endpoint:
                await ctx.send(f"▶  {endpoint.get_song_description()}")
    else:
        if ctx.voice_client is None:
            await join_channel(ctx)
        endpoints = [YouTubeEndpoint(video) for video in videos]
        song_queue = _player.get_queue()
        song_queue.enqueue(endpoints)
        if len(endpoints) > 1:
            await ctx.send(f"Enqueued [{len(endpoints)}] songs!")
        if not _player.get_current():
            _player.play()


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
async def pause(ctx):
    _logger.info(f"Received command \"pause\" from {ctx.author.name}")
    _player.pause()
    endpoint = _player.get_current()
    if endpoint:
        await ctx.send(f"⏸  {endpoint.get_song_description()}")


@bot.command(help="Enqueue a mix of songs similar to the current one (YouTube only).")
@commands.guild_only()
async def radio(ctx: commands.Context):
    _logger.info(f"Received command \"radio\" from {ctx.author.name}")
    if _player:
        current_endpoint = _player.get_current()
        if current_endpoint:
            if isinstance(current_endpoint, YouTubeEndpoint):
                current_id = current_endpoint.get_youtube_id()
                mix_url = f"https://www.youtube.com/watch?v={current_id}&list=RD{current_id}"
                # If the current song itself is part of the radio, filter it out
                radio_endpoints = [YouTubeEndpoint(video) for video in converters.to_youtube_videos([mix_url])
                                   if video.videoid != current_id]
                _player.get_queue().enqueue(radio_endpoints)
                await ctx.send(f"Enqueued [{len(radio_endpoints)}] songs!")
            else:
                await ctx.send("Radio is currently only supported for YouTube songs.")


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
    if _leave_timer:
        _leave_timer.reset_timeout()
    songs = _player.get_queue().list()
    if len(songs) == 0:
        await ctx.send("No songs are currently enqueued!")
    else:
        string = functools.reduce(lambda acc, val: acc +
                                  f"\n[{val[0]+1}]  {val[1].get_song_description()}", enumerate(songs), "")
        await ctx.send(string)


@bot.command(help="Clear the song queue of its current contents.")
@commands.guild_only()
async def clear(ctx):
    _logger.info(f"Received command \"clear\" from {ctx.author.name}")
    if _player:
        _player.get_queue().clear()
        await ctx.send("Cleared the song queue!")


@bot.command(help="Skip the current song.")
@commands.guild_only()
async def skip(ctx, number_of_songs: Optional[int]):
    _logger.info(
        f"Received command \"skip{f' {number_of_songs}' if number_of_songs is not None else ''}\""
        " from {ctx.author.name}")
    if _player:
        current = _player.get_current()
        if current:
            _player.skip()
        queue = _player.get_queue()
        if number_of_songs is not None and number_of_songs > 1:
            # Remove the first (number_of_songs - 1) songs from the queue
            for i in range(number_of_songs - 1):
                if queue.get_next() is None:
                    break
            await ctx.send(f"⏩  to song {number_of_songs} in queue")
        elif current:
            await ctx.send(f"⏩  {current.get_song_description()}")


@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    _logger.info(f"Received command \"shutdown\" from {ctx.author.name}")
    if _leave_timer:
        _leave_timer.cancel()
    await ctx.send("Shutting down, goodbye!")
    await leave_channel(ctx)
    await bot.close()


@bot.event
async def on_command_error(ctx, error: Exception):
    _logger.error(f"Exception occurred during command: {error}")
    await ctx.send(f"Error: {error}")
    raise error


async def join_channel(ctx):
    global _player
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        _logger.debug(f"Joining channel {voice_channel.name}")
        voice_client = await voice_channel.connect()
        _player = Player(voice_client)
        signal("player_song_start").connect(functools.partial(_on_song_start, ctx), sender=_player, weak=False)
        signal("player_song_stop").connect(functools.partial(_on_song_stop, ctx), sender=_player, weak=False)
    elif voice_channel != ctx.voice_client.channel:
        _logger.debug(f"Moving to channel {voice_channel.name}")
        await ctx.voice_client.move_to(voice_channel)


async def leave_channel(ctx, *, send_info=False):
    global _player
    if ctx.voice_client and ctx.voice_client.is_connected():
        voice_channel = ctx.voice_client.channel.name
        _logger.debug(f"Leaving channel {voice_channel}")
        _player.stop()
        _player = None
        await ctx.voice_client.disconnect()
        if send_info:
            await ctx.send(f"Disconnected from {voice_channel}!")
