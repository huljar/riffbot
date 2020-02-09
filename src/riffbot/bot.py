import asyncio
import functools
import typing

from discord.ext import commands

from . import checks
from audio.song_queue import SongQueue
from audio.endpoints.youtube import YouTubeEndpoint

bot = commands.Bot(command_prefix="!")

_voice_client = None
_explicit_join = False


def on_song_over():
    if _song_queue.size() > 0:
        pass  # TODO: post in correct channel which song is playing next
    elif not _explicit_join:
        asyncio.get_event_loop().run_until_complete(leave_channel(None))


_song_queue = SongQueue(on_song_over)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user} :)")


@bot.command(help="Join the issuer's voice channel.")
@commands.guild_only()
# @commands.bot_has_permissions(connect=True)
@checks.is_in_voice_channel()
async def join(ctx):
    global _explicit_join
    _explicit_join = True
    await join_channel(ctx, send_info=True)


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    global _explicit_join
    _explicit_join = False
    await leave_channel(ctx, send_info=True)


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
async def play(ctx, url: typing.Optional[str]):
    global _explicit_join
    if url is None or url == "":
        # Resume paused song
        player = _song_queue.get_player()
        if player is not None:
            player.resume()
            await ctx.send(f"▶ {player.get_endpoint().get_song_description()}")
    else:
        if _voice_client is None:
            _explicit_join = False
            await join_channel(ctx)
        endpoint = YouTubeEndpoint(url)
        pos = _song_queue.enqueue(endpoint)
        if pos == 0:
            await ctx.send(f"▶ {endpoint.get_song_description()}")
        else:
            await ctx.send(f"[{pos}] {endpoint.get_song_description()}")


@bot.command(help="Pause the currently playing song.")
@commands.guild_only()
async def pause(ctx):
    player = _song_queue.get_player()
    player.pause()
    await ctx.send(f"⏸ {player.get_endpoint().get_song_description()}")


@bot.command(help="Show the current contents of the queue.")
async def queue(ctx):
    songs = _song_queue.get_all()
    if len(songs) == 0:
        await ctx.send("No songs are currently enqueued!")
    else:
        ret = f"▶ {songs[0].get_song_description()}"
        ret = functools.reduce(lambda acc, val: acc +
                               f"\n[{val[0]}] {val[1].get_song_description()}", enumerate(songs[1:]), ret)
        await ctx.send(ret)


@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    global _song_queue
    print(f"Shutdown triggered by {ctx.author.name} …")
    await ctx.send("Shutting down, goodbye!")
    _song_queue = None
    await bot.close()


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {error}")
    raise error


async def join_channel(ctx, *, send_info=False):
    global _voice_client
    voice_channel = ctx.author.voice.channel
    if _voice_client is None:
        _voice_client = await voice_channel.connect()
        _song_queue.set_voice_client(_voice_client)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")
    elif voice_channel != _voice_client.channel:
        await _voice_client.move_to(voice_channel)
        if send_info:
            await ctx.send(f"Connected to {voice_channel.name}!")


async def leave_channel(ctx, *, send_info=False):
    if _voice_client is not None and _voice_client.is_connected():
        await _voice_client.disconnect()
        if send_info:
            await ctx.send(f"Disconnected from {_voice_client.channel.name}!")
