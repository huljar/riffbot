import discord
from discord.ext import commands

from riffbot import checks
from audio.endpoints.youtube import YouTubeEndpoint

bot = commands.Bot(command_prefix="!")

_voice_client = None
_explicit_join = False


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user} :)")


@bot.command(help="Join the issuer's voice channel.")
@commands.guild_only()
# @commands.bot_has_permissions(connect=True)
@checks.is_in_voice_channel()
async def join(ctx):
    global _voice_client, _explicit_join
    voiceChannel = ctx.author.voice.channel
    if _voice_client is None:
        _voice_client = await voiceChannel.connect()
    else:
        await _voice_client.move_to(voiceChannel)
    await ctx.send(f"Connected to {voiceChannel.name}!")
    _explicit_join = True


@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    global _explicit_join
    if _voice_client is not None and _voice_client.is_connected():
        await _voice_client.disconnect()
        await ctx.send(f"Disconnected from {_voice_client.channel.name}!")
        _explicit_join = False


@bot.command(help="Play the song at the given URL.")
@commands.guild_only()
async def play(ctx, url):
    # youtube = YouTubeEndpoint(url)
    # audioSource = discord.FFmpegPCMAudio("test.m4a")
    # _voice_client.play(audioSource)
    pass


@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    print(f"Shutdown triggered by {ctx.author.name} …")
    await ctx.send("Shutting down, goodbye!")
    await bot.close()


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {error}")
    raise error
