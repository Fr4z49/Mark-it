# Parser markdown-like base con inline parsing
import pygments_highlighter

def parse_header(line, line_number):
    line = line.lstrip()

    if not line.startswith("#"):
        return None

    # livello
    if len(line) > 1 and line[1].isdigit():
        level = int(line[1])
        text = line[2:].strip()
    else:
        level = 1
        text = line[1:].strip()

    return {
        "type": "heading",
        "level": level,
        "content": parse_inline(text),
        "line": line_number
    }


def parse_blockquote(line, line_number):
    line = line.lstrip()

    if not line.startswith(">"):
        return None

    text = line[1:].strip()

    return {
        "type": "blockquote",
        "content": parse_inline(text),
        "line": line_number
    }

def parse_unordered_list_item(line,line_number):
    line = line.lstrip()
    text = line[1:].strip()

    if not line.startswith("-"):
        return None

    return {
        "type": "ul_item",
        "content": parse_inline(text),
        "line": line_number
    }


def parse_multiline_code(lines, start_index,highlight_style):

    line = lines[start_index].strip()
    
    # apertura blocco
    if not line.startswith("```"):
        return None, start_index

    code_lines = []

    i = start_index + 1

    while i < len(lines):

        current = lines[i]

        # chiusura blocco
        if current.strip().startswith("```"):
            break

        code_lines.append(current)

        i += 1
    
    colored_lines = pygments_highlighter.main(code_lines,highlight_style)
    #print(colored_lines)
    return {
        "type": "multiline_code",
        "content": colored_lines,
        "line": start_index + 1
    }, i


# ----------------------------
# INLINE PARSER (BOLD)
# ----------------------------

def parse_inline(text):
    result = []
    i = 0
    buffer = ""
    active_type = "text"

    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else None
        
        # --- AGGIUNTA: Controllo per \n letterale ---
        if char == "\\" and next_char == "n":
            if buffer:
                result.append({"type": active_type, "value": buffer})
                buffer = ""
            result.append({"type": "newline", "value": "\n"})
            i += 2  # Salta \ e n
            continue
        # --------------------------------------------

        found_tag = None
        step = 1

        if char == "*" and next_char == "*":
            found_tag = "bold"
            step = 2 # numero di caratteri necessari: 2 = " ** "
        elif char == "_" and next_char == "_":
            found_tag = "strikethru"
            step = 2
        elif char == "`":
            found_tag = "code"
            step = 1 # 1 = " ` " 

        if found_tag:
            if buffer:
                result.append({"type": active_type, "value": buffer})
                buffer = ""
            active_type = "text" if active_type == found_tag else found_tag
            i += step
        else:
            buffer += char
            i += 1

    if buffer:
        result.append({"type": active_type, "value": buffer})

    return result

# Esempio d'uso:
# text = "Prova **bold**, `code` e __strikethru__"
# print(parse_inline(text))

# Esempio di test:
# print(parse_inline("Ciao **mondo** e __rigato__"))


# ----------------------------
# PARAGRAPH
# ----------------------------

def parse_paragraph(line, line_number):
    return {
        "type": "paragraph",
        "content": parse_inline(line),
        "line": line_number
    }


# ----------------------------
# MAIN PARSER
# ----------------------------

def parse(lines, highlight_style):

    result = []

    i = 0

    while i < len(lines):

        line = lines[i].rstrip()

        if line.strip() == "":
            i += 1
            continue

        # ------------------------
        # MULTILINE CODE
        # ------------------------

        multiline_code, new_index = parse_multiline_code(lines, i,highlight_style)

        if multiline_code:
            result.append(multiline_code)
            i = new_index + 1
            continue

        # ------------------------
        # HEADER
        # ------------------------

        header = parse_header(line, i)

        if header:
            result.append(header)
            i += 1
            continue

        # ------------------------
        # BLOCKQUOTE
        # ------------------------

        quote = parse_blockquote(line, i)

        if quote:
            result.append(quote)
            i += 1
            continue

        ul = parse_unordered_list_item(line, i)

        if ul:
            result.append(ul)
            i += 1
            continue

        # ------------------------
        # PARAGRAPH
        # ------------------------

        result.append(parse_paragraph(line, i))

        i += 1

    return result


# ----------------------------
# MAIN
# ----------------------------
def main(document,highlight_style):
    file = open(document, "r").read()
    lines = file.split("\n")

    parsed = parse(lines,highlight_style)
    return parsed
