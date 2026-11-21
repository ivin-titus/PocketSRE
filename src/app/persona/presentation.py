"""Keep conversational presentation separate from SRE policy and tool calls."""

from dataclasses import dataclass
from enum import Enum
import re


class Persona(str, Enum):
    KIWI = "kiwi"
    VIKRAM = "vikram"


class Language(str, Enum):
    ENGLISH = "english"
    HINDI = "hindi"
    MALAYALAM = "malayalam"
    HINGLISH = "hinglish"
    MANGLISH = "manglish"


_MALAYALAM = re.compile(r"[\u0D00-\u0D7F]")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_MANGLISH_WORDS = {"aanu", "aayi", "undo", "ille", "nokk", "cheyy", "venam", "entha", "pakshe"}
_HINGLISH_WORDS = {"hai", "kya", "kaise", "karo", "karna", "kar", "nahi", "nahin", "theek", "thik"}


def detect_language(message: str) -> Language:
    """Low-cost deterministic language/style detection for text fallback paths."""
    if _MALAYALAM.search(message):
        return Language.MALAYALAM
    if _DEVANAGARI.search(message):
        return Language.HINDI
    words = set(re.findall(r"[a-z]+", message.lower()))
    if words & _MANGLISH_WORDS:
        return Language.MANGLISH
    if words & _HINGLISH_WORDS:
        return Language.HINGLISH
    return Language.ENGLISH


def language_from(value: object, fallback: Language) -> Language:
    try:
        return Language(str(value).lower())
    except ValueError:
        return fallback


@dataclass(frozen=True)
class Presentation:
    """Only changes how a result is said; it never changes an action request."""

    persona: Persona = Persona.KIWI
    language: Language = Language.ENGLISH

    @property
    def icon_asset(self) -> str:
        return f"src/assets/{self.persona.value}_icon.png"

    def incident_title(self, severity: str, service: str) -> str:
        if self.persona is Persona.VIKRAM:
            return f"{severity} Incident — {service}"
        return f"🌿 Kiwi is on it — {severity} · {service}"

    def incident_intro(self, service: str) -> str:
        copy = {
            Language.ENGLISH: f"I found a signal that needs attention for `{service}`.",
            Language.HINDI: f"`{service}` के लिए ध्यान देने योग्य संकेत मिला है।",
            Language.MALAYALAM: f"`{service}`-നായി ശ്രദ്ധിക്കേണ്ട ഒരു സിഗ്നൽ കണ്ടെത്തി.",
            Language.HINGLISH: f"`{service}` ke liye attention chahiye wala signal mila hai.",
            Language.MANGLISH: f"`{service}`-inu attention venam enna signal kandittundu.",
        }[self.language]
        if self.persona is Persona.VIKRAM:
            return copy.replace("I found", "Detected") if self.language is Language.ENGLISH else copy
        return copy

    def next_steps_label(self) -> str:
        return {
            Language.ENGLISH: "Safe next steps",
            Language.HINDI: "सुरक्षित अगले कदम",
            Language.MALAYALAM: "സുരക്ഷിത അടുത്ത ഘട്ടങ്ങൾ",
            Language.HINGLISH: "Safe next steps",
            Language.MANGLISH: "Safe next steps",
        }[self.language]

    def report_title(self, action: str, service: str) -> str:
        prefix = "Kiwi report" if self.persona is Persona.KIWI else "Execution report"
        return f"{prefix} — {action} → {service}"

    def resolution_title(self, service: str) -> str:
        if self.persona is Persona.KIWI:
            return f"🌿 Back to steady — {service}"
        return f"Resolved — {service}"

    def status_title(self) -> str:
        return "Kiwi’s live check" if self.persona is Persona.KIWI else "PocketSRE — live presence"

    def help_text(self) -> str:
        if self.persona is Persona.KIWI:
            return "🌿 I mirror English, Hindi, Malayalam, Hinglish, and Manglish. Safety checks stay the same in every language."
        return "Language mirroring is active for English, Hindi, Malayalam, Hinglish, and Manglish. Operational safeguards are unchanged."
