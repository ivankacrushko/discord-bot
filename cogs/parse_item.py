import re

def parse_item_details(item_text):
    # Inicjalizacja słownika do przechowywania danych przedmiotu
    item_data = {}
    lines = item_text.splitlines()
    item_mods = set()

    if len(lines) >= 4:
        item_data['item_type'] = lines[4].strip()
        item_text = item_text.replace(f"{item_data['item_type']}", "")

    if len(lines) >= 3:
        item_data['item_name'] = lines[3].strip()
        item_text = item_text.replace(f"{item_data['item_name']}", "")

    item_text = item_text.replace(f"(augmented)", "")
    item_text = item_text.replace(f"Requirements", "")
   
    # 1. Typ przedmiotu
    item_class_match = re.search(r"Item Class:\s*(.+)", item_text)
    if item_class_match:
        item_data['item_class'] = item_class_match.group(1)
        item_text = item_text.replace(f"Item Class: {item_data['item_class']}", "")
    
    # 2. Rzadkość przedmiotu
    rarity_match = re.search(r"Rarity:\s*(\w+)", item_text)
    if rarity_match:
        item_data['rarity'] = rarity_match.group(1)
        item_text = item_text.replace(f"Rarity: {item_data['rarity']}", "")
    
    # 3. Jakość
    quality_match = re.search(r"Quality:\s*\+(\d+)%", item_text)
    if quality_match:
        item_data['quality'] = int(quality_match.group(1))
        item_text = item_text.replace(f"Quality: +{item_data['quality']}%", "")
    
    
    # 4. Poziom przedmiotu (Item Level)
    ilvl_match = re.search(r"Item Level:\s*(\d+)", item_text)
    if ilvl_match:
        item_data['ilvl'] = int(ilvl_match.group(1))
        item_text = item_text.replace(f"Item Level: {item_data['ilvl']}", "")
    
    # 5. Wymagania (Level, Str, Dex, Int)
    req_lvl_match = re.search(r"Level:\s*(\d+)", item_text)
    if req_lvl_match:
        item_data['req_lvl'] = int(req_lvl_match.group(1))
        item_text = item_text.replace(f"Level: {item_data['req_lvl']}", "")
    
    req_str_match = re.search(r"Str:\s*(\d+)", item_text)
    if req_str_match:
        item_data['req_str'] = int(req_str_match.group(1))
        item_text = item_text.replace(f"Str: {item_data['req_str']}", "")
    
    req_dex_match = re.search(r"Dex:\s*(\d+)", item_text)
    if req_dex_match:
        item_data['req_dex'] = int(req_dex_match.group(1))
        item_text = item_text.replace(f"Dex: {item_data['req_dex']}", "")
    
    req_int_match = re.search(r"Int:\s*(\d+)", item_text)
    if req_int_match:
        item_data['req_int'] = int(req_int_match.group(1))
        item_text = item_text.replace(f"Int: {item_data['req_int']}", "")
    
    # 6. Sockets
    sockets_match = re.search(r"Sockets:\s*([A-Za-z]+)", item_text)
    if sockets_match:
        item_data['sockets'] = sockets_match.group(1)
        item_text = item_text.replace(f"Sockets: {item_data['sockets']}", "")
    
    # 7. Zwiększenie Energy Shield (jeśli jest)
    es_match = re.search(r"Energy Shield:\s*(\d+)", item_text)
    if es_match:
        item_data['es'] = int(es_match.group(1))
        item_text = item_text.replace(f"Energy Shield: {item_data['es']}", "")
    
    
    
    # 11. Korozja (Corruption)
    corruption_match = re.search(r"Corrupted", item_text)
    if corruption_match:
        item_data['isCorrupted'] = True
        item_text = item_text.replace(f"Corrupted", "")
    else:
        item_data['isCorrupted'] = False

    # 12. Identifikacja (Identified)
    unidentified_match = re.search(r"Unidentified", item_text)
    if unidentified_match:
        item_data['isUnidentified'] = True
        item_text = item_text.replace(f"Unidentified", "")
    else:
        item_data['isUnidentified'] = False

    # 13. Szaklowanie (Crafted)
    crafted_match = re.search(r"Crafted", item_text)
    if crafted_match:
        item_data['isCrafted'] = True
    else:
        item_data['isCrafted'] = False
    
    # 14. Zaklęcie (Enchanted)
    enchanted_match = re.search(r"Enchanted", item_text)
    if enchanted_match:
        item_data['isEnchanted'] = True
    else:
        item_data['isEnchanted'] = False

    lines = item_text.splitlines()

    for line in lines:

        special_modifier_matches = re.findall(r'([A-Za-z\s]+[\d+%]+[A-Za-z\s]+)', line)
        for mod in special_modifier_matches:
            item_mods.add(mod.strip())
            print(mod.strip())  # Możesz odkomentować, jeśli chcesz zobaczyć te modyfikatory
            line = line.replace(f"{mod.strip()}", "")
    

    return item_data, item_mods

# Przykładowe dane przedmiotu:

