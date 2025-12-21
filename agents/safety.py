from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import re

@dataclass
class SafetyResult:
    ok: bool
    message: str = ""
    suggestion: str = "" # Öneri kısmını buraya ekledik
    category: Optional[str] = None

class SafetyGuard:
    # Hassas kelimeler için Regex tanımları
    _SELF_HARM = re.compile(r"\b(intihar|kendimi öldür|canıma kıy|bilek kes|self-harm)\b", re.IGNORECASE)
    _HATE = re.compile(r"\b(ırkçı|nefret|soykırım|etnik temizlik|naz(i|izm))\b", re.IGNORECASE)
    _HARASS = re.compile(r"\b(tehdit et|şantaj|zorla|ifşa|dox|adresini bul)\b", re.IGNORECASE)
    _ILLEGAL = re.compile(r"\b(bomba|silah yap|uyuşturucu üret|hackle|phishing|kart kopya|cinayet|suç|şiddet)\b", re.IGNORECASE)

    def check_and_input(self, user_input: Dict) -> Dict:
        """
        Main.py'deki 'guard.check_and_input' çağrısı ile tam uyumlu metot.
        Hem kontrol yapar hem de öneri sunar.
        """
        text = " ".join(str(v) for v in user_input.values() if v is not None).lower()

        # 1. Yasadışı / Şiddet Kontrolü (Cinayet, Bomba vb.)
        if self._ILLEGAL.search(text):
            return {
                "safe": False,
                "message": "⚠️ Talebiniz yasadışı veya hassas temalar (şiddet, suç vb.) içeriyor.",
                "suggestion": "Doğrudan şiddeti anlatmak yerine; olayın 'etik boyutuna', 'vicdan azabına' veya 'adaletin sağlanmasına' odaklanmaya ne dersiniz?"
            }

        # 2. Kendine Zarar Verme Kontrolü
        if self._SELF_HARM.search(text):
            return {
                "safe": False,
                "message": "⚠️ Hassas içerik (kendine zarar verme) algılandı.",
                "suggestion": "Bu temayı işlemek yerine, zorluklarla başa çıkma ve umut odaklı bir iyileşme hikayesi kurgulayabiliriz."
            }

        # Her şey yolundaysa
        return {"safe": True}