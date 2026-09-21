import re
import unicodedata

_TR = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "I": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    }
)


def slugify(value: str, max_length: int = 180) -> str:
    """Türkçe karakter destekli, URL güvenli slug üretir."""
    value = value.translate(_TR)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9#+]+", "-", value).replace("#", "sharp").replace("+", "plus")
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:max_length].strip("-")


def normalize_tags(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for t in tags:
        norm = slugify(t, max_length=30)
        if norm and norm not in seen:
            seen.append(norm)
    return seen[:10]


def reading_time_minutes(markdown: str) -> int:
    words = len(re.findall(r"\w+", markdown))
    return max(1, round(words / 200))
