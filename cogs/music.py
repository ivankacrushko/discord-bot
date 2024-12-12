from ast import alias
import disnake
from disnake.ext import commands
from youtubesearchpython import VideosSearch
import yt_dlp
import asyncio
import nacl
import threading

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.music_queue = []

        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}


     
    def get_yt_audio_url(self, query):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            file_path = ydl.prepare_filename(info)
            ydl.download([query])
            return file_path, info.get('title', 'Nieznany tytuł')
        
    async def play_next(self, inter):
        

        if len(self.music_queue) > 0:
            self.is_playing = True
            file_path, title = self.music_queue.pop(0)
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)

            if voice_client:
                audio_source = disnake.FFmpegPCMAudio(file_path)
                voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(inter), self.bot.loop))
                await inter.channel.send(f'Teraz odtwarzam: **{title}**')
        else:
            self.is_playing = False
            

    @commands.slash_command(description='Odtwórz utwór')
    async def play(self, inter: disnake.ApplicationCommandInteraction, query: str):
        if not inter.author.voice:
            print('dupa1')
            await inter.response.send_message("Najpierw musisz dołączyć na kanał głosowy;)")
            
            return
        else: 
            print('dupa2')
            voice_channel = inter.author.voice.channel 
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
            if not voice_client:  
                print('dupa3')
                try:     
                    print('dupa4')
                    await voice_channel.connect()
                    
                except Exception as e:
                    print(f'BLAD {e}')
                    await inter.followup.send("Nie udało się dołączyć na kanał")
                    return  
            
            print('dupa5')
            await inter.response.defer()  
            try:
                url, title = self.get_yt_audio_url(query)
            except Exception as e:
                print(f'BLAD {e}')
                await inter.followup.send('Nie udało się pobrać informacji o tytule')
                return
            
            self.music_queue.append((url, title))
            await inter.followup.send(f"Dodano **{title}** do kolejki")

            if not self.is_playing:
                await self.play_next(inter)

            # try:
            #     if not voice_client.is_playing():
            #         ffmpeg_options = {
            #             'options': '-vn',
            #         }
            #         audio_source = disnake.FFmpegPCMAudio(url, **ffmpeg_options)
            #         await inter.followup.send(f"Odtwarzam: **{title}**")
            #         voice_client.play(audio_source, after=lambda e: print(f"Zakończono odtwarzanie: {e}"))
            #     else:
            #         print("juz odtwarzam")
            # except Exception as e:
            #     print(f"BLAD: {e}")

    @commands.slash_command()
    async def queue(self, inter: disnake.ApplicationCommandInteraction):
        if len(self.music_queue) == 0:
            await inter.response.send_message("Kolejka jest pusta!", ephemeral=True)
        else:
            queue_list = '\n'.join([f'{i+1}. {title}' for i, (_, title) in enumerate(self.music_queue)])
            await inter.response.send_message(f'**Kolejka odtwarzania:**\n{queue_list}')

        

def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))

        
