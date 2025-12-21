from __future__ import annotations
from typing import Callable
from agents.safety import SafetyGuard


class EditorAgent:
    """
    Eleştirmen geri bildirimlerini uygulayarak hikayeyi geliştiren Editör Etmeni.
    - Güvenlik kurallarına uyar.
    - Hikayeyi tamamen baştan yazmaz; temel fikri korur.
    """

    def __init__(self, llm: Callable[[str], str]):
        self.llm = llm

    def revise(self, story_text: str, critic_feedback_json: str) -> str:
        # Eğer hikaye zaten güvenlik nedeniyle üretilemediyse:
        if "yardımcı olamam" in story_text.lower():
            return story_text

        prompt = f"""
Sen yazarlığa yeni başlamış kişilere yardım eden destekleyici bir HİKÂYE EDİTÖRÜ etmensin.

GÜVENLİK VE ETİK KURALLAR:
- Nefret söylemi, taciz, hedef gösterme üretme.
- Kendine zarar verme / intihar teşviki üretme.
- Reşit olmayanları içeren cinsel içerik üretme.
- Yasadışı/tehlikeli eylemlere yönlendirme yapma.
- Kişisel verileri isteme/yayma yapma.

Sana:
1) Bir hikaye taslağı
2) Bu hikayeye ait bir eleştirmen geri bildirimi (JSON)

verilecek.

Görevin:
- Eleştirileri dikkatlice uygula.
- Hikayeyi daha akıcı ve tutarlı hale getir.
- Temel fikri KORU.
- Hikayeyi tamamen baştan yazma.
- Yeni yazarı korkutacak aşırı değişiklikler yapma.

ÖNEMLİ:
- Eleştiriyi tekrar etme.
- Akademik açıklama yazma.
- Sadece GELİŞTİRİLMİŞ HİKAYEYİ yaz.

Hikaye Taslağı:
{story_text}

Eleştirmen Geri Bildirimi (JSON):
{critic_feedback_json}

Geliştirilmiş Hikaye:
""".strip()

        return self.llm(prompt)
