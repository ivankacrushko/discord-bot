from ast import alias
import disnake
from disnake.ext import commands, tasks
from youtubesearchpython import VideosSearch
import yt_dlp
import asyncio
import nacl
import threading
import os
import time

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.music_queue = []
        self.stop_requested = False
        self.download_folder = 'downloads'
        self.last_played_time = time.time()
        self.inactivity_check.start()
        self.text_channels = {}

        self.YDL_OPTIONS = {'format': 'bestaudio/best',
                            'outtmpl': os.path.join(self.download_folder, '%(id)s.%(ext)s')}
        self.FFMPEG_OPTIONS = {'options': '-vn'}
        self.current_file_path = None

        


     
    def get_yt_audio_url(self, query):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(query, download=True)  # Pobieramy metadane oraz plik
                
            except Exception as e:
                print(f'Wystapil blad podczas pobierania: {e}')
                return e

            # Przygotowanie ścieżki pliku
            file_path = os.path.join(self.download_folder, f"{info['id']}.{info['ext']}")
            return file_path, info.get('title', 'Nieznany tytuł')
        
    async def play_next(self, inter):
        

        if len(self.music_queue) > 0:
            self.is_playing = True
            file_path, title = self.music_queue.pop(0)
            self.file_path = file_path
            self.last_played_time = time.time()
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)

            if voice_client:
                prev = self.current_file_path

                self.current_file_path = file_path  # Zapisz ścieżkę aktualnego pliku
                audio_source = disnake.FFmpegPCMAudio(file_path)
                print(f'ODTWARZAM: {self.current_file_path}')
                voice_client.play(audio_source, after=lambda e: self.after_playing(e, inter, prev))
                await self.send_to_text_channel(inter, f"Teraz odtwarzam: **{title}**")
            else:
                self.is_playing = False
                self.current_file_path = None


        else:
            self.is_playing = False



    def after_playing(self, error, inter, prev):
        if prev:
            self.remove_file(prev)

        if self.stop_requested == False:
            asyncio.run_coroutine_threadsafe(self.play_next(inter), self.bot.loop)
            return
        else:
            return
        
    async def send_to_text_channel(self, inter, message):
        guild_id = inter.guild.id
        channel_id = self.text_channels.get(guild_id)
        if channel_id:
            channel = (
            inter.guild.get_channel(channel_id) if channel_id else inter.channel
        )
            if channel:
                await channel.send(message)
            else:
                print(f"Nie znaleziono kanału o ID: {channel_id}")

    def remove_file(self, file_path):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Usunięto plik: {file_path}")
            except Exception as e:
                print(f"Nie udało się usunąć pliku: {e}")

    async def skip_current_song(self, inter):
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
        
        if voice_client and voice_client.is_playing():
            # Zatrzymaj bieżący utwór
            voice_client.stop()
            #await inter.response.send_message("Pominięto utwór. Odtwarzam następny...", ephemeral=True)
            await self.send_to_text_channel(inter, "Pominięto utwór. Odtwarzam następny...")

    @tasks.loop(seconds=60)
    async def inactivity_check(self):
        # Jeśli od ostatniego odtwarzania minęło 5 minut
        if self.is_playing == False and (time.time() - self.last_played_time) > 300:
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=self.bot.guilds[0])
            if voice_client:
                await voice_client.disconnect()


    def download_song_in_background(self, query, inter):
    

        try:
            url, title = self.get_yt_audio_url(query)
            self.music_queue.append((url, title))  # Dodaj utwór do kolejki
            asyncio.run_coroutine_threadsafe(
                inter.followup.send(f"Dodano do kolejki: **{title}**"), self.bot.loop
                
            )
            
            

            # Jeśli nie jest nic odtwarzane, zacznij odtwarzanie
            if not self.is_playing:
                asyncio.run_coroutine_threadsafe(self.play_next(inter), self.bot.loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                inter.followup.send(f"Nie udało się pobrać utworu, czy napewno podajesz poprawny link?"), self.bot.loop
                
            )
            
            

    @commands.slash_command(description='Odtwórz utwór')
    async def play(self, inter: disnake.ApplicationCommandInteraction, query: str):
        self.stop_requested = False

        if not inter.author.voice:
            await inter.response.send_message("Najpierw musisz dołączyć na kanał głosowy;)")

            
            return
        else: 
            voice_channel = inter.author.voice.channel 
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
            if not voice_client:  
                try:     
                    await voice_channel.connect()
                    
                except Exception as e:
                    print(f'BLAD {e}')
                    await inter.followup.send("Nie udało się dołączyć na kanał")
                    return 
                
            await inter.response.defer()  
            try:
                threading.Thread(target=self.download_song_in_background, args=(query, inter)).start()
                
            except Exception as e:
                print(f'BLAD {e}')
                await inter.followup.send('Nie udało się pobrać informacji o tytule')
                return
            
    @commands.slash_command(description="Ustaw kanał tekstowy dla powiadomień o muzyce.")
    async def set_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        # Zapisujemy ID kanału w słowniku
        print(channel.id)
        self.text_channels[inter.guild.id] = channel.id
        await inter.response.send_message(f"Ustawiono kanał tekstowy: {channel.mention}")

            
            

    @commands.slash_command(description='Wyswietl aktualna kolejke')
    async def queue(self, inter: disnake.ApplicationCommandInteraction):
        if len(self.music_queue) == 0:
            await inter.response.send_message("Kolejka jest pusta!", ephemeral=True)
        else:
            queue_list = '\n'.join([f'{i+1}. {title}' for i, (_, title) in enumerate(self.music_queue)])
            await self.send_to_text_channel(inter, f'**Kolejka odtwarzania:**\n{queue_list}')
            

    @commands.slash_command(description='Pomin se utwor')
    async def skip(self, inter: disnake.ApplicationCommandInteraction):
        """Pomija bieżący utwór i przechodzi do następnego w kolejce."""
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
        if not voice_client:
            await inter.response.send_message("Bot nie jest na kanale głosowym.")
            return
        
        if not voice_client.is_playing():
            await inter.response.send_message("Nie ma żadnego utworu do pominięcia.")
            return

        # Zatrzymaj obecnie odtwarzany utwór i przejdź do następnego
        await self.skip_current_song(inter)

    @commands.slash_command(description='Wywal bota')
    async def leave(self, inter: disnake.ApplicationCommandInteraction):
        self.is_playing = False

        voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
        if not voice_client:
            await inter.response.send_message("Przeciez mnie nie ma lol", ephemeral=True)
            return
        
        for music in self.music_queue:
            file_path = music[0]

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Usunięto plik: {file_path}")
                except Exception as e:
                    print(f"Nie udało się usunąć pliku2: {e}")


        # Jeśli aktualnie odtwarzany utwór istnieje, poczekaj na zakończenie odtwarzania
        if voice_client.is_playing():
            #self.stop_requested = True
            voice_client.stop()

        await asyncio.sleep(1)

        for file in os.listdir(self.download_folder):
            print(file)
            self.remove_file(os.path.join(self.download_folder, file))
            
        
        
                
        self.music_queue = []
        self.is_playing = False
        await voice_client.disconnect()
        await inter.response.send_message("Peace out.")

    @leave.before_invoke
    async def stop_inactivity_check(self, inter):
        # Zatrzymanie timera, gdy bot wychodzi z kanału
        self.inactivity_check.cancel()

    @leave.after_invoke
    async def restart_inactivity_check(self, inter):
        # Ponowne uruchomienie timera po ponownym dołączeniu bota
        self.inactivity_check.start()


        

def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))

        
