import asyncio
import functools
import logging
import traceback
from typing import Optional
import urllib

from blinker import signal
import discord
from discord.ext import commands
from i18n import t

from riffbot.audio.player import Player
from riffbot.endpoints.endpoint import Endpoint
from riffbot.endpoints.texttospeech import TextToSpeechEndpoint
from riffbot.endpoints.youtube import YouTubeEndpoint
from riffbot.utils import actions, checks, converters, utils
from riffbot.utils.timer import Timer

_logger = logging.getLogger(__name__)

bot: commands.Bot = commands.Bot(command_prefix="!")

_player: Optional[Player] = None
_leave_timer: Optional[Timer] = None


def cancel_leave_timer():
    global _leave_timer
    if _leave_timer:
        _leave_timer.cancel()
        _leave_timer = None


def reset_leave_timer():
    if _leave_timer:
        _leave_timer.reset_timeout()


def _on_song_start(ctx: commands.Context, sender: Player, song: Endpoint):
    _logger.debug("Song start handler called")

    async def exec():
        try:
            await ctx.channel.edit(topic=t("commands.channel_topic_playing", locale=ctx.guild.preferred_locale,
                                           desc=song.get_song_description()))
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


@bot.command(help="Search YouTube for a song and play/enqueue it")
@commands.guild_only()
@checks.is_in_voice_channel()
@actions.log_command(_logger)
async def play(ctx: commands.Context, *args):
    reset_leave_timer()
    if len(args) == 0:
        # Resume paused song if one is currently playing
        if _player and _player.is_paused():
            _player.play()
            endpoint = _player.get_current()
            if endpoint:
                cancel_leave_timer()
                await ctx.send(t("commands.resume", locale=ctx.guild.preferred_locale))
                try:
                    await ctx.channel.edit(topic=t("commands.channel_topic_playing", locale=ctx.guild.preferred_locale,
                                                   desc=endpoint.get_song_description()))
                except discord.Forbidden:
                    _logger.warning("Unable to edit channel description to current song (missing permission)")
    else:
        # Show in channel that the bot is typing (fetching the video(s) may take up to a few seconds)
        # Not using "with ctx.typing()" because the typing indicator sometimes lingered too long after the reply was
        # already sent
        await ctx.trigger_typing()
        reply = t("commands.play_no_results", locale=ctx.guild.preferred_locale)
        # Can't specify a converter directly for a variable number of arguments unfortunately
        videos = converters.to_youtube_videos(args)
        if ctx.voice_client is None:
            await join_channel(ctx)
        if videos is not None:
            cancel_leave_timer()
            endpoints = [YouTubeEndpoint(video) for video in videos]
            song_queue = _player.get_queue()
            song_queue.enqueue(endpoints)
            if not _player.get_current():
                # No song is currently playing, so start playback and reply with appropriate message
                _player.play()
                length = utils.to_human_readable_position(endpoints[0].get_length())
                if len(endpoints) > 1:
                    reply = t("commands.playnow_multiple", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length, more=len(endpoints)-1)
                else:
                    reply = t("commands.play_single", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length)
            else:
                # A song is already playing, reply with a different message in this case
                position = song_queue.size() - len(endpoints) + 1
                if len(endpoints) > 1:
                    length = utils.to_human_readable_position(utils.get_total_length(endpoints))
                    reply = t("commands.enqueued_multiple", locale=ctx.guild.preferred_locale,
                              num=len(endpoints), total=length, pos=position)
                else:
                    length = utils.to_human_readable_position(endpoints[0].get_length())
                    reply = t("commands.enqueued_single", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length, pos=position)
        # Send the reply (also clearing the typing status from the channel)
        await ctx.send(reply)


@bot.command(help="Search YouTube for a song and and play it right now, skipping the current song")
@commands.guild_only()
@actions.log_command(_logger)
async def playnow(ctx: commands.Context, *args):
    reset_leave_timer()
    if len(args) > 0:
        # Show in channel that the bot is typing (fetching the video(s) may take up to a few seconds)
        # Not using "with ctx.typing()" because the typing indicator sometimes lingered too long after the reply was
        # already sent
        await ctx.trigger_typing()
        reply = t("commands.play_no_results", locale=ctx.guild.preferred_locale)
        # Can't specify a converter directly for a variable number of arguments unfortunately
        videos = converters.to_youtube_videos(args)
        if ctx.voice_client is None:
            await join_channel(ctx)
        if videos is not None:
            cancel_leave_timer()
            endpoints = [YouTubeEndpoint(video) for video in videos]
            song_queue = _player.get_queue()
            song_queue.enqueue(endpoints, pos=0)
            if _player.get_current():
                # A song is currently playing, so skip it
                _player.skip()
            else:
                # No song is playing, so start playback now
                _player.play()
            length = utils.to_human_readable_position(endpoints[0].get_length())
            if len(endpoints) > 1:
                reply = t("commands.playnow_multiple", locale=ctx.guild.preferred_locale,
                          desc=endpoints[0].get_song_description(), len=length, more=len(endpoints)-1)
            else:
                reply = t("commands.play_single", locale=ctx.guild.preferred_locale,
                          desc=endpoints[0].get_song_description(), len=length)
        # Send the reply (also clearing the typing status from the channel)
        await ctx.send(reply)


@bot.command(help="Search YouTube for a song and and play it after the current song")
@commands.guild_only()
@actions.log_command(_logger)
async def playnext(ctx: commands.Context, *args):
    reset_leave_timer()
    if len(args) > 0:
        # Show in channel that the bot is typing (fetching the video(s) may take up to a few seconds)
        # Not using "with ctx.typing()" because the typing indicator sometimes lingered too long after the reply was
        # already sent
        await ctx.trigger_typing()
        reply = t("commands.play_no_results", locale=ctx.guild.preferred_locale)
        # Can't specify a converter directly for a variable number of arguments unfortunately
        videos = converters.to_youtube_videos(args)
        if ctx.voice_client is None:
            await join_channel(ctx)
        if videos is not None:
            cancel_leave_timer()
            endpoints = [YouTubeEndpoint(video) for video in videos]
            song_queue = _player.get_queue()
            song_queue.enqueue(endpoints, pos=0)
            if not _player.get_current():
                # No song is playing, so start playback now
                _player.play()
                length = utils.to_human_readable_position(endpoints[0].get_length())
                if len(endpoints) > 1:
                    reply = t("commands.play_multiple", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length, more=len(endpoints)-1)
                else:
                    reply = t("commands.play_single", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length)
            else:
                if len(endpoints) > 1:
                    length = utils.to_human_readable_position(utils.get_total_length(endpoints))
                    reply = t("commands.enqueued_multiple", locale=ctx.guild.preferred_locale,
                              num=len(endpoints), total=length, pos=1)
                else:
                    length = utils.to_human_readable_position(endpoints[0].get_length())
                    reply = t("commands.enqueued_single", locale=ctx.guild.preferred_locale,
                              desc=endpoints[0].get_song_description(), len=length, pos=1)
        # Send the reply (also clearing the typing status from the channel)
        await ctx.send(reply)


@bot.command(help="Say anything via text to speech")
@commands.guild_only()
@actions.log_command(_logger)
async def say(ctx: commands.Context, *args: str):
    reset_leave_timer()
    if len(args) > 0:
        await ctx.trigger_typing()
        reply = t("commands.say_no_results", locale=ctx.guild.preferred_locale)
        if ctx.voice_client is None:
            await join_channel(ctx)
        cancel_leave_timer()
        text = " ".join(args)
        text_abbrev = f"{text[:50]}…" if len(text) > 52 else text
        endpoint = TextToSpeechEndpoint(text)
        song_queue = _player.get_queue()
        song_queue.enqueue(endpoint)
        if not _player.get_current():
            _player.play()
            reply = t("commands.say_now", locale=ctx.guild.preferred_locale, text=text_abbrev)
        else:
            reply = t("commands.say_enqueued", locale=ctx.guild.preferred_locale,
                      text=text_abbrev, pos=song_queue.size())
        await ctx.send(reply)


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
@actions.log_command(_logger)
async def pause(ctx):
    reset_leave_timer()
    if _player and _player.is_playing():
        _player.pause()
        endpoint = _player.get_current()
        if endpoint:
            await ctx.send(t("commands.pause", locale=ctx.guild.preferred_locale))
            try:
                await ctx.channel.edit(topic=t("commands.channel_topic_paused", locale=ctx.guild.preferred_locale,
                                               desc=endpoint.get_song_description()))
            except discord.Forbidden:
                _logger.warning("Unable to edit channel description to current song (missing permission)")


@bot.command(help="Enqueue a mix of songs similar to the current one (YouTube only).")
@commands.guild_only()
@actions.log_command(_logger)
async def radio(ctx: commands.Context):
    reset_leave_timer()
    if _player:
        current_endpoint = _player.get_current()
        if current_endpoint:
            if isinstance(current_endpoint, YouTubeEndpoint):
                try:
                    current_id = current_endpoint.get_youtube_id()
                    mix_url = f"https://www.youtube.com/watch?v={current_id}&list=RD{current_id}"
                    # If the current song itself is part of the radio, filter it out
                    radio_endpoints = [YouTubeEndpoint(video) for video in converters.to_youtube_videos([mix_url])
                                       if video.videoid != current_id]
                    _player.get_queue().enqueue(radio_endpoints)
                    length = utils.to_human_readable_position(utils.get_total_length(radio_endpoints))
                    await ctx.send(t("commands.radio", locale=ctx.guild.preferred_locale,
                                     num=len(radio_endpoints), total=length))
                except urllib.error.HTTPError as error:
                    if error.code == 400:
                        await ctx.send(t("commands.radio_not_found", locale=ctx.guild.preferred_locale))
                    else:
                        raise error
            else:
                await ctx.send(t("commands.radio_not_supported", locale=ctx.guild.preferred_locale))


@bot.command(help="Seek to an approximate position in the current song.")
@commands.guild_only()
@actions.log_command(_logger)
async def seek(ctx, position: converters.to_position):
    reset_leave_timer()
    # Seeking is not yet supported in the player/endpoints, so cancel early
    await ctx.send(t("commands.seek_not_supported", locale=ctx.guild.preferred_locale))
    return

    if not position:
        await ctx.send(f"Invalid position, use syntax 2:01 or 1:05:42 or similar.")
        return
    if _player:
        await ctx.send("Seeking…")
        (h, m, s) = position
        try:
            _player.seek(h * 3600 + m * 60 + s)
        except Exception:  # TODO: replace with specific exception
            await ctx.send("Position is out of bounds!")


@bot.command(help="Display information on the currently playing song")
@commands.guild_only()
@actions.log_command(_logger)
async def current(ctx: commands.Context):
    reset_leave_timer()
    if _player:
        song = _player.get_current()
        if song:
            length = utils.to_human_readable_position(song.get_length())
            await ctx.send(t("commands.current", locale=ctx.guild.preferred_locale,
                             desc=song.get_song_description(), len=length))


@bot.command(help="Show the current contents of the queue.")
@commands.guild_only()
@actions.log_command(_logger)
async def queue(ctx):
    reset_leave_timer()
    if not _player or not _player.get_current():
        # Queue empty and nothing playing
        await ctx.send(t("commands.queue_empty", locale=ctx.guild.preferred_locale, cmd_prefix="!"))
        return
    current = _player.get_current()
    current_length = utils.to_human_readable_position(current.get_length())
    current_string = t("commands.queue_helper_entry", locale=ctx.guild.preferred_locale,
                       pos=utils.to_keycap_emojis(0), desc=current.get_song_description(), len=current_length)
    songs = _player.get_queue().list()
    if len(songs) == 0:
        # Queue empty but something's playing
        await ctx.send(t("commands.queue_single", locale=ctx.guild.preferred_locale,
                         len=current_length, current=current_string))
        return

    # Queue not empty and something's playing
    total_length = utils.to_human_readable_position(utils.get_total_length([current, *songs]))
    next_string = "\n".join(
        [t("commands.queue_helper_entry", locale=ctx.guild.preferred_locale, pos=utils.to_keycap_emojis(idx+1),
           desc=song.get_song_description(), len=utils.to_human_readable_position(song.get_length()))
         for idx, song in enumerate(songs[:9])])
    if len(songs) <= 9:
        await ctx.send(t("commands.queue_multiple", locale=ctx.guild.preferred_locale, num=1+len(songs),
                         total=total_length, current=current_string, next=next_string))
    else:
        await ctx.send(t("commands.queue_many", locale=ctx.guild.preferred_locale, num=1+len(songs),
                         total=total_length, current=current_string, next=next_string, remaining=len(songs)-9))


@bot.command(help="Clear the song queue of its current contents.")
@commands.guild_only()
@actions.log_command(_logger)
async def clear(ctx):
    reset_leave_timer()
    if _player:
        queue = _player.get_queue()
        num_songs = queue.size()
        total_length = utils.to_human_readable_position(queue.get_total_length())
        queue.clear()
        await ctx.send(t("commands.queue_clear", locale=ctx.guild.preferred_locale, num=num_songs, total=total_length))


@bot.command(help="Skip the current song.")
@commands.guild_only()
@actions.log_command(_logger)
async def skip(ctx, number_of_songs: Optional[int]):
    reset_leave_timer()
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
            await ctx.send(t("commands.skip_to", locale=ctx.guild.preferred_locale, num=number_of_songs))
        elif current:
            await ctx.send(t("commands.skip_single", locale=ctx.guild.preferred_locale))


@bot.command(help="Shuffle the songs in the queue")
@commands.guild_only()
@checks.bot_is_in_voice_channel()
@actions.log_command(_logger)
async def shuffle(ctx: commands.Context):
    reset_leave_timer()
    if _player:
        _player.get_queue().shuffle()
        await ctx.send(t("commands.shuffle", locale=ctx.guild.preferred_locale))


@bot.command(help="Move to the user's current voice channel.")
@commands.guild_only()
@checks.is_in_voice_channel()
@checks.bot_is_in_voice_channel()
@actions.log_command(_logger)
async def follow(ctx: commands.Context):
    reset_leave_timer()
    await join_channel(ctx, send_info=True)


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
@actions.log_command(_logger)
async def leave(ctx):
    cancel_leave_timer()
    await leave_channel(ctx, send_info=True)


@bot.command(help="Log out and shut down the bot. This can only be done by the bot owner.")
@commands.is_owner()
@actions.log_command(_logger)
async def shutdown(ctx):
    cancel_leave_timer()
    await ctx.send(t("commands.shutdown", locale=ctx.guild.preferred_locale))
    await leave_channel(ctx)
    await bot.close()


@bot.event
async def on_command_error(ctx, error: BaseException):
    _logger.error(f"Exception occurred during command: {error}")
    # Handle all remaining exceptions
    root_error = error.__cause__ if error.__cause__ else error
    message = "\n".join([str(root_error), *traceback.format_tb(root_error.__traceback__)])
    await ctx.send(t("commands.general_error", locale=ctx.guild.preferred_locale, message=message))


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
        reply = t("commands.channel_join", locale=ctx.guild.preferred_locale, name=voice_channel.name)
    elif voice_channel != ctx.voice_client.channel:
        _logger.debug(f"Moving to channel {voice_channel.name}")
        await ctx.voice_client.move_to(voice_channel)
        reply = t("commands.channel_move", locale=ctx.guild.preferred_locale, name=voice_channel.name)
    else:
        reply = t("commands.channel_already_in", locale=ctx.guild.preferred_locale, name=voice_channel.name)
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
            await ctx.send(t("commands.channel_leave", locale=ctx.guild.preferred_locale, name=voice_channel))
