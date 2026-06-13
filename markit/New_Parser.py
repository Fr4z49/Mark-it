import re

try:
    from . import NewPdfPrinter
except ImportError:
    import NewPdfPrinter

def parse_inline(line, block_type):
    #line = line.replace("\t", "   ")

    pattern = re.compile(
        r"\*\*(?P<bold>.+?)\*\*"
        r"|"
        r"\_\_(?P<strikethru>.+?)\_\_"
        r"|"
        r"\\\\(?P<italic>.+?)\\\\"
        r"|"
        r"`(?P<code>.+?)`"
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

        elif m.group("code"):
            result.append({'type': 'code', 'value': m.group("code")})

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
        table_row_match = re.findall(r"(?<=\|)[^|]+(?=\|)", stripped)

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

        elif stripped.startswith("-"):
            if current_block:
                parsed_blocks.append(current_block)
            clean_content = stripped[1:].lstrip()
            current_block = {
                'type': 'Ul_item',
                'content': parse_inline(clean_content, "ul")
            }

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

                   

        elif img_match:
            if current_block:
                parsed_blocks.append(current_block)
                current_block = None

            parsed_blocks.append({
                'type': 'img',
                'path': img_match.group(1),
                'size': int(img_match.group(2))
            })
        
        elif table_row_match:
            # crea tabella se non esiste
            if not current_block or current_block.get('type') != 'table':
                if current_block:
                    parsed_blocks.append(current_block)

                current_block = {
                    'type': 'table',
                    'rows': []
                }

            current_block['rows'].append({
                'type': 'table_row',
                'content': table_row_match
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