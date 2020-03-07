from discord.ext import commands


def is_in_voice_channel():
    async def predicate(ctx):
        try:
            return ctx.author.voice.channel is not None
        except AttributeError:
            return False
    return commands.check(predicate)


def bot_is_in_voice_channel():
    async def predicate(ctx):
        try:
            return ctx.voice_client is not None
        except AttributeError:
            return False
    return commands.check(predicate)
