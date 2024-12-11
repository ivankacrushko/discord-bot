from ast import alias
import disnake
from disnake.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import nacl

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.is_paused = False

        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}


     
    def get_yt_audio_url(self, query):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            return info['url'], info.get('title', 'Nieznany tytuł')
            

    @commands.slash_command(description='Odtwórz utwór')
    async def play(self, inter: disnake.ApplicationCommandInteraction, query: str):
        if not inter.author.voice:
            await inter.response.send_message("Najpierw musisz dołączyć na kanał głosowy;)")
            return
        else:        
            voice_channel = inter.author.voice.channel   
            try:     
                await voice_channel.connect()
                voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
            except disnake.ClientException:
                await inter.followup.send("Nie udało się dołączyć na kanał")
                return  
              
            await inter.response.defer()  
            try:
                url, title = self.get_yt_audio_url(query)
            except Exception as e:
                await inter.followup.send('Nie udało się pobrać informacji o tytule')
                return
            try:
                if not voice_client.is_playing():
                    ffmpeg_options = {
                        'options': '-vn',
                    }
                    audio_source = disnake.FFmpegPCMAudio(url, **ffmpeg_options)
                    await inter.followup.send(f"Odtwarzam: **{title}**")
                    voice_client.play(audio_source, after=lambda e: print(f"Zakończono odtwarzanie: {e}"))
                else:
                    print("juz odtwarzam")
            except Exception as e:
                print(f"BLAD: {e}")

        

def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))

        
