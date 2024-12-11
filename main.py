
import disnake
from disnake.ext import commands
import os

bot = commands.Bot()


@bot.event
async def on_ready():
    print("The bot is ready!")

bot.load_extension("cogs.ping")
bot.load_extension("cogs.music")

bot.run(os.getenv('TOKEN'))