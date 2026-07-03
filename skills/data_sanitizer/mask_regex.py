import re
from typing import Tuple, Dict

CURRENCY_PATTERN = re.compile(r'\$\d+(?:,\d{3})*(?:\.\d+)?')
EMAIL_PATTERN = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
# Simple heuristic for "Capitalized Word(s) Inc/Corp/LLC/Ltd"
COMPANY_PATTERN = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\s(?:Inc|Corp|LLC|Ltd|Co)\.?)\b')
PERSON_NAME_PATTERN = re.compile(r'\b(Mr|Mrs|Ms|Dr)\.\s[A-Z][a-z]+\s[A-Z][a-z]+\b')


def sanitize(contract_text: str) -> Tuple[str, Dict[str, str]]:
    """
    Masks sensitive entities in contract_text.
    Returns (masked_text, reverse_map) where reverse_map lets you
    de-mask the final output for the human reviewer. reverse_map is
    NEVER sent to the LLM.
    """
    reverse_map: Dict[str, str] = {}
    masked = contract_text
    counter = {"company": 0, "currency": 0, "email": 0, "person": 0}

    def _mask(pattern, label):
        nonlocal masked
        def repl(match):
            counter[label] += 1
            token = f"[{label.upper()}_{counter[label]}]"
            reverse_map[token] = match.group(0)
            return token
        masked = pattern.sub(repl, masked)

    _mask(EMAIL_PATTERN, "email")
    _mask(CURRENCY_PATTERN, "currency")
    _mask(COMPANY_PATTERN, "company")
    _mask(PERSON_NAME_PATTERN, "person")

    return masked, reverse_map


def restore(masked_text: str, reverse_map: Dict[str, str]) -> str:
    """De-masks text using the reverse map, for final human-facing output only."""
    restored = masked_text
    for token, original in reverse_map.items():
        restored = restored.replace(token, original)
    return restored


if __name__ == "__main__":
    sample = "Acme Corp agrees to pay $45,000 to Globex Inc. Contact Mr. John Smith at john@acme.com."
    masked_text, rmap = sanitize(sample)
    print("MASKED:", masked_text)
    print("RESTORED:", restore(masked_text, rmap))
