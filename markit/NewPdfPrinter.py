from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

from reportlab.pdfbase.ttfonts import TTFError

import json

px = 0.75


def get_font_height(font_name, font_size):
    try:
        face = pdfmetrics.getFont(font_name).face
    except:
        face = pdfmetrics.getFont("Helvetica").face
    ascender = face.ascent / 1000 * font_size
    descender = face.descent / 1000 * font_size
    return ascender - descender

def register_font(font_name,file_name,folder):
    font_path = Path(folder / file_name).expanduser()
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except TTFError:
        print(f"\033[31mUnable to register the font '{font_name}'.")
        print(f"Is it really in '{font_path}'? \nor did you type the font file_name wrong in the 'style.json'?\033[0m")


# =========================
# TEXT BASE CLASS
# =========================
class Text:
    def __init__(self, content, font_name, font_size, line_spacing, parsed_json):
        self.content = content
        self.total_height = 0
        self.page_end = 0

        if font_name in pdfmetrics.getRegisteredFontNames() or font_name in pdfmetrics.standardFonts:
            self.font_name = font_name
        else:
            self.font_name = "Helvetica"
            print(self)
            print(f"\033[31mUnable to use the font '{font_name}'\nDefaulting to font:'Helvetica'.\033[0m")
            print(f"\033[33mPlease check the 'Style.json' file currently in use\033[0m")
        
        self.font_size = font_size
        self.color = "#000000"  
        self.margin_top = 0
        self.margin_left = 0
        self.margin_right = 0
        self.alignment = "left"  
        self.content_width = 0   

        self.code_font_name = parsed_json["inline-code"]["font-name"]
        self.code_font_size = parsed_json["inline-code"]["font-size"]
        self.code_background_color = parsed_json["inline-code"]["background"]
        self.code_color = parsed_json["inline-code"]["color"]
        self.code_bg_pad_x = parsed_json["inline-code"]["padding-x"]
        self.code_bg_pad_y = parsed_json["inline-code"]["padding-y"]

        self.font_height = get_font_height(font_name, font_size)
        self.line_height = self.font_height * line_spacing  
        self.lines = []

    def word_wrap(self, page):
        avail_width = page.content_width - self.margin_left - self.margin_right
        current_line = []
        current_width = 0
        self.page_end = avail_width

        for segment in self.content:
            seg_type = segment["type"]
            text = segment["value"]

            if seg_type == "newline":
                self.lines.append(current_line)
                current_line = []
                current_width = 0
                continue

            if seg_type == "code":
                seg_width = stringWidth(text, self.code_font_name, self.code_font_size)
            elif seg_type == "bold":
                try:
                    seg_width = stringWidth(text, self.font_name + "-Bold", self.font_size)
                except KeyError:
                    seg_width = stringWidth(text, self.font_name + self.font_size)
            else:
                seg_width = stringWidth(text, self.font_name, self.font_size)

            if current_width + seg_width <= avail_width:
                current_line.append(segment)
                current_width += seg_width
            else:
                words = text.split(" ")
                for i, word in enumerate(words):
                    value = word + " " if i < len(words) - 1 else word
                    if seg_type == "code":
                        word_width = stringWidth(value, self.code_font_name, self.code_font_size)
                    elif seg_type == "bold":
                        word_width = stringWidth(value, self.font_name + "-Bold", self.font_size)
                    else:
                        word_width = stringWidth(value, self.font_name, self.font_size)

                    if current_width + word_width > avail_width:
                        self.lines.append(current_line)
                        current_line = []
                        current_width = 0

                    current_line.append({"type": seg_type, "value": value})
                    current_width += word_width

        if current_line:
            self.lines.append(current_line)

    def render_formatted(self, c, x, y, block):
        if block["type"] == "bold":
            c.setFillColor(HexColor(self.color))
            try:
                c.setFont(self.font_name + "-Bold", self.font_size)
            except KeyError:
                c.setFont("Helvetica-Bold", self.font_size)
                print(f"\033[31m'{self.font_name}' Bold variant is missing, defaulting to 'Helvetica-Bold'.\033[0m")
                print(f"\033[33mPlease import {self.font_name}-Bold inside the 'Style.json' currently in use.\033[0m")
            c.drawString(x, y - self.font_height, block["value"])
        
        if block["type"] == "italic":
            c.setFillColor(HexColor(self.color))
            try:
                c.setFont(self.font_name + "-Oblique", self.font_size)
            except KeyError:
                c.setFont("Helvetica-Oblique", self.font_size)
                print(f"\033[31m'{self.font_name}' font Italic variant is missing, defaulting to 'Helvetica-Oblique'.\033[0m")
                print(f"\033[33mPlease import {self.font_name}-Oblique inside the 'Style.json' currently in use.\033[0m")

            c.drawString(x, y - self.font_height, block["value"])

        elif block["type"] == "strikethru":
            c.setFillColor(HexColor(self.color))
            c.setFont(self.font_name, self.font_size)
            c.drawString(x, y - self.font_height, block["value"])
            text_width = stringWidth(block["value"], self.font_name, self.font_size)
            strike_y = y + self.font_size * 0.3 - self.font_height
            c.setStrokeColor(HexColor(self.color))
            c.setLineWidth(1)
            c.line(x, strike_y, x + text_width, strike_y)

        elif block["type"] == "code":
            c.setFont(self.code_font_name, self.code_font_size)
            text_width = stringWidth(block["value"], self.code_font_name, self.code_font_size)
            code_height = get_font_height(self.code_font_name, self.code_font_size)

            c.setFillColor(HexColor(self.code_background_color))
            c.rect(
                x - self.code_bg_pad_x,
                y - self.code_bg_pad_y - self.font_height,
                text_width + self.code_bg_pad_x * 2,
                code_height + self.code_bg_pad_y * 2,
                stroke=0, fill=1
            )
            c.setFillColor(HexColor(self.code_color))
            c.drawString(x, y + 1 - self.font_height, block["value"])

    def render(self, c, x, y):
        initial_y = y
        for line in self.lines:
            if self.alignment == "center":
                line_width = 0
                for block in line:
                    if block["type"] == "code":
                        line_width += stringWidth(block["value"], self.code_font_name, self.code_font_size)
                    elif block["type"] == "bold":
                        line_width += stringWidth(block["value"], self.font_name + "-Bold", self.font_size)
                    else:
                        line_width += stringWidth(block["value"], self.font_name, self.font_size)
                
                line_x = x + (self.content_width - line_width) / 2
            else:
                line_x = x

            for block in line:
                if block["type"] != "text":
                    self.render_formatted(c, line_x, y, block)
                else:
                    c.setFillColor(HexColor(self.color))
                    c.setFont(self.font_name, self.font_size)
                    c.drawString(line_x, y - self.font_height, block["value"])

                if block["type"] == "code":
                    line_x += stringWidth(block["value"], self.code_font_name, self.code_font_size)
                elif block["type"] == "bold":
                    line_x += stringWidth(block["value"], self.font_name + "-Bold", self.font_size)
                else:
                    line_x += stringWidth(block["value"], self.font_name, self.font_size)

            y -= self.line_height

        # Restituisce lo spazio effettivamente consumato dal testo puro
        return initial_y - y

    def layout(self, page, extra=0):
        self.content_width = page.content_width + extra
        self.word_wrap(page)
        self.text_height = self.line_height * len(self.lines)
        self.total_height = self.text_height
        return self.total_height


# =========================
# PARAGRAPH & HEADER CLASSES
# =========================
class Paragraph(Text):
    def __init__(self, content, parsed_json):
        font_name = parsed_json["text"]["font-name"]
        font_size = parsed_json["text"]["font-size"]
        self.line_spacing = parsed_json["text"].get("interline", 1.2)
        super().__init__(content, font_name, font_size, self.line_spacing, parsed_json)
        self.color = parsed_json["text"].get("color", "#000000")
        self.margin_top = parsed_json["text"]["margin-top"] 
        self.margin_left = parsed_json["text"]["margin-left"] 
        self.margin_right = parsed_json["text"]["margin-right"] 
    
    def layout(self, page):
        super().layout(page)
        self.total_height = self.text_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        # Consuma il margine superiore + l'altezza del testo sputata da super().render
        return self.margin_top + super().render(c, x + self.margin_left, y - self.margin_top)
    

class Ul_item(Text):
    def __init__(self, content, parsed_json):
        font_name = parsed_json["unordered-list"]["font-name"]
        font_size = parsed_json["unordered-list"]["font-size"]
        line_spacing = parsed_json["unordered-list"].get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.bullet = parsed_json["unordered-list"].get("bullet-char", "•")
        self.text_pad_l = parsed_json["unordered-list"].get("text-pad-left", 10) * px
        self.margin_top = parsed_json["unordered-list"]["margin-top"] * px
        self.margin_left = parsed_json["unordered-list"]["margin-left"] * px
        self.margin_right = parsed_json["unordered-list"]["margin-right"] * px
        self.color = parsed_json["unordered-list"].get("color", "#000000")

    def layout(self, page):
        super().layout(page)
        self.total_height = self.text_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        text_y = y - self.margin_top
        c.setFont(self.font_name, self.font_size)
        c.setFillColor(HexColor(self.color))
        c.drawString(x + self.margin_left, text_y - self.font_height, self.bullet)
        
        return self.margin_top + super().render(c, x + self.margin_left + self.text_pad_l, text_y)


class Header(Text):
    def __init__(self, content, level, parsed_json):
        style = parsed_json.get(level, parsed_json.get("header1"))
        
        font_name = style["font-name"]
        font_size = style["font-size"]
        line_spacing = style.get("line-spacing", 1.2)
        
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color = style.get("color", "#000000")
        self.margin_top = style.get("margin-top", 0)
        self.margin_left = style.get("margin-left", 0)
        self.alignment = style.get("align", "left")  
        
        self.line_color = style.get("line-color", "#000000")
        self.line = style.get("line", True)
        self.line_width = style.get("line-thickness",1)
        self.line_start = style.get("line-start", 0) 
        self.line_end = style.get("line-end", 0)
        self.space_between_line = style.get("space-between-line", 0)
        self.level = level

    def layout(self, page):
        super().layout(page)
        # Se c'è la linea, l'ingombro spinge fino alla coordinata della linea stessa
        if self.line:
            # Calcoliamo esattamente dove finisce la linea rispetto alla Y iniziale del testo
            # last_line_baseline dista (len(lines)-1)*line_height. Sotto c'è lo space_between e il font_height.
            text_lines_height = (len(self.lines) - 1) * self.line_height
            self.total_height = text_lines_height + self.space_between_line + self.font_height + self.margin_top
        else:
            self.total_height = self.text_height + self.margin_top
        return self.total_height 

    def render(self, c, x, y):
        text_y = y - self.margin_top
        super().render(c, x + self.margin_left, text_y) 

        c.bookmarkHorizontalAbsolute(self.lines[0][0]["value"], y)
        c.addOutlineEntry(self.lines[0][0]["value"], self.lines[0][0]["value"], level=int(self.level[-1])-1)
        
        if self.line:
            last_line_baseline = text_y - ((len(self.lines) - 1) * self.line_height)
            text_bottom_y = last_line_baseline - self.space_between_line - self.font_height
            
            start_x = x + self.line_start
            end_x = x + self.content_width - self.line_end
            
            c.setStrokeColor(HexColor(self.line_color))
            c.setLineWidth(self.line_width)  
            c.line(start_x, text_bottom_y, end_x, text_bottom_y)

        return self.total_height 


class Multiline_Code(Text):
    def __init__(self, content, parsed_json):
        font_name = parsed_json["multiline-code"]["font-name"]
        font_size = parsed_json["multiline-code"]["font-size"]
        line_spacing = parsed_json["multiline-code"].get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color = parsed_json["multiline-code"].get("color", "#000000")
        self.margin_top = parsed_json["multiline-code"]["margin-top"] * px
        self.background = parsed_json["multiline-code"]["background"]
        self.padding_x = parsed_json["multiline-code"].get("padding-x")
        self.padding_y = parsed_json["multiline-code"].get("padding-y")
        self.margin_left = parsed_json["multiline-code"].get("margin-left") * px 
        self.margin_right = parsed_json["multiline-code"].get("margin-right") * px

    def layout(self, page):
        super().layout(page)
        # Corretto: Il rettangolo parte a y - margin_top ed è profondo box_height.
        # Poiché il testo finisce prima del rettangolo, l'ingombro reale è determinato dal rettangolo.
        box_height = self.text_height + self.padding_y
        self.total_height = box_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        box_x      = x + self.margin_left - self.padding_x / 2
        box_top    = y - self.margin_top
        box_height = self.text_height + self.padding_y 
        box_width  = self.page_end + self.padding_x 

        c.setFillColor(HexColor(self.background))
        c.rect(box_x, box_top, box_width, -box_height, fill=1, stroke=0)

        # Il testo viene renderizzato leggermente rientrato verticalmente
        super().render(c, x + self.margin_left + (self.padding_x /2), y - self.margin_top - self.padding_y / 2)
        return self.total_height


class Blockquote(Text):
    def __init__(self, content,special, parsed_json):
        font_name = parsed_json["quote"]["font-name"]
        font_size = parsed_json["quote"]["font-size"]
        line_spacing = parsed_json["quote"].get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        
        self.color = parsed_json["quote"].get("color", "#000000")
        self.line_color = parsed_json["quote"].get("line-color", "#ffffff")
        self.background = parsed_json["quote"]["background"]
        if special: #(se non è None)
            modifier = self.map_special(special)
            self.color = parsed_json["quote"].get("color-"+modifier, "#000000")
            self.line_color = parsed_json["quote"].get("line-color-"+modifier, "#ffffff")
            self.background = parsed_json["quote"].get("background-"+modifier,"#000000")
            
        else: #se è none usa i colori principali
            self.color = parsed_json["quote"].get("color", "#000000")
            self.line_color = parsed_json["quote"].get("line-color", "#ffffff")
            self.background = parsed_json["quote"].get("background","#000000")


        self.margin_top = parsed_json["quote"]["margin-top"] * px
        self.padding_x = parsed_json["quote"].get("padding-x")
        self.padding_y = parsed_json["quote"].get("padding-y")
        self.margin_left = parsed_json["quote"].get("margin-left") * px 
        self.margin_right = parsed_json["quote"].get("margin-right") * px
    
    def map_special(self,special):
        return {
            "n": "note",
            "t": "tip",
            "i": "important",
            "w": "warning",
            "c": "caution"
        }.get(special)

    def layout(self, page):
        super().layout(page)
        # Stessa logica matematica del Multiline_Code
        box_height = self.text_height + self.padding_y
        self.total_height = box_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        box_x      = x + self.margin_left - self.padding_x / 2
        box_top    = y - self.margin_top
        box_height = self.text_height + self.padding_y 
        box_width  = self.page_end + self.padding_x

        c.setFillColor(HexColor(self.background))
        c.rect(box_x, box_top, box_width, -box_height, fill=1, stroke=0)

        c.setLineWidth(2)
        c.setStrokeColor(HexColor(self.line_color))
        c.line(box_x, box_top, box_x, box_top - box_height)

        super().render(c, x + self.margin_left + (self.padding_x /2), y - self.margin_top - self.padding_y / 2)
        return self.total_height

class Table(Text):
    def __init__(self):
        pass 

# =========================
# IMAGE
# =========================

class Image:
    def __init__(self, path, parsed_json,size):
        self.style = parsed_json["image"]
        self.path = path
        self.margin_top = self.style.get("margin-top", 0)
        self.margin_left = self.style.get("margin-left", 0)
        #self.size = self.style.get("size",100)/100
        self.size = size/100
        self.width, self.height = ImageReader(path).getSize()
        self.totalHeight = 0

    def layout(self,page):
        
        self.total_height = self.height * self.size + self.margin_top

        return self.total_height

    def render(self, c, x, y):
        c.drawImage(
            self.path,
            x + self.margin_left,
            y-self.total_height,
            width=self.width*self.size,
            height=self.height*self.size
        )
        return self.total_height 




# =========================
# PAGE
# =========================
class Page:
    def __init__(self, page_height, page_width):
        self.height = page_height  
        self.width = page_width    

        self.margin_top = 0        
        self.margin_bottom = 0
        self.margin_left = 0
        self.margin_right = 0

        self.content_width = 0    

        self.global_y = 0
        self.backgroundColor = "#FFFFFF"


# =========================
# HELPERS
# =========================
def blocks_to_objects(parsed, parsed_json):
    objects = []
    for element in parsed:
        #print (element)
        if element["type"] == "Paragraph":
            objects.append(Paragraph(element["content"], parsed_json))
        elif element["type"] == "Multiline_code":
            objects.append(Multiline_Code(element["content"], parsed_json))
        elif element["type"] == "Blockquote":
            objects.append(Blockquote(element["content"],element["special"], parsed_json))
        elif element["type"] == "Ul_item":
            objects.append(Ul_item(element["content"], parsed_json))
        
        elif element["type"] == "img":
            try:
                objects.append(Image(element["path"], parsed_json,element["size"]))
            except OSError:
                objects.append(Paragraph([{'type':'text','value':f"[{element["path"]} Cannot be loaded]"}], parsed_json))

        elif element["type"] == "Heading":
            level_key = f"header{element['level']}"
            objects.append(Header(element["content"], level_key, parsed_json))
    return objects


def get_page_height(objects, page):
    total = 0
    for obj in objects:
        total += obj.layout(page)

    total_mm = total / mm
    if total_mm < page.height:
        return page.height

    return total_mm + page.margin_bottom / mm


def LoadJson(path):
    with open(path, "r") as f:
        return json.load(f)


def render(c, objects, page):
    c.setFillColor(HexColor(page.backgroundColor))
    c.rect(0, 0, page.width * mm, page.height * mm, fill=1, stroke=0)

    for obj in objects:
        page.global_y -= obj.render(c, page.margin_left, page.global_y)


def main(parsed_file, output_path, style_path,font_path):
    parsed_json = LoadJson(style_path)
    #print(parsed_file)
    PAGE = parsed_json["page"]
    page = Page(
        PAGE["minimum-page-height"],
        PAGE["page-width"]
    )

    FONTS = parsed_json["custom-fonts"]
    for font in FONTS:
        register_font(font,FONTS[font],font_path)

    page.margin_top    = PAGE["margin-top"]    * px * mm
    page.margin_bottom = PAGE["margin-bottom"] * px * mm
    page.margin_left   = PAGE["margin-left"]   * px * mm
    page.margin_right  = PAGE["margin-right"]  * px * mm
    page.backgroundColor = PAGE["background"]

    page.content_width = (page.width * mm) - page.margin_left - page.margin_right

    objects = blocks_to_objects(parsed_file, parsed_json)

    page.height = get_page_height(objects, page)

    page.global_y = (page.height * mm) - page.margin_top

    c = canvas.Canvas(output_path)
    c.setPageSize((page.width * mm, page.height * mm))

    render(c, objects, page)

    c.showPage()
    c.save()