import discord

class RiffBot(discord.Client):
    voiceClient = None

    async def on_ready(self):
        print(f"Logged on as {self.user} :)")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content == "commands" and isinstance(message.channel, discord.DMChannel):
            await message.channel.send("Available commands:\n  !join")
            return

        if isinstance(message.channel, discord.TextChannel):
            try:
                voiceChannel = message.author.voice.channel
            except AttributeError:
                await message.channel.send(f"You don't seem to be in a voice channel.")
                return

            if message.content == "!join":
                self.voiceClient = await voiceChannel.connect()
                await message.channel.send(f"Connected to {voiceChannel.name}!")
                return