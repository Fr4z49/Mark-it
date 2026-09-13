import os,sys
libs = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.insert(0, libs)

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

try:
    from . import JsonLoader
except ImportError:
    import JsonLoader

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
            print(f"\033[31mUnable to use the font '{font_name}'\nDefaulting to font:'Helvetica'.\033[0m")
            print(f"\033[33mPlease check the 'Style.json' file currently in use\033[0m")
        self.line_spacing = line_spacing
        self.font_size = font_size
        self.color = "#000000"  
        self.margin_top = 0
        self.margin_left = 0
        self.margin_right = 0
        self.alignment = "left"  
        self.content_width = 0   

        inline = parsed_json.get("inline-code", {})
        self.bold_font_name = None
        self.oblique_font_name = None
        self.code_font_name        = inline.get("font-name", "Helvetica-Bold")
        self.code_font_size        = inline.get("font-size", 10)
        self.code_background_color = inline.get("background", "#1e242a")
        self.code_color            = inline.get("color", "#f0f6fc")
        self.code_bg_pad_x         = inline.get("padding-x", 2)
        self.code_bg_pad_y         = inline.get("padding-y", 2)
        self.temp_font_name = None
        self.temp_font_size = None

        highlight = parsed_json.get("highlighted-text")

        self.highlight_color = highlight.get("color","#000000")
        self.highlight_background_color = highlight.get("background","#ffff00")
        self.highlight_pad_x = highlight.get("padding-x",2)
        self.highlight_pad_y = highlight.get("padding-y",2)

        link = parsed_json.get("link", {})
        self.link_color = link.get("color", "#2f81f7")
        self.link_line  = link.get("line", True)

        self.font_height = get_font_height(font_name, font_size)
        self.line_height = self.font_height * line_spacing  
        self.word_width = 0
        self.avail_width = 0
        self.lines = []

    def _merge_segments(self):
        """
        Dopo il word-wrap, parole consecutive dello stesso segmento originale
        (es. un inline-code spezzato su più righe) vengono ri-fuse in un
        unico blocco per riga, così il background/stile viene applicato
        all'intera porzione di riga e non a ogni singola parola.
        """
        merged_lines = []
        for line in self.lines:
            if not line:
                merged_lines.append(line)
                continue

            new_line = [dict(line[0])]
            for block in line[1:]:
                last = new_line[-1]
                if block["type"] == last["type"] and block["type"] in ("code", "bold", "text"):
                    last["value"] += block["value"]
                else:
                    new_line.append(dict(block))
            merged_lines.append(new_line)

        self.lines = merged_lines
        
    def word_wrap(self, page, forced_width=None):
        if forced_width is not None:
            self.avail_width = forced_width
        elif self.avail_width == 0:
            self.avail_width = page.content_width - self.margin_left - self.margin_right
        else:
            self.avail_width = 60

        current_line = []
        current_width = 0
        self.page_end = self.avail_width

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
                    seg_width = stringWidth(text, self.bold_font_name, self.font_size)
                except KeyError:
                    seg_width = stringWidth(text, self.font_name, self.font_size)
            else:
                seg_width = stringWidth(text, self.font_name, self.font_size)

            if current_width + seg_width <= self.avail_width:
                current_line.append(segment)
                current_width += seg_width
            else:
                words = text.split(" ")
                for i, word in enumerate(words):
                    value = word + " " if i < len(words) - 1 else word
                    if seg_type == "code":
                        self.word_width = stringWidth(value, self.code_font_name, self.code_font_size)
                    elif seg_type == "bold":
                        self.word_width = stringWidth(value, self.bold_font_name, self.font_size)
                    else:
                        self.word_width = stringWidth(value, self.font_name, self.font_size)

                    if current_width + self.word_width > self.avail_width:
                        self.lines.append(current_line)
                        current_line = []
                        current_width = 0

                    current_line.append({"type": seg_type, "value": value})
                    current_width += self.word_width

        if current_line:
            self.lines.append(current_line)

        self._merge_segments()
        return self.lines

    def render_formatted(self, c, x, y, block):

        if block["type"] == "bold":
            c.setFillColor(HexColor(self.color))
            try:
                
                c.setFont(self.bold_font_name, self.font_size)
                c.drawString(x, y - self.font_height, block["value"])
                
            except KeyError:
                c.setFont("Helvetica-Bold", self.font_size)
                #print(f"\033[31m'{self.font_name}' Bold variant is missing, defaulting to 'Helvetica-Bold'.\033[0m")
                print(f"\033[31m'{self.font_name}' Bold variant is missing, Using fallback method.\033[0m")
                print(f"\033[33mPlease import {self.font_name}-Bold inside the 'Style.json' currently in use.\033[0m")


                c.saveState()
                c.setStrokeColor(HexColor(self.color))
                c.setLineWidth(0.6)

                text = c.beginText(x, y - self.font_height)
                text.setFont(self.font_name, self.font_size)
                text.setCharSpace(0.7)
                text.setTextRenderMode(2)
                text.textOut(block["value"])
                c.drawText(text)
                c.restoreState()
            
        
        elif block["type"] == "italic":
            c.setFillColor(HexColor(self.color))
            
            try:
                # nel caso ci fosse il font italico, allora uso quello
                c.setFont(self.oblique_font_name, self.font_size)
                c.drawString(x, y - self.font_height, block["value"])
                
            except KeyError:
                # altrimenti applico una trasformazione per renderlo obliquo senza fare fallback ad un font base

                c.setFont(self.font_name, self.font_size)
                c.saveState()
                c.transform(1, 0, 0.21, 1, 0, 0) #Rendo il testo obliquo
                c.drawString(x - 0.21 * (y - self.font_height),y - self.font_height,block["value"])
                c.restoreState() #ritorno allo stato salvato

                if self.font_name.endswith("-Bold"):
                    print(f"\033[31mUsing more than one formatting type at the same time is currently unsupported.\033[0m")
                    self.oblique_font_name= self.oblique_font_name.replace("-Bold","")
                    print(f"\033[33mDefaulting to {self.oblique_font_name}.\033[0m")
                else:
                    #print(f"\033[31m'{self.font_name}' font Italic variant is missing, defaulting to 'Helvetica-Oblique'.\033[0m")
                    print(f"\033[31m'{self.font_name}' font Italic variant is missing, using fallback method.\033[0m")
                    print(f"\033[33mPlease import {self.font_name}-Oblique inside the 'Style.json' currently in use.\033[0m")
            
        elif block["type"] == "strikethru":
            c.setFillColor(HexColor(self.color))
            c.setFont(self.font_name, self.font_size)
            c.drawString(x, y - self.font_height, block["value"])
            text_width = stringWidth(block["value"], self.font_name, self.font_size)
            strike_y = y + self.font_size * 0.3 - self.font_height
            c.setStrokeColor(HexColor(self.color))
            c.setLineWidth(1)
            c.line(x, strike_y, x + text_width, strike_y)
        
        elif block["type"] == "underline":
            c.setFillColor(HexColor(self.color))
            c.setFont(self.font_name, self.font_size)
            c.drawString(x, y - self.font_height, block["value"])
            text_width = stringWidth(block["value"], self.font_name, self.font_size)
            underline_y = y - self.font_size 
            c.setStrokeColor(HexColor(self.color))
            c.setLineWidth(1)
            c.line(x, underline_y, x + text_width, underline_y)
        
        elif block["type"] == "link":
            c.setFillColor(HexColor(self.link_color))
            c.setFont(self.font_name, self.font_size)
            c.drawString(x, y - self.font_height, block["value"])
            text_width = stringWidth(block["value"], self.font_name, self.font_size)
            c.linkURL(url=block["path"], rect=(x, y, x + text_width, y - self.font_height), relative=0)
            if self.link_line:
                underline_y = y - self.font_size 
                c.setStrokeColor(HexColor(self.link_color))
                c.setLineWidth(1)
                c.line(x, underline_y, x + text_width, underline_y)

        elif block["type"] == "code":
            c.setFont(self.code_font_name, self.code_font_size)
            text_width = stringWidth(block["value"], self.code_font_name, self.code_font_size)
            code_height = get_font_height(self.code_font_name, self.code_font_size)
            baseline_y = y - self.font_height  # baseline allineata al testo circostante, non al font del code

            c.setFillColor(HexColor(self.code_background_color))
            radius = 5*px
            c.roundRect(
                x,
                baseline_y - self.code_bg_pad_y/2,
                text_width + self.code_bg_pad_x * 2,
                code_height + self.code_bg_pad_y,
                radius,
                stroke=0, fill=1
            )
            c.setFillColor(HexColor(self.code_color))
            c.drawString(x + self.code_bg_pad_x, baseline_y+self.code_bg_pad_y/2, block["value"])
        
        elif block["type"] == "highlight":
            c.setFont(self.font_name, self.font_size)
            text_width = stringWidth(block["value"], self.font_name, self.font_size)
            text_height = get_font_height(self.font_name, self.font_size)
            c.setFillColor(HexColor(self.highlight_background_color))
            line_height = (self.line_height-text_height)
            c.rect(
                x,
                y - self.highlight_pad_y/2 -self.line_spacing - text_height  ,
                text_width + self.highlight_pad_x * 2, 
                text_height + self.highlight_pad_y ,stroke=0, fill=1
            )
            c.setFillColor(HexColor(self.highlight_color))
            c.drawString(x + self.highlight_pad_x, y - text_height, block["value"])
        
        elif block["type"] == "color": #cioè il color inline
            c.setFont(self.font_name, self.font_size)
            c.setFillColor(f"#{block["color"]}")
            c.drawString(x,y-self.font_height,block["value"])

        elif block["type"] == "style": #cioè la prop generale
            modifier = block["property"][0].upper()
            value = block["property"][1:]
            temp_font_height = None

            if value.isdigit():
                self.temp_font_size = int(value)
                self.temp_font_name = self.font_name
                c.setFont(self.font_name, self.temp_font_size)
                get_font_height(self.font_name,self.temp_font_size)

            else:
                self.temp_font_name = value
                self.temp_font_size = self.font_size
                c.setFont(self.temp_font_name, self.font_size)
                get_font_height(self.temp_font_name,self.font_size)
        
            c.drawString(x,y-self.font_height,block["value"])

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
                    line_x += stringWidth(block["value"], self.code_font_name, self.code_font_size) + self.code_bg_pad_x * 2
                elif block["type"] == "highlight":
                    line_x += stringWidth(block["value"], self.font_name, self.font_size) + self.highlight_pad_x * 2
                elif block["type"] == "bold":
                    line_x += stringWidth(block["value"], self.bold_font_name  , self.font_size)
                elif block["type"] == "style":
                    line_x += stringWidth(block["value"], self.temp_font_name  , self.temp_font_size)
                else:
                    line_x += stringWidth(block["value"], self.font_name, self.font_size)

            y -= self.line_height

        return initial_y - y

    def layout(self, page, extra=0):
        if not self.bold_font_name: self.bold_font_name = self.font_name if self.font_name.endswith("-Bold") else self.font_name + "-Bold"
        if not self.oblique_font_name: self.oblique_font_name = self.font_name if self.font_name.endswith("-Oblique") else self.font_name + "-Oblique"
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
        s = parsed_json.get("text", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 12)
        line_spacing = s.get("interline", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color        = s.get("color", "#000000")
        self.margin_top   = s.get("margin-top", 20)
        self.margin_left  = s.get("margin-left", 15)
        self.margin_right = s.get("margin-right", 0)
    
    def layout(self, page):
        super().layout(page)
        self.total_height = self.text_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        return self.margin_top + super().render(c, x + self.margin_left, y - self.margin_top)
    

class List:
    def __init__(self, content, parsed_json):
        s = parsed_json.get("list-block", {})
        self.margin_top    = s.get("margin-top", 20) * px
        self.margin_left   = s.get("margin-left", 40) * px
        self.margin_right  = s.get("margin-right", 0) * px
        self.space_between = s.get("space-between", 10) * px
        self.indent_width  = s.get("indent-width", 20) * px

        self.items = []
        for entry in content:
            indent = entry.get("indent", 0)

            if entry["type"] == "Ul":
                item = Ul_item(entry["value"], parsed_json)
            elif entry["type"] == "Tl":
                item = Tl_item(entry["value"], entry.get("checked", False), parsed_json)
            else:
                continue

            item.margin_left += self.margin_left + indent * self.indent_width
            item.margin_right = self.margin_right 
            self.items.append(item)

        self.total_height = 0

    def layout(self, page):
        self.total_height = self.margin_top
        for i, item in enumerate(self.items):
            self.total_height += item.layout(page)
            if i < len(self.items) - 1:
                self.total_height += self.space_between
        return self.total_height

    def render(self, c, x, y):
        initial_y = y
        y -= self.margin_top
        for i, item in enumerate(self.items):
            y -= item.render(c, x, y)
            if i < len(self.items) - 1:
                y -= self.space_between
        return initial_y - y

class Ul_item(Text):
    def __init__(self, content, parsed_json):
        s = parsed_json.get("unordered-list", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 13)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.bullet       = s.get("bullet-char", "•")
        self.text_pad_l   = s.get("text-pad-left", 20) * px
        self.margin_left  = s.get("margin-left", 40) * px
        self.margin_right = s.get("margin-right", 0) * px
        self.color        = s.get("color", "#f0f6fc")

    def layout(self, page):
        super().layout(page)
        self.total_height = self.text_height
        self.avail_width -= self.text_pad_l
        return self.total_height

    def render(self, c, x, y):
        text_y = y 
        c.setFont(self.font_name, self.font_size)
        c.setFillColor(HexColor(self.color))
        c.drawString(x + self.margin_left, text_y - self.font_height, self.bullet)
        return super().render(c, x + self.margin_left + self.text_pad_l, text_y)

class Tl_item(Text):
    def __init__(self, content, checked, parsed_json):
        s = parsed_json.get("task-list", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 13)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.text_pad_l   = s.get("text-pad-left", 20) * px
        self.margin_left  = s.get("margin-left", 40) * px
        self.margin_right = s.get("margin-right", 0) * px
        self.color        = s.get("color", "#f0f6fc")
        self.checked      = checked

    def draw_check(self, c, x, y):
        c.setStrokeColor(self.color)
        box_height = self.font_height
        box_x = x + self.margin_left
        box_y = y 
        c.setLineWidth(1.0)
        radius = box_height * 0.18
        c.roundRect(box_x, box_y - box_height, box_height, box_height, radius, fill=0, stroke=1)

        if self.checked:
            from reportlab.lib.colors import HexColor as HC
            c.setFillColor(HC("#0969da"))
            c.setStrokeColor(HC("#0969da"))
            c.roundRect(box_x, box_y - box_height, box_height, box_height, radius, fill=1, stroke=0)
            c.setStrokeColor(HC("#ffffff"))
            c.setLineWidth(1.4)
            c.setLineCap(1)
            c.setLineJoin(1)
            m = box_height
            p1 = (box_x + m * 0.18, box_y - m * 0.48)
            p2 = (box_x + m * 0.40, box_y - m * 0.74)
            p3 = (box_x + m * 0.82, box_y - m * 0.28)
            p = c.beginPath()
            p.moveTo(*p1)
            p.lineTo(*p2)
            p.lineTo(*p3)
            c.drawPath(p, fill=0, stroke=1)
            c.setStrokeColor(self.color)
            c.setLineCap(0)
            c.setLineJoin(0)

        return box_height

    def layout(self, page):
        super().layout(page)
        self.total_height = self.text_height 
        return self.total_height

    def render(self, c, x, y):
        text_y = y 
        box_height = self.draw_check(c, x, y-2)
        c.setFont(self.font_name, self.font_size)
        c.setFillColor(HexColor(self.color))
        return super().render(c, x + self.margin_left + box_height + self.text_pad_l, text_y)

class Header(Text):
    def __init__(self, content, level, parsed_json):
        s = parsed_json.get(level, parsed_json.get("header1", {}))
        font_name    = s.get("font-name", "Helvetica-Bold")
        font_size    = s.get("font-size", 18)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color               = s.get("color", "#000000")
        self.margin_top          = s.get("margin-top", 15)
        self.margin_left         = s.get("margin-left", 0)
        self.alignment           = s.get("align", "left")
        self.line_color          = s.get("line-color", "#000000")
        self.line                = s.get("line", True)
        self.line_width          = s.get("line-thickness", 1)
        self.line_start          = s.get("line-start", 0)
        self.line_end            = s.get("line-end", 0)
        self.space_between_line  = s.get("space-between-line", 10)
        self.level               = level

    def layout(self, page):
        super().layout(page)
        if self.line:
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
            end_x   = x + self.content_width - self.line_end
            c.setStrokeColor(HexColor(self.line_color))
            c.setLineWidth(self.line_width)  
            c.line(start_x, text_bottom_y, end_x, text_bottom_y)

        return self.total_height 


class Multiline_Code(Text):
    def __init__(self, content, indent,parsed_json):
        s = parsed_json.get("multiline-code", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 13)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color        = s.get("color", "#f0f6fc")
        self.margin_top   = s.get("margin-top", 25) * px
        self.background   = s.get("background", "#151b23")
        self.padding_x    = s.get("padding-x", 15)
        self.padding_y    = s.get("padding-y", 20)
        self.margin_right = s.get("margin-right", 0) * px 
        self.indent_width  = s.get("indent-width", 40) * px
        self.indent = indent
        self.margin_left  = (s.get("margin-left", 30) * px) + (self.indent*self.indent_width)

    def layout(self, page):
        super().layout(page)
        box_height = self.text_height + self.padding_y
        self.total_height = box_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        box_x      = x + self.margin_left - self.padding_x / 2
        box_top    = y - self.margin_top
        box_height = self.text_height + self.padding_y 
        box_width  = self.page_end + self.padding_x 
        radius = 7*px
        c.setFillColor(HexColor(self.background))
        c.roundRect(box_x , box_top, box_width, -box_height,radius, fill=1, stroke=0)

        super().render(c, x + self.margin_left  + (self.padding_x / 2), y - self.margin_top - self.padding_y / 2)
        return self.total_height


class Blockquote(Text):
    def __init__(self, content, special,indent, parsed_json):
        s = parsed_json.get("quote", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 14)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        
        if special:
            modifier = self.map_special(special)
            self.color      = s.get("color-" + modifier, "#000000")
            self.line_color = s.get("line-color-" + modifier, "#ffffff")
            self.background = s.get("background-" + modifier, "#000000")
        else:
            self.color      = s.get("color", "#adbac7")
            self.line_color = s.get("line-color", "#444c56")
            self.background = s.get("background", "#22272e")

        self.margin_top   = s.get("margin-top", 15) * px
        self.padding_x    = s.get("padding-x", 15)
        self.padding_y    = s.get("padding-y", 15)
        self.indent_width  = s.get("indent-width", 40) * px
        self.margin_left  = (s.get("margin-left", 30) * px) + indent * self.indent_width
        self.margin_right = s.get("margin-right", 15) * px
        
    
    
    def map_special(self, special):
        return {
            "n": "note",
            "t": "tip",
            "i": "important",
            "w": "warning",
            "c": "caution"
        }.get(special)

    def layout(self, page):
        super().layout(page)
        box_height = self.text_height + self.padding_y
        self.total_height = box_height + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        box_x      = x + self.margin_left - self.padding_x / 2
        box_top    = y - self.margin_top
        box_height = self.text_height + self.padding_y 
        box_width  = self.page_end + self.padding_x*2

        c.setFillColor(HexColor(self.background))
        c.rect(box_x, box_top, box_width, -box_height, fill=1, stroke=0)

        c.setLineWidth(2)
        c.setStrokeColor(HexColor(self.line_color))
        c.line(box_x, box_top, box_x, box_top - box_height)

        super().render(c, x + self.margin_left + (self.padding_x / 2), y - self.margin_top - self.padding_y / 2)
        return self.total_height



# =========================
# IMAGE
# =========================

class Image:
    def __init__(self, path, parsed_json, size):
        s = parsed_json.get("image", {})
        self.path         = path
        self.margin_top   = s.get("margin-top", 25)
        self.margin_left  = s.get("margin-left", 25)
        self.size         = size / 100
        self.width, self.height = ImageReader(path).getSize()
        self.totalHeight  = 0

    def layout(self, page):
        self.total_height = self.height * self.size + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        c.drawImage(
            self.path,
            x + self.margin_left,
            y - self.total_height,
            width=self.width * self.size,
            height=self.height * self.size
        )
        return self.total_height 
    
class Hr:
    def __init__(self, parsed_json):
        s = parsed_json.get("hr", {})
        self.color      = s.get("color", "#ffffff")
        self.line_width = s.get("thickness", 1)
        self.style      = s.get("style", "solid")
        self.margin_top = s.get("margin-top", 15)
        self.page_end   = 0
        self.used_y     = 0
    
    def layout(self, page):
        self.page_end = page.width * mm - page.margin_left
        self.used_y   = (self.line_width * px) + self.margin_top
        return self.used_y

    def render(self, c, x, y):
        c.setStrokeColor(HexColor(self.color))
        c.setLineWidth(self.line_width)
        line_y = y - self.margin_top

        if self.style == "solid":
            c.setDash()
        elif self.style == "dash":
            c.setDash(8, 4)
        elif self.style == "dot":
            c.setDash(1, 5)

        c.line(x, line_y, self.page_end, line_y)
        c.setDash()
        return self.used_y

class Cell(Text):
    def __init__(self, content, parsed_json):
        s = parsed_json.get("table", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 13)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)
        self.color = s.get("color", "#e6edf3")

    def natural_width(self):
        """Larghezza del contenuto se stesse su un'unica riga (nessun wrap)."""
        width = 0
        for block in self.content:
            if block["type"] == "code":
                width += stringWidth(block["value"], self.code_font_name, self.code_font_size)
            elif block["type"] == "bold":
                try:
                    width += stringWidth(block["value"], self.bold_font_name, self.font_size)
                except KeyError:
                    width += stringWidth(block["value"], self.font_name, self.font_size)
            else:
                width += stringWidth(block["value"], self.font_name, self.font_size)
        return width

    def layout(self, page, col_width):
        if not self.bold_font_name:
            self.bold_font_name = self.font_name if self.font_name.endswith("-Bold") else self.font_name + "-Bold"
        if not self.oblique_font_name:
            self.oblique_font_name = self.font_name if self.font_name.endswith("-Oblique") else self.font_name + "-Oblique"

        self.content_width = col_width
        self.word_wrap(page, forced_width=col_width)
        self.text_height = self.line_height * len(self.lines)
        self.total_height = self.text_height
        return self.total_height

class Table(Text):

    def __init__(self, content, parsed_json):
        s = parsed_json.get("table", {})
        font_name    = s.get("font-name", "Helvetica")
        font_size    = s.get("font-size", 13)
        line_spacing = s.get("line-spacing", 1.2)
        super().__init__(content, font_name, font_size, line_spacing, parsed_json)

        self.parsed_json = parsed_json
        self.margin_top   = s.get("margin-top", 20) * px
        self.margin_left  = s.get("margin-left", 30) * px
        self.margin_right = s.get("margin-right", 0) * px
        self.cell_padding_x = s.get("padding-x", 8)
        self.cell_padding_y = s.get("padding-y", 6)
        self.border_width  = s.get("border-thickness", 1)
        self.border_color  = s.get("border-color", "#3d444d")
        self.cell_bg_color = s.get("background-color", "#151b23")
        self.cell_txt_color = s.get("color", "#e6edf3")

        # costruisco la griglia di oggetti Cell
        self.grid = []
        for row in content:
            cell_row = []
            for cell_content in row:
                cell_row.append(Cell(cell_content, parsed_json))
            self.grid.append(cell_row)

        self.col_widths = []
        self.row_heights = []
        self.total_height = 0

    def layout(self, page):
        if not self.grid:
            self.total_height = self.margin_top
            return self.total_height

        n_cols = max(len(row) for row in self.grid)
        avail_width = page.content_width - self.margin_left - self.margin_right

        # --- Passata 1: larghezza naturale per colonna ---
        natural_col_widths = [0] * n_cols
        for row in self.grid:
            for i, cell in enumerate(row):
                w = cell.natural_width() + self.cell_padding_x * 2
                if w > natural_col_widths[i]:
                    natural_col_widths[i] = w

        total_natural = sum(natural_col_widths)

        if total_natural <= avail_width or total_natural == 0:
            # ci sta tutto comodamente, nessun clamp necessario
            self.col_widths = natural_col_widths
        else:
            # cap per colonna: una colonna non può mai superare
            # una quota massima "equa" più eventuale spazio extra
            # lasciato dalle colonne più strette della media
            min_col_width = 50 * px  # larghezza minima leggibile, es. per una parola
            max_col_width = avail_width / n_cols * 1.8  # colonna "larga" ma non infinita

            capped = [min(w, max_col_width) for w in natural_col_widths]
            capped = [max(w, min_col_width) for w in capped]

            total_capped = sum(capped)

            if total_capped <= avail_width:
                # lo spazio libero rimasto va redistribuito alle colonne
                # che erano state effettivamente cappate (quelle "grosse"),
                # proporzionalmente al loro sforamento originale
                extra = avail_width - total_capped
                overflow_cols = [i for i, w in enumerate(natural_col_widths) if w > max_col_width]
                if overflow_cols:
                    total_overflow = sum(natural_col_widths[i] - max_col_width for i in overflow_cols)
                    for i in overflow_cols:
                        share = (natural_col_widths[i] - max_col_width) / total_overflow
                        capped[i] += extra * share
                self.col_widths = capped
            else:
                # anche col cap non ci sta: scala tutto proporzionalmente
                scale = avail_width / total_capped
                self.col_widths = [w * scale for w in capped]

        # --- Passata 2: wrap reale sulla larghezza definitiva ---
        self.row_heights = []
        for row in self.grid:
            row_height = 0
            for i, cell in enumerate(row):
                col_w = self.col_widths[i] - self.cell_padding_x * 2
                col_w = max(col_w, 10)  # mai negativo/zero, altrimenti word_wrap va in loop
                cell_h = cell.layout(page, col_w)
                cell_h += self.cell_padding_y * 2
                if cell_h > row_height:
                    row_height = cell_h
            self.row_heights.append(row_height)

        self.max_row_width = sum(self.col_widths)
        self.total_height = sum(self.row_heights) + self.margin_top
        return self.total_height

    def render(self, c, x, y):
        start_y = y
        y -= self.margin_top
        table_x = x + self.margin_left

        for row, row_height in zip(self.grid, self.row_heights):
            cell_x = table_x
            for i, cell in enumerate(row):
                col_w = self.col_widths[i]

                # sfondo cella
                c.setFillColor(HexColor(self.cell_bg_color))
                c.rect(cell_x, y - row_height, col_w, row_height, fill=1, stroke=0)

                # bordo cella
                c.setStrokeColor(HexColor(self.border_color))
                c.setLineWidth(self.border_width)
                c.rect(cell_x, y - row_height, col_w, row_height, fill=0, stroke=1)

                # testo della cella (riusa Text.render per bold/code/link/ecc.)
                cell.color = self.cell_txt_color
                cell.render(c, cell_x + self.cell_padding_x, y - self.cell_padding_y)

                cell_x += col_w

            y -= row_height

        return start_y - y

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
        if element["type"] == "Paragraph":
            objects.append(Paragraph(element["content"], parsed_json))
        elif element["type"] == "Multiline_code":
            objects.append(Multiline_Code(element["content"],element["indent"], parsed_json))
        elif element["type"] == "Blockquote":
            objects.append(Blockquote(element["content"], element["special"],element["indent"], parsed_json))
        elif element["type"] == "list":
            objects.append(List(element["content"], parsed_json))
        elif element["type"] == "table":
            objects.append(Table(element["content"], parsed_json))
        elif element["type"] == "hr":
            objects.append(Hr(parsed_json))
        elif element["type"] == "img":
            try:
                objects.append(Image(element["path"], parsed_json, element["size"]))
            except OSError:
                objects.append(Paragraph([{'type': 'italic', 'value': f"[file:'{element['path']}' Cannot be loaded]"}], parsed_json))
                print(f"\033[31mError loading image '{element['path']}'. Please check the image path.\033[0m")
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
    JsonLoader.main(path)
    
    with open(path, "r") as f:
        return json.load(f)


def render(c, objects, page):
    c.setFillColor(HexColor(page.backgroundColor))
    c.rect(0, 0, page.width * mm, page.height * mm, fill=1, stroke=0)

    for obj in objects:
        page.global_y -= obj.render(c, page.margin_left, page.global_y)


def main(parsed_file, output_path, style_path, font_path):
    
    parsed_json = LoadJson(style_path)

    #------- Debug Json --------
    #print(parsed_json)

    PAGE = parsed_json.get("page", {})
    page = Page(
        PAGE.get("minimum-page-height", 297),
        PAGE.get("page-width", 210)
    )

    FONTS = parsed_json.get("custom-fonts", {})
    for font in FONTS:
        register_font(font, FONTS[font], font_path)

    page.margin_top    = PAGE.get("margin-top", 0)    * px * mm
    page.margin_bottom = PAGE.get("margin-bottom", 15) * px * mm
    page.margin_left   = PAGE.get("margin-left", 10)   * px * mm
    page.margin_right  = PAGE.get("margin-right", 10)  * px * mm
    page.backgroundColor = PAGE.get("background", "#0d1117")

    page.content_width = (page.width * mm) - page.margin_left - page.margin_right

    objects = blocks_to_objects(parsed_file, parsed_json)

    page.height = get_page_height(objects, page)

    page.global_y = (page.height * mm) - page.margin_top

    c = canvas.Canvas(output_path)
    c.setPageSize((page.width * mm, page.height * mm))

    render(c, objects, page)

    c.showPage()
    c.save()
