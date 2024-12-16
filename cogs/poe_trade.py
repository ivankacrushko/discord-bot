from disnake.ext import commands
from disnake.ui import Modal, TextInput
from disnake import TextInputStyle
import disnake
import requests
import json
#import parse_item as pi
import cogs.parse_item as pi
import cogs.modifiers_fetch as mf
import aiohttp
import json

class PriceCheckModal(Modal):
    def __init__(self, callback_function):
        # Modal z jednym polem tekstowym
        self.callback_function = callback_function
        components = [
            TextInput(
                label="Wklej tutaj dane przedmiotu",
                placeholder="Item Class: Gloves\nRarity: Rare\nCorruption Hold\nIntricate Gloves\n--------\n...",
                style=TextInputStyle.paragraph,
                custom_id="price_check_input"
            )
        ]
        super().__init__(title="Price Check", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        # Odbieramy dane z modala
        query = inter.text_values["price_check_input"]
        

        # Przetwarzanie danych
        await self.callback_function(inter, query)

class PoeTrade(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def search_items(self, league, item_type, rarity=None, quality_min=None, level_min=None, mods=None):
    # URL do wyszukiwania
        url = f"https://www.pathofexile.com/api/trade2/search/{league}"
        
        # Parametry wyszukiwania
        query = {
            "query": {
                "status": {"option": "online"},
                'type': item_type,
                'stats': [{
                    'type': 'and',
                    'filters': []
                }],
                'filters':{                
                    #'weapon_filters': {'filters':{}},
                    #'armour_filters': {'filters':{}},
                    #'socket_filters': {'filters':{}},
                    'req_filters':{'filters': {}},
                    'misc_filters':{'filters': {}},
                    'type_filters': {'filters': {}},
                }
            },
            "sort": {"price": "asc"}
        }

        if rarity:
            query["query"]["filters"]["type_filters"]['filters']["rarity"] = {"option": rarity}

        # Dodajemy minimalną jakość, jeśli jest podana
        if quality_min:
            query["query"]["filters"]["misc_filters"]['filters']["quality"] = {"min": quality_min}

        # Dodajemy minimalny poziom, jeśli jest podany
        if level_min:
            query["query"]["filters"]["misc_filters"]['filters']["ilvl"] = {"min": level_min}

        if mods:
            for mod in mods:
                for section in query['query']['stats']:
                    section['filters'].append(mod)
                    break

        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"
        }
        #print(json.dumps(query, indent=2))
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=query) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["id"], data["result"]
                else:
                    print("Błąd wyszukiwania:", response.status, await response.text())
                    return None, None

    # Funkcja pobierająca szczegóły przedmiotów
    async def fetch_item_details(self, search_id, item_ids):
        # Pobieramy szczegóły dla maksymalnie 10 ID na raz (ograniczenie API)
        ids_to_fetch = ",".join(item_ids[:3])  # Można rozszerzyć obsługę większej liczby wyników
        url = f"https://www.pathofexile.com/api/trade2/fetch/{ids_to_fetch}?query={search_id}"

        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"
    }
        
        # Wysłanie zapytania GET
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    #print(json.dumps(data, sort_keys=True, indent=4))
                    return data.get("result", [])
                else:
                    print("Błąd pobierania szczegółów:", response.status, await response.text())
                    return []
        
    def format_item_details(self, item):
        
        price_info = item.get("listing", {}).get("price", {})
        seller_info = item.get("listing", {}).get("account", {})

        item_info = item.get("item", {})

        item_name = item_info.get("name", "Brak nazwy")
        item_type_line = item_info.get("typeLine", "Brak typu")
        item_rarity = item_info.get("rarity", "Brak rzadkości")
        item_level = item_info.get("ilvl", "Brak poziomu")
        item_id = item_info.get("id", "Brak ID")

        seller_name = seller_info.get("name", "Nieznany sprzedawca")

        price_amount = price_info.get("amount", "Brak ceny")
        price_currency = price_info.get("currency", "Brak waluty")


        quality = None
        if "properties" in item_info:
            for prop in item_info["properties"]:
                #print(f'PROP:{prop}')
                if prop.get("name") == "[Quality]":
                    
                    quality = prop.get("values", [])[0][0]

        results = {
            'name':item_name,
            'rarity':item_rarity,
            'ilvl': item_level,
            'quality':quality,
            'typeLine':item_type_line,
            'id': item_id,
            'currency': price_currency,
            'amount':price_amount,
            'seller': seller_name,
        }
        
        gs_list = []
        granted_skills = item.get('granted_skills', [])
        if granted_skills:
            for skill in granted_skills:
                gs_list.append(skill)
                
        em_list = []
        explicit_mods = item_info.get('explicitMods', [])
        if explicit_mods:
            for mod in explicit_mods:
                
                em_list.append(mod)


        data = [results, gs_list, em_list]

        return data

    # Główna funkcja programu
    async def look_for_item(self, inter, item_text):
        # Parametry wyszukiwania
        league = "Standard"  # Nazwa ligi

        
        item_details, item_mods = pi.parse_item_details(item_text)
        #print(item_details)

        mods, error = mf.query_set(item_mods)
        #print(item_details)


        
        
        #print(f"Wyszukiwanie przedmiotu: {item_name} ({item_type}) w lidze {league}...")
        
        # Krok 1: Wyszukiwanie przedmiotów
        search_id, item_ids = await self.search_items(league, item_details['item_name'], item_details['rarity'],
                                        item_details['quality'], item_details['ilvl'], mods)
        
        if not search_id or not item_ids:
            await inter.response.send_message("Brak wyników wyszukiwania.", ephemeral=True)
            return
        
        #print(f"Znaleziono {len(item_ids)} wyników. Pobieram szczegóły dla pierwszych 10...")
        
        # Krok 2: Pobieranie szczegółów przedmiotów
        details = await self.fetch_item_details(search_id, item_ids)
        
        if not details:
            await inter.response.send_message("Nie udało się pobrać szczegółów przedmiotów.", ephemeral=True)
            return
        result = []
        for item in details:
            result.append(self.format_item_details(item))

        return result, error
    
    def create_item_embed(self, item):
        gs = item[1]
        em = item[2]
        item = item[0]
        embed = disnake.Embed(title=f"{item.get('name')} ({item.get('typeLine')})", color=0x00FF00)  # Możesz ustawić dowolny kolor
        embed.add_field(name="Rzadkość", value=item.get('rarity', 'Brak danych'), inline=True)
        embed.add_field(name="Poziom", value=item.get('ilvl', 'Brak danych'), inline=True)
        embed.add_field(name="Quality", value=item.get('quality', 'Brak danych'), inline=True)
        embed.add_field(name="Cena", value=f"{item.get('amount', 'Brak ceny')} {item.get('currency', 'Brak waluty')}", inline=False)
        embed.add_field(name="Sprzedawca", value=item.get('seller', 'Brak danych'), inline=False)

        
        if gs:
            for skill in gs:

                skills = "\n".join([f"- {skill}"])
            embed.add_field(name="Umiejętności przyznawane przez przedmiot", value=skills, inline=False)

        # Modyfikacje przedmiotu (jeśli są dostępne)
        if em:
            mods = "\n".join([f"- {mod}" for mod in em])
            embed.add_field(name="Umiejętności przyznawane przez przedmiot", value=mods, inline=False)
        # Dodaj inne szczegóły, np. modyfikacje, umiejętności itp.
        return embed

    @commands.slash_command(description='Wyszukaj przedmiot w POE2')
    async def price_check(self, inter: disnake.ApplicationCommandInteraction):
        async def handle_query(inter, query):
            try:
                # Wywołanie głównej funkcji przetwarzającej wprowadzone dane
                results, error = await self.look_for_item(inter, query)
                #print(results)
                if not results:
                    await inter.response.send_message("Nie znaleziono żadnych wyników.", ephemeral=True)
                    return
                
                embeds = []

                for item in results:
                    embed = self.create_item_embed(item)
                    embeds.append(embed)
                print(error)
                if error:
                    error_embed = disnake.Embed(title=f"{error}", color=0x00FF00)
                    embeds.append(error_embed)

                # Wysłanie embeda
                await inter.response.send_message(
                    embeds=embeds,  # Lista embedów
                    ephemeral=True  # Opcjonalnie, jeśli wiadomość ma być widoczna tylko dla użytkownika
                )
                    
            except Exception as e:
                await inter.response.send_message(f"Wystąpił błąd podczas przetwarzania: {e}", ephemeral=True)

        # Wywołanie modala
        modal = PriceCheckModal(callback_function=handle_query)
        await inter.response.send_modal(modal)
            

def setup(bot: commands.Bot):
    bot.add_cog(PoeTrade(bot))