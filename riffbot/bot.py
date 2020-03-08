import asyncio
import functools
import logging
from typing import Optional

from blinker import signal
import discord
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


def cancel_leave_timer():
    global _leave_timer
    if _leave_timer:
        _leave_timer.cancel()
        _leave_timer = None


def _on_song_start(ctx: commands.Context, sender: Player, song: Endpoint):
    _logger.debug("Song start handler called")

    async def exec():
        try:
            await ctx.channel.edit(topic=f"▶  {song.get_song_description()}")
        except discord.Forbidden:
            _logger.warning("Unable to edit channel description to current song (missing permission)")

    asyncio.ensure_future(exec())


def _on_song_stop(ctx: commands.Context, sender: Player, is_last: bool):
    _logger.debug("Song stop handler called")

    async def exec():
        global _leave_timer
        if is_last:
            if _leave_timer:
                _leave_timer.reset_timeout()
            else:
                _leave_timer = Timer(120, leave_channel, ctx)  # 2 minutes until bot leaves the channel
            try:
                await ctx.channel.edit(topic=None)
            except discord.Forbidden:
                _logger.warning("Unable to clear channel topic (missing permission)")

    asyncio.ensure_future(exec())


@bot.event
async def on_ready():
    _logger.info(f"Logged on as {bot.user} :)")


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
@checks.is_in_voice_channel()
async def play(ctx: commands.Context, *args):
    _logger.info(f"Received command \"{' '.join(['play', *args])}\" from {ctx.author.name}")
    cancel_leave_timer()
    if len(args) == 0:
        # Resume paused song if one is currently playing
        if _player and _player.is_paused():
            _player.play()
            endpoint = _player.get_current()
            if endpoint:
                await ctx.send(f"▶  Resuming…")
                try:
                    await ctx.channel.edit(topic=f"▶  {endpoint.get_song_description()}")
                except discord.Forbidden:
                    _logger.warning("Unable to edit channel description to current song (missing permission)")
    else:
        # Show in channel that the bot is typing (fetching the video(s) may take up to a few seconds)
        # Not using "with ctx.typing()" because the typing indicator sometimes lingered too long after the reply was
        # already sent
        await ctx.trigger_typing()
        reply = "Sorry, no videos found :("
        # Can't specify a converter directly for a variable number of arguments unfortunately
        videos = converters.to_youtube_videos(args)
        if ctx.voice_client is None:
            await join_channel(ctx)
        if videos is not None:
            endpoints = [YouTubeEndpoint(video) for video in videos]
            song_queue = _player.get_queue()
            song_queue.enqueue(endpoints)
            if not _player.get_current():
                # No song is currently playing, so start playback and reply with appropriate message
                _player.play()
                reply = f"▶  {endpoints[0].get_song_description()}"
                if len(endpoints) > 1:
                    reply += f" (+ {len(endpoints) - 1} enqueued)"
            else:
                # A song is already playing, reply with a different message in this case
                reply = f"[{song_queue.size() - len(endpoints) + 1}] "
                if len(endpoints) == 1:
                    reply += endpoints[0].get_song_description()
                elif len(endpoints) > 1:
                    reply = f"{len(endpoints)} songs"
        # Send the reply (also clearing the typing status from the channel)
        await ctx.send(reply)


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
async def pause(ctx):
    _logger.info(f"Received command \"pause\" from {ctx.author.name}")
    if _player and _player.is_playing():
        _player.pause()
        endpoint = _player.get_current()
        if endpoint:
            await ctx.send(f"⏸  Pausing…")
            try:
                await ctx.channel.edit(topic=f"⏸  {endpoint.get_song_description()}")
            except discord.Forbidden:
                _logger.warning("Unable to edit channel description to current song (missing permission)")


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
        # Build string to print the first 15 songs in the queue
        string = functools.reduce(lambda acc, val: acc +
                                  f"\n[{val[0]+1}]  {val[1].get_song_description()}", enumerate(songs[:15]), "")
        # If there are more than 15 songs enqueued, add how many were not printed
        if len(songs) > 15:
            string += f"\n+ {len(songs) - 15} more songs"
        await ctx.send(string[1:])  # [1:] to get rid of the first newline character


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
        f" from {ctx.author.name}")
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
            await ctx.send(f"⏭  to song {number_of_songs} in queue")
        elif current:
            await ctx.send(f"⏭  Skipping…")


@bot.command(help="Shuffle the songs in the queue")
@commands.guild_only()
@checks.bot_is_in_voice_channel()
async def shuffle(ctx: commands.Context):
    _logger.info(f"Received command \"shuffle\" from {ctx.author.name}")
    if _player:
        _player.get_queue().shuffle()
        await ctx.send("🔀  Shuffled the queue")


@bot.command(help="Move to the user's current voice channel.")
@commands.guild_only()
@checks.is_in_voice_channel()
@checks.bot_is_in_voice_channel()
async def follow(ctx: commands.Context):
    _logger.info(f"Received command \"follow\" from {ctx.author.name}")
    if _leave_timer:
        _leave_timer.reset_timeout()
    await join_channel(ctx, send_info=True)


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    _logger.info(f"Received command \"leave\" from {ctx.author.name}")
    cancel_leave_timer()
    await leave_channel(ctx, send_info=True)


@bot.command(help="Log out and shut down the bot. This can only be done by the bot owner.")
@commands.is_owner()
async def shutdown(ctx):
    _logger.info(f"Received command \"shutdown\" from {ctx.author.name}")
    cancel_leave_timer()
    await ctx.send("Shutting down, goodbye!")
    await leave_channel(ctx)
    await bot.close()


@bot.event
async def on_command_error(ctx, error: Exception):
    _logger.error(f"Exception occurred during command: {error}")
    await ctx.send(f"Error: {error}")
    raise error


async def join_channel(ctx, *, send_info=False):
    global _player
    voice_channel = ctx.author.voice.channel
    reply = ""
    if ctx.voice_client is None:
        _logger.debug(f"Joining channel {voice_channel.name}")
        voice_client = await voice_channel.connect()
        _player = Player(voice_client)
        signal("player_song_start").connect(functools.partial(_on_song_start, ctx), sender=_player, weak=False)
        signal("player_song_stop").connect(functools.partial(_on_song_stop, ctx), sender=_player, weak=False)
        reply = f"Connected to {voice_channel.name}!"
    elif voice_channel != ctx.voice_client.channel:
        _logger.debug(f"Moving to channel {voice_channel.name}")
        await ctx.voice_client.move_to(voice_channel)
        reply = f"Moved to {voice_channel.name}!"
    else:
        reply = f"I am already in {voice_channel.name}!"
    if send_info:
        await ctx.send(reply)


async def leave_channel(ctx, *, send_info=False):
    global _player
    if ctx.voice_client and ctx.voice_client.is_connected():
        voice_channel = ctx.voice_client.channel.name
        _logger.debug(f"Leaving channel {voice_channel}")
        _player.stop()
        _player = None
        await ctx.voice_client.disconnect()
        try:
            await ctx.channel.edit(topic=None)
        except discord.Forbidden:
            _logger.warning("Unable to clear channel topic (missing permission)")
        if send_info:
            await ctx.send(f"Disconnected from {voice_channel}!")
