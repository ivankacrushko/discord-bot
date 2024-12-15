from ast import alias
import disnake
from disnake.ext import commands
from youtubesearchpython import VideosSearch
import yt_dlp
import asyncio
import nacl
import threading
import os

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.music_queue = []
        self.stop_requested = False
        self.download_folder = 'downloads'

        self.YDL_OPTIONS = {'format': 'bestaudio/best',
                            'outtmpl': os.path.join(self.download_folder, '%(id)s.%(ext)s')}
        self.FFMPEG_OPTIONS = {'options': '-vn'}
        self.current_file_path = None

        


     
    def get_yt_audio_url(self, query):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            print('pobieram')

            info = ydl.extract_info(query, download=True)  # Pobieramy metadane oraz plik
            print('Pobieranie zakończone')

            # Przygotowanie ścieżki pliku
            file_path = os.path.join(self.download_folder, f"{info['id']}.{info['ext']}")
            return file_path, info.get('title', 'Nieznany tytuł')
        
    async def play_next(self, inter):
        

        if len(self.music_queue) > 0:
            self.is_playing = True
            file_path, title = self.music_queue.pop(0)
            self.file_path = file_path
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)

            if voice_client:
                prev = self.current_file_path

                self.current_file_path = file_path  # Zapisz ścieżkę aktualnego pliku
                audio_source = disnake.FFmpegPCMAudio(file_path)
                print(f'ODTWARZAM: {self.current_file_path}')
                voice_client.play(audio_source, after=lambda e: self.after_playing(e, inter, prev))
                await inter.channel.send(f'Teraz odtwarzam: **{title}**')
            else:
                self.is_playing = False
                self.current_file_path = None


        else:
            self.is_playing = False



    def after_playing(self, error, inter, prev):
        print(f'PRZEKAZUJE DO USUNIECIA: {prev}')
        if prev:
            print(f'USUWAMmmmm: {prev}')
            self.remove_file(prev)

        if self.stop_requested == False:
            asyncio.run_coroutine_threadsafe(self.play_next(inter), self.bot.loop)
        else:
            return

    def remove_file(self, file_path):
        """Funkcja usuwająca plik."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Usunięto plik: {file_path}")
            except Exception as e:
                print(f"Nie udało się usunąć pliku: {e}")

    async def skip_current_song(self, inter):
        """Pomiń aktualny utwór."""
        voice_client = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
        to_delete = self.current_file_path
        if voice_client and voice_client.is_playing():
            # Zatrzymaj bieżący utwór
            voice_client.stop()
            print("Pomijam aktualny utwór.")

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
                inter.followup.send(f"Nie udało się pobrać utworu: {e}"), self.bot.loop
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
            
            

    @commands.slash_command(description='Wyswietl aktualna kolejke')
    async def queue(self, inter: disnake.ApplicationCommandInteraction):
        if len(self.music_queue) == 0:
            await inter.response.send_message("Kolejka jest pusta!", ephemeral=True)
        else:
            queue_list = '\n'.join([f'{i+1}. {title}' for i, (_, title) in enumerate(self.music_queue)])
            await inter.response.send_message(f'**Kolejka odtwarzania:**\n{queue_list}')

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


        

def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))

        
