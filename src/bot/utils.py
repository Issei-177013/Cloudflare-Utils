# Just somthings we need :]

lri, pdi = "\u2066", "\u2069"

def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))