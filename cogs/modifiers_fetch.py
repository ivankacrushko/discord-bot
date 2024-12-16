import requests
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    return text

def fetch_modifier_data():
    url = "https://www.pathofexile.com/api/trade2/data/stats"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        # Sprawdzamy status odpowiedzi
        if response.status_code == 200:
            return response.json()  # Zwraca dane w formacie JSON
        else:
            print(f"Błąd odpowiedzi: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Błąd połączenia z API: {e}")
        return None

def parse_data(modifiers_data):
    if 'result' not in modifiers_data:
        print("Nie znaleziono sekcji 'result' w danych.")
        return

    #attributes = []
    modifiers_list = []
    for section in modifiers_data['result']:
        section_id = section.get('id', 'Brak ID')
        section_label = section.get('label', 'Brak Label')
        if 'entries' in section:
            for modifier in section['entries']:
                attributes = []
                modifier_id = modifier.get('id', 'Brak ID')
                text = modifier.get('text', 'Brak Tekstu')
                brackets = re.findall(r"\[([^\]]+)\]", text)
                
                for match in brackets:
                    if match not in attributes:
                        
                        attributes.append(match)
                text_without_brackets = re.sub(r'\[([^\]]+)\]', '$', text)

                if "Mana" in text and "Mana" not in attributes:
                    attributes.append("Mana")
                    text_without_brackets = text_without_brackets.replace("Mana", "$")
                if "Life" in text and "Life" not in attributes:
                    attributes.append("Life")
                    text_without_brackets = text_without_brackets.replace("Life", "$")
                
                
                
                modifier_dict = {
                    'modifier_id': modifier_id,
                    'attributes': attributes,
                    'text': text_without_brackets
                }

                modifiers_list.append(modifier_dict)
    
    return modifiers_list

def hash_numbers(text):
    """
    Zamienia pierwszą liczbę w tekście na #, a pozostałe liczby usuwa.
    """
    numbers = re.findall(r'[+-]?\d+', text)

    # Zamiana wyników na int
    numbers = [int(num) for num in numbers]
    if len(numbers) <= 1:
        numbers.append(None)
        
    is_hashed = False
    for letter in text:
        if letter.isdigit() and is_hashed:
            text = text.replace(letter, '', 1)
        elif letter.isdigit() and not is_hashed:
            text = text.replace(letter, '#', 1)
            is_hashed = True

    if numbers:
        return text, numbers
    return text, 0

def normalize_attribute(attribute):

    return attribute.replace(" ", "").lower()

def calculate_cosine_similarity(text1, text2):
    """
    Oblicza podobieństwo kosinusowe między dwoma tekstami.
    """
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    similarity = cosine_similarity(vectors)
    return similarity[0, 1]  # Zwraca wynik porównania text1 v

def contains_maximum(attribute):
    return 'maximum' in attribute.lower()

def find_modifier_id_by_attribute(modifiers_list, search_text, similarity_threshold=0.8):
    normalized_search_text = normalize_attribute(search_text)
    search_text, value = hash_numbers(normalized_search_text)
    
    # Przechodzimy przez listę modyfikatorów
    for modifier in modifiers_list:
        text = modifier['text']
        modifier_id = modifier['modifier_id']
        # Dla każdego modyfikatora, normalizujemy atrybuty
        for attribute in modifier['attributes']:
            attribute_parts = attribute.split('|') if '|' in attribute else [attribute]
            #attribute_parts = process_attribute(attribute)
            normalized_attribute = normalize_attribute(attribute)
           
            
            for part in attribute_parts:
                if not contains_maximum(part):
                    
                    normalized_attribute = normalize_attribute(part)
                    
                    
                        
                    # Jeśli znormalizowany atrybut modyfikatora pasuje do zapytania, zwracamy ID modyfikatora
                    if normalized_attribute in normalized_search_text:

                        remaining_search_text = re.sub(re.escape(normalize_attribute(part)), '$', search_text, flags=re.IGNORECASE).strip()

                        similarity = calculate_cosine_similarity(normalize_attribute(remaining_search_text), normalize_attribute(text))
                        # if similarity > 0.8:
                            #print(f"Atrybut: {modifier_id}, Cosine Similarity: {similarity}")

                        
                        

                        # print(f'Szukane: {search_text}')
                        # print(f'Usuniete: {normalize_attribute(part)}')
                        # print(f'Znormalizowane zap:{normalize_attribute(remaining_search_text)}')
                        # print(f'Znormalizowany atr: {normalize_attribute(text)}')
                        # print(f'Text: {text}')
                        # print(f'Modyfukatory: {modifier['attributes']}')
                        # print('\n')
                        if normalize_attribute(text) in normalize_attribute(remaining_search_text) :
                            stat_query = {
                                'id': modifier_id,
                                'value':{}
                            }
                            if value[0]:
                                stat_query['value']['min'] = value[0]
                            if value[1]:
                                stat_query['value']['max'] = value[1]
                            print(stat_query)
                            return stat_query

    
    
    return None

def extract_numbers(text):
    """
    Funkcja wyciąga wszystkie liczby z tekstu, niezależnie od ich ilości.
    Obsługuje przypadki z jedną, dwiema lub większą ilością liczb.
    """
    # Wyszukiwanie liczb w tekście
    numbers = re.findall(r'\b\d+\b', text)

    # Zamiana wyników na int
    numbers = [int(num) for num in numbers]

    if numbers:
        return numbers  # Zwróć listę znalezionych liczb
    else:
        print("Nie znaleziono liczb w tekście.")
        return None




modifiers_data = fetch_modifier_data()
modifiers_list = parse_data(modifiers_data)
for item in modifiers_list:
    #print(item)
    pass


search_text = {
    '+38 to maximum Energy Shield',
    '+110 to Accuracy Rating',
    '+54 to maximum Mana',
    '+13% to Cold Resistance',
    '+12% to Lightning Resistance',
    'Gain 4 Life per Enemy Hit with Attacks',
    "Adds 7 to 12 Fire damage to Attack"
}

def query_set(mods):
    modifiers_data = fetch_modifier_data()
    modifiers_list = parse_data(modifiers_data)
    query_list = []
    err = 0
    err_mod = []
    for mod in mods:
        query = find_modifier_id_by_attribute(modifiers_list, mod)

        if query:
            print(f"Znaleziono: {mod}\n")
            query_list.append(query)
        elif query == None:
            err +=1
            err_mod.append(mod)
    if err > 0:
        error = f'Nieznaleziono: {err}: {err_mod}'
    else:
        error = None

    return query_list, error


    
    


