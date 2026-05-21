from pygments.lexers import *
from pygments.lexers.special import TextLexer
from pygments.styles import get_style_by_name


def main(lines, style_name):

    style = get_style_by_name(style_name)

    code = "\n".join(lines)

    lexer = PythonLexer()


    print(lexer)

    # testo normale
    if isinstance(lexer, TextLexer):

        return [
            [(line, "#ffffff"), ("\n", "#ffffff")]
            for line in lines
        ]

    tokens = list(lexer.get_tokens(code))

    token_list_colored = []

    for ttype, value in tokens:

        color_str = (
            style.styles.get(ttype)
            or style.styles.get(ttype.parent)
            or "ffffff"
        )

        # pygments può restituire:
        # "bold #ff00aa"
        # quindi prendiamo solo il colore
        if " " in color_str:
            color_str = color_str.split(" ")[-1]

        # fallback
        if color_str == "":
            color_str = "ffffff"

        # HexColor vuole '#'
        if not color_str.startswith("#"):
            color_str = "#" + color_str

        token_list_colored.append((value, color_str))

    linee = []
    tmp = []

    for token in token_list_colored:

        tmp.append(token)

        if token[0] == "\n":
            linee.append(tmp)
            tmp = []

    # ultima riga senza newline finale
    if tmp:
        linee.append(tmp)

    return linee