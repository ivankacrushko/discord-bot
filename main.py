
import disnake
from disnake.ext import commands
import os

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True


bot = commands.Bot(command_sync_flags=command_sync_flags)


@bot.event
async def on_ready():
    #await bot.sync_commands()
    print("The bot is ready!")

bot.load_extension("cogs.ping")
bot.load_extension("cogs.music")

bot.run(os.getenv('TOKEN'))