import re


def escape_markdown_v2(text: str | None) -> str:
    """ Escape str or return None if None is provided """

    if text is None:
        return None

    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)
