from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

import Parser
import json
import io


px = 0.75


# =========================================================
# LOAD STYLE
# =========================================================

def load_style(style_path):

    file = open(style_path, "r").read()
    parsed = json.loads(file)

    return parsed


# =========================================================
# PAGE SETTINGS
# =========================================================

def get_config(parsed_json):

    return {
        "HEADER1":        parsed_json["header1"],
        "HEADER2":        parsed_json["header2"],
        "HEADER3":        parsed_json["header3"],
        "PAGE":           parsed_json["page"],
        "TEXT":           parsed_json["text"],
        "CODE":           parsed_json["inline-code"],
        "BLOCKQUOTE":     parsed_json["quote"],
        "MULTILINE_CODE": parsed_json["multiline-code"],
        "UL": parsed_json["unordered-list"],
    }


# =========================================================
# UTILS
# =========================================================

def background(c, color, page_width, page_height):
    c.setFillColor(color)
    c.rect(
        0 * mm,
        0 * mm,
        page_width * mm,
        page_height * mm,
        fill=1
    )


def get_left_offset(text, font_name, font_size):
    if not text:
        return 0
    return stringWidth(text[0], font_name, font_size) * 0.1


def get_ascent(font_name, font_size):
    font = pdfmetrics.getFont(font_name)
    face = font.face
    if face and face.ascent is not None:
        return face.ascent / 1000 * font_size
    return font_size * 0.8


def get_font_height(font_name, font_size):
    font = pdfmetrics.getFont(font_name)
    face = font.face
    if face and face.ascent is not None and face.descent is not None:
        return (face.ascent - face.descent) / 1000 * font_size
    return font_size * 1.2


def drawStringTopLeft(c, x, y_top, text, font_name, font_size,
                      margin_left=0, margin_top=0):
    ascent = get_ascent(font_name, font_size)
    x_offset = get_left_offset(text, font_name, font_size)
    c.setFont(font_name, font_size)
    c.drawString(x - x_offset + margin_left, y_top - ascent - margin_top, text)
    return get_font_height(font_name, font_size)


def drawStringCentered(c, y_top, text, font_name, font_size):
    text_width = stringWidth(text, font_name, font_size)
    page_width = c._pagesize[0]
    ascent = get_ascent(font_name, font_size)
    x = (page_width - text_width) / 2
    c.setFont(font_name, font_size)
    c.drawString(x, y_top - ascent, text)
    return get_font_height(font_name, font_size)


# =========================================================
# HEADER
# =========================================================

def draw_header(c, y, text_input, level, cfg, draw=True,
                x=0, margin_left=25 * px, margin_top=30 * px,
                space_between_line=5 * px):

    HEADER1 = cfg["HEADER1"]
    HEADER2 = cfg["HEADER2"]
    HEADER3 = cfg["HEADER3"]
    PAGE    = cfg["PAGE"]

    if isinstance(text_input, list):
        segments = text_input
    else:
        from Parser import parse_inline
        segments = parse_inline(text_input)

    configs = {1: HEADER1, 2: HEADER2, 3: HEADER3}
    conf = configs.get(level, HEADER1)

    base_name = str(conf["font-name"])
    style = str(conf.get("font-style", "Bold"))

    if style == "Bold" and not base_name.endswith("-Bold"):
        font_header = f"{base_name}-Bold"
    else:
        font_header = base_name

    font_size = conf["font-size"]
    line_height = get_font_height(font_header, font_size)
    ascent = get_ascent(font_header, font_size)

    total_width = sum(
        stringWidth(seg["value"], font_header, font_size)
        for seg in segments
    )

    if level == 1:
        curr_x = (PAGE["page-width"] * mm - total_width) / 2
    else:
        curr_x = x + margin_left

    curr_y = y - conf["margin-top"] - ascent

    c.setFillColor(conf["color"])
    c.setFont(font_header, font_size)

    for seg in segments:

        valore_testo = seg["value"]

        if draw:
            c.drawString(curr_x, curr_y, valore_testo)

        if seg["type"] == "strikethru":
            w = stringWidth(valore_testo, font_header, font_size)
            strike_y = curr_y + (font_size * 0.3)
            c.setLineWidth(1)
            c.setStrokeColor(conf["color"])
            if draw:
                c.line(curr_x, strike_y, curr_x + w, strike_y)

        curr_x += stringWidth(valore_testo, font_header, font_size)

    y_shift = line_height + conf["margin-top"]

    if conf.get("line", False):
        c.setLineWidth(conf["line-thickness"])
        c.setStrokeColor(conf["line-color"])
        line_x_start = conf["line-start"] if level == 1 else margin_left
        if draw:
            c.line(
                line_x_start,
                y - y_shift - space_between_line,
                PAGE["page-width"] * mm - conf["line-end"],
                y - y_shift - space_between_line
            )
        return y_shift + space_between_line + 5

    return y_shift


# =========================================================
# BLOCKQUOTE
# =========================================================

def render_blockquote(c, x, y, string, font_name, font_size, cfg,
                      draw=True, margin_left=30, margin_right=30,
                      margin_top=15 * px):

    TEXT      = cfg["TEXT"]
    BLOCKQUOTE = cfg["BLOCKQUOTE"]
    PAGE      = cfg["PAGE"]

    text_pad_l = 15 * px
    bg_pad_y   = 10 * px

    line_height = get_font_height(font_name, font_size)
    max_width   = PAGE["page-width"] * mm - margin_left - margin_right - text_pad_l

    all_words_styled = []

    for part in string:

        if part["type"] == "newline":
            all_words_styled.append({"text": "\n", "type": "newline"})
            continue

        words = part["value"].split(" ")

        for i, w in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            all_words_styled.append({"text": w + suffix, "type": part["type"]})

    lines = []
    current_line  = []
    current_width = 0

    for item in all_words_styled:

        if item["type"] == "newline":
            lines.append(current_line)
            current_line  = []
            current_width = 0
            continue

        current_f = (
            font_name + "-Bold"
            if item["type"] == "bold"
            else font_name
        )
        w_width = stringWidth(item["text"], current_f, font_size)

        if current_width + w_width > max_width:
            lines.append(current_line)
            current_line  = [item]
            current_width = w_width
        else:
            current_line.append(item)
            current_width += w_width

    if current_line:
        lines.append(current_line)

    text_height = len(lines) * (line_height + TEXT["interline"])
    bg_width    = PAGE["page-width"] * mm - margin_left - margin_right
    bg_height   = text_height + (bg_pad_y * 2)
    top_y       = y - margin_top
    bg_x        = margin_left
    bg_y        = top_y - bg_height

    if draw:
        c.setFillColor(BLOCKQUOTE["background"])
        c.rect(bg_x, bg_y, bg_width, bg_height, stroke=0, fill=1)
        c.setStrokeColor(BLOCKQUOTE["line-color"])
        c.setLineWidth(2)
        c.line(bg_x, bg_y, bg_x, bg_y + bg_height)

    x_cursor = bg_x + text_pad_l
    y_cursor = top_y - bg_pad_y - line_height + (line_height * 0.2)

    def new_line():
        nonlocal x_cursor, y_cursor
        y_cursor -= line_height + TEXT["interline"]
        x_cursor  = bg_x + text_pad_l

    for line in lines:

        for item in line:

            if item["type"] == "newline":
                continue

            current_f = (
                font_name + "-Bold"
                if item["type"] == "bold"
                else font_name
            )

            c.setFont(current_f, font_size)
            c.setFillColor(BLOCKQUOTE["color"])

            if draw:
                c.drawString(x_cursor, y_cursor, item["text"])

            if item["type"] == "strikethru":
                w        = stringWidth(item["text"], current_f, font_size)
                strike_y = y_cursor + (line_height * 0.3)
                c.setLineWidth(1)
                c.setStrokeColor(BLOCKQUOTE["color"])
                if draw:
                    c.line(x_cursor, strike_y, x_cursor + w, strike_y)

            x_cursor += stringWidth(item["text"], current_f, font_size)

        new_line()

    return margin_top + bg_height


# =========================================================
# PARAGRAPH
# =========================================================

def render_paragraph(c, x, y, blocks, font_name, font_size, cfg,
                     draw=True, margin_left=None, margin_right=None,
                     margin_top=None):

    TEXT = cfg["TEXT"]
    CODE = cfg["CODE"]
    PAGE = cfg["PAGE"]

    if margin_left  is None: margin_left  = TEXT["margin-left"]
    if margin_right is None: margin_right = TEXT["margin-right"]
    if margin_top   is None: margin_top   = TEXT["margin-top"]

    CODE_PADDING_X = 3
    CODE_PADDING_Y = 2

    max_width   = PAGE["page-width"] * mm - margin_left - margin_right
    line_height = get_font_height(font_name, font_size)

    x_cursor = margin_left
    y_cursor = y - margin_top

    def new_line():
        nonlocal x_cursor, y_cursor
        y_cursor -= line_height + TEXT["interline"]
        x_cursor  = margin_left

    def draw_text_segment(text, font, color, is_strike=False):
        nonlocal x_cursor, y_cursor

        words       = text.split(" ")
        space_width = stringWidth(" ", font, font_size)

        for i, word in enumerate(words):
            word_width = stringWidth(word, font, font_size)

            if x_cursor + word_width > (margin_left + max_width):
                new_line()

            c.setFont(font, font_size)
            c.setFillColor(color)

            if draw:
                c.drawString(x_cursor, y_cursor, word)

            if is_strike:
                line_y = y_cursor + font_size * 0.3
                c.setStrokeColor(color)
                c.setLineWidth(1)
                if draw:
                    c.line(x_cursor, line_y, x_cursor + word_width, line_y)

            x_cursor += word_width

            if i < len(words) - 1 or text.endswith(" "):
                if x_cursor + space_width > (margin_left + max_width):
                    new_line()
                else:
                    x_cursor += space_width

    def draw_code_segment(text, font, color):
        nonlocal x_cursor, y_cursor

        text_width = stringWidth(text, font, font_size)

        if x_cursor + text_width > (margin_left + max_width):
            new_line()

        c.saveState()
        c.setFillColor(CODE["background"])

        if draw:
            c.rect(
                x_cursor - CODE_PADDING_X,
                y_cursor - CODE_PADDING_Y,
                text_width + 2 * CODE_PADDING_X,
                font_size + 2 * CODE_PADDING_Y,
                fill=1, stroke=0
            )

        c.restoreState()
        c.setFont(font, font_size)
        c.setFillColor(color)

        if draw:
            c.drawString(x_cursor, y_cursor, text)

        x_cursor += text_width

    for block in blocks:

        if block["type"] == "newline":
            new_line()
            continue

        text  = block.get("value", "")
        style = block["type"]

        if style == "bold":
            draw_text_segment(text, TEXT["font-name"] + "-Bold", TEXT["color"])

        elif style == "code":
            draw_code_segment(text, CODE["font-name"], CODE["color"])

        elif style == "strikethru":
            draw_text_segment(text, TEXT["font-name"], TEXT["color"], is_strike=True)

        else:
            draw_text_segment(text, font_name, TEXT["color"])

    return (y - y_cursor) + (line_height / 2)


# =========================================================
# MULTILINE CODE
# =========================================================

def render_multiline_code(c, x, y, string, font_name, font_size, cfg,
                          draw=True, margin_left=None, margin_right=None,
                          margin_top=None):

    MULTILINE_CODE = cfg["MULTILINE_CODE"]
    PAGE           = cfg["PAGE"]

    if margin_left  is None: margin_left  = MULTILINE_CODE["margin-left"]
    if margin_right is None: margin_right = MULTILINE_CODE["margin-right"]
    if margin_top   is None: margin_top   = MULTILINE_CODE["margin-top"] * px

    lines        = string.split("\n")
    temp_y_shift = get_font_height(font_name, font_size) + 5
    bg_pad_y     = MULTILINE_CODE["background-pad-y"] * px
    text_padx    = MULTILINE_CODE["background-pad-x"] * px

    y_cursor = y - margin_top
    x_cursor = x + margin_left
    bg_height = (len(lines) * temp_y_shift) + (2 * bg_pad_y)

    c.setFillColor(MULTILINE_CODE["background"])
    c.rect(
        x + margin_left,
        y - bg_height - margin_top,
        PAGE["page-width"] * mm - margin_right - margin_left,
        bg_height,
        fill=1, stroke=0
    )
    c.setFillColor(MULTILINE_CODE["color"])

    c.setFont(font_name,font_size)

    for line in lines:
        if draw:
            c.drawString(
                x_cursor + text_padx,
                y_cursor - bg_pad_y / 2 - margin_top,
                line
            )
        y_cursor -= temp_y_shift

    return y - y_cursor + bg_pad_y + margin_top

def render_ul_item(c, x, y, text, font_name, font_size, cfg, draw=True,
                   margin_left=None, margin_right=None, margin_top=None):

    PAGE = cfg["PAGE"]
    UL   = cfg["UL"]
    CODE = cfg["CODE"]

    if margin_left  is None: margin_left  = UL["margin-left"]
    if margin_right is None: margin_right = UL["margin-right"]
    if margin_top   is None: margin_top   = UL["margin-top"]

    CODE_PADDING_X = 3
    CODE_PADDING_Y = 2

    max_width   = PAGE["page-width"] * mm - margin_left - margin_right
    line_height = get_font_height(font_name, font_size)

    y_cursor = y - margin_top 
    x_cursor = margin_left

    # --- bullet ---
    c.setFont(font_name, font_size)
    if draw:
        c.drawString(x_cursor, y_cursor, UL["bullet-char"])

    bullet_offset = stringWidth(UL["bullet-char"], font_name, font_size) + UL["text-pad-left"] * px
    x_cursor += bullet_offset
    text_start_x = margin_left + bullet_offset  # ← usato da new_line per rientrare correttamente

    def new_line():
        nonlocal x_cursor, y_cursor
        y_cursor -= line_height + UL["interline"]
        x_cursor  = text_start_x  # ← rientra dopo il bullet, non a margin_left

    def draw_text_segment(value, font, color, is_strike=False):
        nonlocal x_cursor, y_cursor

        words       = value.split(" ")
        space_width = stringWidth(" ", font, font_size)

        for i, word in enumerate(words):
            word_width = stringWidth(word, font, font_size)

            if x_cursor + word_width > (margin_left + max_width):
                new_line()

            c.setFont(font, font_size)
            c.setFillColor(color)

            if draw:
                c.drawString(x_cursor, y_cursor, word)

            if is_strike:
                line_y = y_cursor + font_size * 0.3
                c.setStrokeColor(color)
                c.setLineWidth(1)
                if draw:
                    c.line(x_cursor, line_y, x_cursor + word_width, line_y)

            x_cursor += word_width

            if i < len(words) - 1 or value.endswith(" "):
                if x_cursor + space_width > (margin_left + max_width):
                    new_line()
                else:
                    x_cursor += space_width

    def draw_code_segment(value, font, color):
        nonlocal x_cursor, y_cursor

        text_width = stringWidth(value, font, font_size)

        if x_cursor + text_width > (margin_left + max_width):
            new_line()

        c.saveState()
        c.setFillColor(CODE["background"])

        if draw:
            c.rect(
                x_cursor - CODE_PADDING_X,
                y_cursor - CODE_PADDING_Y,
                text_width + 2 * CODE_PADDING_X,
                font_size + 2 * CODE_PADDING_Y,
                fill=1, stroke=0
            )

        c.restoreState()
        c.setFont(font, font_size)
        c.setFillColor(color)

        if draw:
            c.drawString(x_cursor, y_cursor, value)

        x_cursor += text_width

    for block in text:

        if block["type"] == "newline":
            new_line()
            continue

        value = block.get("value", "")  # ← rinominato da "text" a "value"
        style = block["type"]

        if style == "bold":
            draw_text_segment(value, UL["font-name"] + "-Bold", UL["color"])
        elif style == "code":
            draw_code_segment(value, CODE["font-name"], CODE["color"])
        elif style == "strikethru":
            draw_text_segment(value, UL["font-name"], UL["color"], is_strike=True)
        else:
            draw_text_segment(value, font_name, UL["color"])

    return y - y_cursor 





# =========================================================
# RENDER
# =========================================================

def render(c, parsed_file, cfg, draw=False, page_height=10000):

    PAGE       = cfg["PAGE"]
    TEXT       = cfg["TEXT"]
    BLOCKQUOTE = cfg["BLOCKQUOTE"]
    MULTILINE_CODE = cfg["MULTILINE_CODE"]
    UL = cfg["UL"]

    # c.bookmarkPage("root")
    # c.addOutlineEntry("root", "root", level=0)
    start_y = (page_height * mm) - PAGE["margin-top"]
    y = start_y
    
    if draw:
        background(c, PAGE["background"], PAGE["page-width"], page_height)

    for line in parsed_file:

        current_line = [line[k] for k in line]
        print(current_line)

        if current_line[0] == "heading":
            y_shift= draw_header(
                c, y, current_line[2], current_line[1], cfg,
                draw=draw, margin_top=10 * px
            )
            c.bookmarkHorizontalAbsolute(current_line[2][0]["value"], y+y_shift)
            c.addOutlineEntry(current_line[2][0]["value"], current_line[2][0]["value"], level=current_line[1]-1)
            y-=y_shift

        elif current_line[0] == "paragraph":
            y -= render_paragraph(
                c, TEXT["margin-left"], y, current_line[1],
                TEXT["font-name"], TEXT["font-size"], cfg, draw=draw
            )

        elif current_line[0] == "blockquote":
            y -= render_blockquote(
                c, 0, y, current_line[1],
                BLOCKQUOTE["font-name"], BLOCKQUOTE["font-size"], cfg, draw=draw
            )

        elif current_line[0] == "multiline_code":
            y -= render_multiline_code(
                c, 0, y, current_line[1],
                MULTILINE_CODE["font-name"], MULTILINE_CODE["font-size"], cfg, draw=draw
            )
        elif current_line[0] == "ul_item":
            y -= render_ul_item(
                c, 0, y, current_line[1],
                UL["font-name"], UL["font-size"], cfg, draw=draw
            )

    used_height_mm = (start_y - y) / mm

    return max(
        used_height_mm + PAGE["margin-top"] + PAGE["margin-bottom"],
        PAGE["minimum-page-height"]
    )


# =========================================================
# ENTRY POINT
# =========================================================

def generate_pdf(input_path, output_path, style_path):
    """
    Genera un PDF da un file di input Markdown-like.

    Parametri:
        input_path  (str): percorso del file sorgente  (es. "Input.mi")
        output_path (str): percorso del PDF di output  (es. "Output.pdf")
        style_path  (str): percorso del JSON di stile  (es. "Style.json")
    """

    parsed_json = load_style(style_path)
    cfg         = get_config(parsed_json)

    PAGE       = cfg["PAGE"]
    PAGE_WIDTH = PAGE["page-width"]

    PAGE_HEIGHT_INTERNAL = 10000

    parsed = Parser.main(input_path)

    # --------------------------------------------------
    # PASS 1 — misura l'altezza necessaria
    # --------------------------------------------------

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.setPageSize((PAGE_WIDTH * mm, PAGE_HEIGHT_INTERNAL * mm))

    effective_page_height = render(c, parsed, cfg, draw=False, page_height=PAGE_HEIGHT_INTERNAL)

    c.save()

    # --------------------------------------------------
    # PASS 2 — disegna il PDF finale
    # --------------------------------------------------

    c = canvas.Canvas(output_path)
    c.setPageSize((PAGE_WIDTH * mm, effective_page_height * mm))
    c.setTitle(output_path[:-4])
    render(c, parsed, cfg, draw=True, page_height=effective_page_height)

    c.showPage()
    c.save()

    print(f"PDF generato: {output_path}  ({effective_page_height:.1f} mm di altezza)")


# =========================================================
# ESECUZIONE DIRETTA (opzionale)
# =========================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        _, inp, out, sty = sys.argv
        generate_pdf(inp, out, sty)

    else:
        print("Uso: python Renderer.py <input> <output> <stile>")
        print("Es.: python Renderer.py Input.mi Output.pdf Style.json")
