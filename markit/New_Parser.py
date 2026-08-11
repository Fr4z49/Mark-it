import re

try:
    from . import NewPdfPrinter
except ImportError:
    import NewPdfPrinter

def parse_inline(line, block_type):
    line = line.replace("\t", "   ")

    pattern = re.compile(
        r"\*\*(?P<bold>.+?)\*\*"
        r"|"
        r"\_\-(?P<strikethru>.+?)\-\_" 
        r"|"
        r"\_\_(?P<underline>.+?)\_\_"
        r"|"
        r"\=\=(?P<highlight>.+?)\=\="
        r"|"
        r"\\\\(?P<italic>.+?)\\\\"
        r"|"
        r"`(?P<code>.+?)`"
        r"|"
        r"(?P<arrow>-->)"
        r"|"
        r"(?P<link>\((?P<l_text>[^)]+)\)\^(?P<l_url>https?://[^\s\)]+))"
        r"|"
        r"(?P<i_style>\((?P<text>[^)]+)\)(?P<type>[$#])(?P<prop>[^\s$#]+))"
        r"|"
        r"(?P<E_bold>\\\*\*)"
        r"|"
        r"(?P<E_underline>\\\_\_)"
        r"|"
        r"(?P<E_code>\\`)"
        r"|"
        r"(?P<E_quote>\\>)"
        r"|"
        r"(?P<E_header>\\#)"
    
    )

    result = []
    last_index = 0

    for m in pattern.finditer(line):
        start, end = m.span()

        if start > last_index:
            result.append({'type': 'text', 'value': line[last_index:start]})

        if m.group("bold"):
            result.append({'type': 'bold', 'value': m.group("bold")})
        
        elif m.group("italic"):
            result.append({'type': 'italic', 'value': m.group("italic")})

        elif m.group("strikethru"):
            result.append({'type': 'strikethru', 'value': m.group("strikethru")})
        
        elif m.group("underline"):
            result.append({'type': 'underline', 'value': m.group("underline")})
        
        elif m.group("highlight"):
            result.append({'type': 'highlight', 'value': m.group("highlight")})

        elif m.group("code"):
            result.append({'type': 'code', 'value': m.group("code")})

        elif m.group("arrow"):
            result.append({'type': 'text', 'value':"➡"})
        
        elif m.group("l_url"):
            result.append({'type': 'link', 'path':m.group("l_url"), 'value':m.group("l_text")})
        
        elif m.group("i_style"): #inline style
            if m.group("type") == "#":
                result.append({'type': 'color', 'value':m.group("text"), 'color':m.group("prop")})
            elif m.group("type") == "$":
                result.append({'type': 'style', 'value':m.group("text"), 'property':m.group("prop")})
        
        elif m.group("E_bold"):
            result.append({'type': 'text', 'value':"**"})

        elif m.group("E_underline"):
            result.append({'type': 'text', 'value':"__"})
        elif m.group("E_code"):
            result.append({'type': 'text', 'value':"`"})
        elif m.group("E_quote"):
            result.append({'type': 'text', 'value':">"})

        elif m.group("E_header"):
            result.append({'type': 'text', 'value':"#"})

        

        last_index = end

    if last_index < len(line):
        result.append({'type': 'text', 'value': line[last_index:]})

    return result


def parse(lines):
    parsed_blocks = []
    current_block = None

    for line in lines:
        # 1. Gestione Blocco Multiline Code attivo
        line = line.replace("\t", "    ")

        raw_line = line.replace("    ", "\t")
        if current_block and current_block['type'] == 'Multiline_code':
            if line.lstrip().startswith("```"):
                # Rimuove l'ultimo newline superfluo prima di chiudere
                if current_block['content'] and current_block['content'][-1]['type'] == 'newline':
                    current_block['content'].pop()
                parsed_blocks.append(current_block)
                current_block = None
            else:
                # Se il blocco non è vuoto, inserisce il blocco newline prima della nuova linea
                if current_block['content']:
                    current_block['content'].append({'type': 'newline', 'value': '\n'})
                current_block['content'].append({'type': 'text', 'value': line})
            continue

        # 2. Linea Vuota (Separatore di blocchi)
        if line.strip() == "":
            if current_block:
                parsed_blocks.append(current_block)
                current_block = None
            continue

        stripped = line.lstrip()
        img_match = re.fullmatch(r'!\((.*?)\)\[(\d+)\]', stripped)
        list_match = re.match(r"^(\t*)(-|\[[ xX]?\])\s+(.*)", raw_line)
        table_match = re.match(r'^\|(?:[^|]+\|)+$',stripped)

        # 3. Riconoscimento inizio Nuovi Blocchi
        if stripped.startswith("```"):
            if current_block:
                parsed_blocks.append(current_block)
            current_block = {'type': 'Multiline_code', 'content': []}
        
        elif stripped.startswith("#"):
            if current_block:
                parsed_blocks.append(current_block)
            
            # Parsing del livello dell'header (supporta #2 o ##)
            m_digit = re.match(r'^#(\d+)\s*(.*)', stripped)
            if m_digit:
                level = int(m_digit.group(1))
                clean_content = m_digit.group(2)
            else:
                m_hashes = re.match(r'^(#+)\s*(.*)', stripped)
                level = len(m_hashes.group(1))
                clean_content = m_hashes.group(2)
            
            current_block = {
                'type': 'Heading',
                'level': level,
                'content': parse_inline(clean_content, "header")
            }
        
        elif stripped.startswith("----"):
            if current_block:
                parsed_blocks.append(current_block)
            current_block = {
                'type': 'hr',
            }
        
    
        # --------- Vecchia parte degli elenchi ----------

        # elif stripped.startswith("-"):
        #     if current_block:
        #         parsed_blocks.append(current_block)
        #     clean_content = stripped[1:].lstrip()
        #     current_block = {
        #         'type': 'Ul_item',
        #         'content': parse_inline(clean_content, "ul")
        #     }
        
        # elif stripped.startswith("[]"):
        #     if current_block:
        #         parsed_blocks.append(current_block)
        #     clean_content = stripped[2:].lstrip()
        #     current_block = {
        #         'type': 'Tl_item',
        #         'content': parse_inline(clean_content, "ul"),
        #         'checked':False
        #     }
        # elif stripped.startswith("[x]"):
        #     if current_block:
        #         parsed_blocks.append(current_block)
        #     clean_content = stripped[3:].lstrip()
        #     current_block = {
        #         'type': 'Tl_item',
        #         'content': parse_inline(clean_content, "ul"),
        #         'checked':True
        #     }


        elif stripped.startswith(">"):
            if current_block:
                parsed_blocks.append(current_block)
            
            content = re.match(r'^>([n|t|i|w|c])?\s?(.*)', stripped)
            
            # Se c'è un tipo speciale ...
            if content.group(1):
                special = content.group(1)
            else:
                special = None

            clean_content = content.group(2)

            current_block = {
                'type': 'Blockquote',
                'special': special,
                'content': parse_inline(clean_content, "blockquote")
            }

        elif list_match:
            if line.startswith("    "):
                line = line.replace("    ","\t")
            indent = len(list_match.group(1))
            marker = list_match.group(2)
            clean_content = list_match.group(3)

            if marker == "-":
                item_type = "Ul"
                item = {
                    'type': 'Ul',
                    'value': parse_inline(clean_content, "ul"),
                    'indent': indent
                }
            else:
                checked = marker.lower() == "[x]"
                item = {
                    'type': 'Tl',
                    'value': parse_inline(clean_content, "ul"),
                    'indent': indent,
                    'checked': checked
                }

            if not current_block or current_block.get('type') != 'list':
                if current_block:
                    parsed_blocks.append(current_block)
                current_block = {'type': 'list', 'content': []}

            current_block['content'].append(item)
        
        elif table_match:
            #print("esecuzione")
            cell_match = re.findall(r'(?<=\|)[^|]*(?=\|)', stripped)
            inline_parsed_rows = []
            for cell in cell_match:
                inline_parsed_rows.append(parse_inline(cell,"placeholder"))

            if current_block:
                current_block["content"].append(inline_parsed_rows)                

            if not current_block or current_block.get('type') != 'table':
                if current_block:
                    parsed_blocks.append(current_block)
                current_block = {'type': 'table', 'content': [inline_parsed_rows]}

            #print(current_block)


        

        elif img_match:
            if current_block:
                parsed_blocks.append(current_block)
                current_block = None

            parsed_blocks.append({
                'type': 'img',
                'path': img_match.group(1),
                'size': int(img_match.group(2))
            })
        

        # 4. Linea di testo normale (o continuazione del blocco precedente)
        else:
            if current_block:
                # Se c'è un blocco attivo, vai a capo all'interno dello stesso
                current_block['content'].append({'type': 'newline', 'value': '\n'})
                current_block['content'].extend(parse_inline(line, "placeholder"))
            else:
                current_block = {
                    'type': 'Paragraph',
                    'content': parse_inline(line, "placeholder")
                }

    # Aggiunge l'ultimo blocco rimasto aperto a fine file
    if current_block:
        if current_block['type'] == 'Multiline_code' and current_block['content'] and current_block['content'][-1]['type'] == 'newline':
            current_block['content'].pop()
        parsed_blocks.append(current_block)

    return parsed_blocks


def main(document,output_path,style_path,font_path):
    with open(document, "r", encoding="utf-8") as file:
        lines = file.read().split("\n")

    parsed = parse(lines)
    #print(parsed)
    NewPdfPrinter.main(parsed,output_path,style_path,font_path)

if __name__ == "__main__":
    main("DocumentoProva.mi")