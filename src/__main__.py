import os
from dotenv import load_dotenv
from riffbot.bot import bot

def main():
    # Read environment variables from .env file
    load_dotenv()
    # Load the discord authorization token from DISCORD_TOKEN environment variable
    token = os.getenv("DISCORD_TOKEN")

    # Run the bot
    bot.run(token)

if __name__ == "__main__":
    main()