import functools
import logging

from discord.ext import commands

from riffbot.utils import checks
from riffbot.utils import converters
from riffbot.audio.song_queue import SongQueue
from riffbot.audio.endpoints.youtube import YouTubeEndpoint

_logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!")

_voice_client = None
_song_queue = None
_text_channel = None
_explicit_join = False


async def on_song_over():
    if _song_queue.size() > 0:
        if _text_channel is not None:
            await _text_channel.send(f"▶  {_song_queue.get_next().get_song_description()}")
    elif not _explicit_join:
        await leave_channel(None)


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
    if _voice_client is not None:
        _explicit_join = True
        await ctx.send("I will now stay in the current voice channel :)")


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
async def play(ctx, *args):
    global _explicit_join
    _logger.info(f"Received command \"play {' '.join(args)}\" from {ctx.author.name}")
    # Can't specify a converter directly for a variable number of arguments unfortunately
    youtube_id = converters.to_youtube_video(args)
    if youtube_id is None:
        # Resume paused song
        player = _song_queue.get_player()
        if player is not None:
            player.resume()
            await ctx.send(f"▶  {player.get_endpoint().get_song_description()}")
    else:
        if _voice_client is None:
            _explicit_join = False
            await join_channel(ctx)
        endpoint = YouTubeEndpoint(youtube_id)
        pos = _song_queue.enqueue(endpoint)
        if pos == 0:
            await ctx.send(f"▶  {endpoint.get_song_description()}")
        else:
            await ctx.send(f"[{pos}]  {endpoint.get_song_description()}")


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
async def pause(ctx):
    _logger.info(f"Received command \"pause\" from {ctx.author.name}")
    player = _song_queue.get_player()
    player.pause()
    await ctx.send(f"⏸  {player.get_endpoint().get_song_description()}")


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
    player = _song_queue.get_player() if _song_queue else None
    if player:
        await ctx.send("Seeking …")
        (h, m, s) = position
        try:
            player.seek(h * 3600 + m * 60 + s)
        except Exception:  # TODO: replace with specific exception
            await ctx.send("Position is out of bounds!")


@bot.command(help="Show the current contents of the queue.")
@commands.guild_only()
async def queue(ctx):
    _logger.info(f"Received command \"queue\" from {ctx.author.name}")
    songs = _song_queue.get_all() if _song_queue is not None else []
    if len(songs) == 0:
        await ctx.send("No songs are currently enqueued!")
    else:
        ret = f"▶  {songs[0].get_song_description()}"
        ret = functools.reduce(lambda acc, val: acc +
                               f"\n[{val[0]+1}]  {val[1].get_song_description()}", enumerate(songs[1:]), ret)
        await ctx.send(ret)


@bot.command(help="Skip the current song.")
@commands.guild_only()
async def skip(ctx):
    _logger.info(f"Received command \"skip\" from {ctx.author.name}")
    if _song_queue:
        current = _song_queue.get_current()
        _song_queue.skip()
        if current:
            await ctx.send(f"⏩  {current.get_song_description()}")


@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    global _song_queue
    _logger.info(f"Received command \"shutdown\" from {ctx.author.name}")
    await ctx.send("Shutting down, goodbye!")
    await leave_channel(ctx)
    await bot.close()


@bot.event
async def on_command_error(ctx, error):
    _logger.error(f"Exception occurred during command: {error}")
    await ctx.send(f"Error: {error}")


async def join_channel(ctx, *, send_info=False):
    global _voice_client, _text_channel, _song_queue
    _text_channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    if _voice_client is None:
        _logger.debug(f"Joining channel {voice_channel.name}")
        _voice_client = await voice_channel.connect()
        _song_queue = SongQueue(on_song_over)
        _song_queue.set_voice_client(_voice_client)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")
    elif voice_channel != _voice_client.channel:
        _logger.debug(f"Moving to channel {voice_channel.name}")
        await _voice_client.move_to(voice_channel)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")


async def leave_channel(ctx, *, send_info=False):
    global _voice_client, _text_channel, _song_queue
    _text_channel = None
    if _voice_client is not None and _voice_client.is_connected():
        _logger.debug(f"Leaving channel {_voice_client.channel.name}")
        _song_queue = None
        await _voice_client.disconnect()
        if send_info:
            await ctx.send(f"Disconnected from {_voice_client.channel.name}!")
        _voice_client = None
