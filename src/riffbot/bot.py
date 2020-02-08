from discord.ext import commands

from . import checks
from audio.song_queue import SongQueue
from audio.endpoints.youtube import YouTubeEndpoint

bot = commands.Bot(command_prefix="!")

_voice_client = None
_explicit_join = False


def on_song_over(queue_length):
    if queue_length == 0 and not _explicit_join:
        leave()


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
async def play(ctx, url):
    global _song_queue, _explicit_join
    if _voice_client is None:
        _explicit_join = False
        await join_channel(ctx)
    endpoint = YouTubeEndpoint(url)
    pos = _song_queue.enqueue(endpoint)
    if pos == 0:
        await ctx.send(f"[▶] {endpoint.get_song_name()}")
    else:
        await ctx.send(f"[{pos}] {endpoint.get_song_name()}")


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
