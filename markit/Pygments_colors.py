from pygments import lex
from pygments.lexers import get_lexer_for_filename
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound


def main(code, filename, hilight_style="github-dark"):

    style = get_style_by_name(hilight_style)
    try:
        lexer = get_lexer_for_filename(filename)
    
    except ClassNotFound:
        return([{'type': 'text', 'value': code}])

    result = []

    for token_type, value in lex(code, lexer):

        if value == "\n":
            continue

        color = style.style_for_token(token_type)["color"]

        if color:
            result.append({
                "type": "color",
                "value": value,
                "color": color
            })



    return result