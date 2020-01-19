import discord
from discord.ext import commands

from riffbot import checks

bot = commands.Bot(command_prefix="!")

_voiceClient = None

@bot.event
async def on_ready():
    print(f"Logged on as {bot.user} :)")

@bot.command(help="Join the issuer's voice channel.")
@commands.guild_only()
#@commands.bot_has_permissions(connect=True)
@checks.is_in_voice_channel()
async def join(ctx):
    global _voiceClient
    voiceChannel = ctx.author.voice.channel
    if _voiceClient is None:
        _voiceClient = await voiceChannel.connect()
        _voiceClient.stop()
    else:
        _voiceClient.stop()
        await _voiceClient.move_to(voiceChannel)
    await ctx.send(f"Connected to {voiceChannel.name}!")

@bot.command(help="Leave the current voice channel.")
@commands.guild_only()
async def leave(ctx):
    if _voiceClient is not None and _voiceClient.is_connected():
        await _voiceClient.disconnect()
        await ctx.send(f"Disconnected from {_voiceClient.channel.name}!")

@bot.command(help="Log out and shut down the bot. This can only be done by admins and is irreversible.")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    print(f"Shutdown triggered by {ctx.author.name} …")
    await ctx.send("Shutting down, goodbye!")
    await bot.close()

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {error}")