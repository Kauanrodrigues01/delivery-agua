import re
import unicodedata


def normalize_text(name: str) -> str:
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", name)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Remove caracteres especiais e espaços, deixa só letras, números e underline
    no_special = re.sub(r"[^a-zA-Z0-9_]+", "", no_accent.replace(" ", "_"))
    return no_special.lower()
