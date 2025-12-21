from __future__ import annotations
from typing import Callable
import json
from agents.safety import SafetyGuard


def _clean_json_text(text: str) -> str:
    # Model bazen ```json ... ``` şeklinde döndürür.
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return cleaned


class CriticAgent:
    """
    Yeni yazarlara rehberlik eden, ancak edebi unsurları ciddiyetle değerlendiren
    Hikaye Eleştirmen Etmeni.

    Güvenlik notu:
    - Hikayeyi yeniden yazmaz.
    - Zararlı içerik üretmez; gerekirse güvenli şekilde uyarır.
    """

    def __init__(self, llm: Callable[[str], str]):
        self.llm = llm

    def run(self, story_text: str) -> str:
        # Eğer story_text zaten bir "ret mesajı" ise eleştirmeye kalkma:
        # (İstersen burada daha sağlam bir kontrol yazabiliriz.)
        if "yardımcı olamam" in story_text.lower():
            return json.dumps({
                "general_evaluation": "Bu içerik güvenlik nedeniyle üretilemediği için edebi değerlendirme yapılmadı.",
                "theme": {"comment": "", "suggestion": ""},
                "language": {"comment": "", "suggestion": ""},
                "characters": {"comment": "", "suggestion": ""},
                "plot": {"comment": "", "suggestion": ""},
                "strengths": [],
                "areas_to_improve": [],
                "confidence_score": 90,
                "next_step_for_writer": "Güvenli bir tema/istekle tekrar dene (ör. umut, dostluk, keşif)."
            }, ensure_ascii=False, indent=2)

        prompt = f"""
Sen yazarlığa yeni başlamış kişilere rehberlik eden,
ancak edebi unsurları ciddiyetle değerlendiren bir HİKÂYE ELEŞTİRMENİ etmensin.

GÜVENLİK VE ETİK KURALLAR:
- Nefret söylemi, taciz, hedef gösterme üretme.
- Kendine zarar verme / intihar teşviki üretme.
- Reşit olmayanları içeren cinsel içerik üretme.
- Yasadışı/tehlikeli eylemlere yönlendirme yapma.
- Kişisel verileri isteme/yayma yapma.
- Hikâyeyi yeniden yazma. Sadece geri bildirim ver.

Cevabını SADECE şu JSON formatında ver:

{{
  "general_evaluation": "Hikaye hakkında genel, destekleyici ama gerçekçi değerlendirme",

  "theme": {{
    "comment": "Temanın ne olduğu ve ne kadar net yansıtıldığı",
    "suggestion": "Temayı güçlendirmek için somut bir öneri"
  }},

  "language": {{
    "comment": "Dil ve anlatımın genel durumu",
    "suggestion": "Dili daha canlı veya etkili yapmak için öner"
  }},

  "characters": {{
    "comment": "Karakterlerin derinliği ve tutarlılığı",
    "suggestion": "Karakterleri geliştirmek için öner"
  }},

  "plot": {{
    "comment": "Olay örgüsünün anlaşılırlığı ve akışı",
    "suggestion": "Olay örgüsünü netleştirmek veya güçlendirmek için öner"
  }},

  "strengths": [
    "Hikayenin güçlü yönü 1",
    "Hikayenin güçlü yönü 2"
  ],

  "areas_to_improve": [
    "Geliştirilmeye açık alan 1",
    "Geliştirilmeye açık alan 2"
  ],

  "confidence_score": 0 ile 100 arası bir tam sayı,

  "next_step_for_writer": "Yazarın bir sonraki adımda deneyebileceği net ve küçük bir gelişim önerisi"
}}

Kurallar:
- Hikâyeyi yeniden yazma.
- Sert/aşağılayıcı ifade kullanma.
- Hikaye çok kısaysa bunu nazikçe belirt.

Hikaye:
{story_text}
""".strip()

        raw = self.llm(prompt)
        cleaned = _clean_json_text(raw)

        # Parse edilebilir olsun diye kontrol (UI’da kullanacaksan önemli)
        try:
            data = json.loads(cleaned)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            # Model JSON bozarsa: güvenli hata çıktısı
            return json.dumps({
                "general_evaluation": "Geri bildirim üretildi ancak JSON biçimi hatalı geldi. Lütfen tekrar dene.",
                "theme": {"comment": "", "suggestion": ""},
                "language": {"comment": "", "suggestion": ""},
                "characters": {"comment": "", "suggestion": ""},
                "plot": {"comment": "", "suggestion": ""},
                "strengths": [],
                "areas_to_improve": [],
                "confidence_score": 40,
                "next_step_for_writer": "Eleştiriyi daha kısa ve net cümlelerle tekrar iste."
            }, ensure_ascii=False, indent=2)
