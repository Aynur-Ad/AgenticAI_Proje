from __future__ import annotations
from typing import Dict, List, Callable, Optional, Any
from agents.safety import SafetyGuard


class WriterAgent:
    """
    Writer Agent - GÜNCELLENMİŞ
    - Yeni yazarlara yönelik hikaye taslağı üretir.
    - Güvenlik/etik kurallara uyar.
    - Belirsiz girişlerde netleştirici soru üretebilir.
    - Başlık tekrarını ve sohbet cümlelerini engeller.
    """

    def __init__(self, llm: Callable[[str], str]):
        """
        llm: callable -> llm(prompt: str) -> str
        """
        self.llm = llm

    def _needs_clarification(self, user_input: Dict) -> bool:
        # Çok basit bir belirsizlik ölçütü:
        # En azından tema veya karakter veya kısa bir olay fikri yoksa belirsiz say.
        theme = (user_input.get("theme") or "").strip()
        chars = user_input.get("characters")
        if isinstance(chars, (list, tuple)):
            chars = ", ".join(chars)
        chars = (chars or "").strip()
        constraints = user_input.get("constraints") or []
        return (not theme) and (not chars) and (len(constraints) == 0)

    def build_clarifying_questions(self, user_input: Dict) -> List[str]:
        """
        ch8'deki 'belirsizlik yönetimi' fikri:
        Muğlak isteklerde kullanıcıya 3-5 net soru sor.
        """
        title = user_input.get("title", "").strip()
        genre = user_input.get("genre", "").strip()

        questions = []
        if not title:
            questions.append("Hikâyenin başlığı ne olsun? (İstersen ben de önerebilirim.)")
        if not genre:
            questions.append("Tür ne olsun? (kısa öykü / bilim kurgu / korku / romantik / fantastik vb.)")

        questions += [
            "Ana karakter(ler) kim? 1-2 cümleyle tarif eder misin?",
            "Hikâyenin teması ne olsun? (ör. dostluk, kayıp, umut, adalet)",
            "Hikâye nerede ve ne zaman geçsin?",
            "Mutlu mu, ters köşe mi, açık uçlu mu bitsin?"
        ]
        return questions[:5]

    def _build_prompt(self, user_input: Dict) -> str:
        title = user_input.get("title", "Bir Hikâye")
        genre = user_input.get("genre", "kısa öykü")

        characters = user_input.get("characters", "")
        if isinstance(characters, (list, tuple)):
            characters = ", ".join(characters)

        theme = user_input.get("theme", "")
        style = user_input.get("style", "akıcı, sade Türkçe")
        constraints = user_input.get("constraints", [])
        length = user_input.get("length", "short")

        length_hint = {
            "short": "yaklaşık 2-3 paragraf",
            "medium": "yaklaşık 4-6 paragraf",
            "long": "detaylı ve uzun"
        }.get(length, "orta uzunlukta")

        # Güvenlik + etik sistem talimatı (ch8: güven + şeffaflık)
        safety_rules = """
GÜVENLİK VE ETİK KURALLAR:
- Nefret söylemi, hedef gösterme, taciz/hakaret içeren içerik üretme.
- Reşit olmayanları içeren cinsel içerik üretme.
- Kendine zarar verme / intihar teşviki üretme.
- Yasadışı/tehlikeli eylemlere (silah, bomba, hack, uyuşturucu vb.) yönlendirme yapma.
- Kişisel veri isteme/yayma (adres, telefon, kimlik vb.) yapma.
- Eğer kullanıcı isteği bu sınırlara giriyorsa: KISA bir şekilde reddet ve güvenli alternatif öner.
"""

        prompt = f"""
Sen yazarlığa yeni başlayan kişilere örnek olacak bir HİKÂYE YAZARI etmensin.
Önceliğin güvenilir, güvenli ve sorumlu bir şekilde yardımcı olmak.

{safety_rules}

Görevin:
Aşağıdaki bilgilere dayanarak {length_hint}, akıcı ve anlaşılır bir hikâye TASLAĞI yaz.

ÖNEMLİ:
- Bu bir ilk taslaktır, mükemmel olmak zorunda değil.
- Tema, karakter ve olay örgüsü hissedilmeli.
- Editör/eleştirmen tarafından geliştirilebilir boşluklar bırak.

ÇOK ÖNEMLİ BİÇİM KURALLARI (BUNA KESİNLİKLE UY):
1. Çıktıda ASLA 'Başlık: ...' veya '**Başlık**' satırı yazma.
2. 'Harika bir fikir', 'İşte taslağınız' gibi giriş cümleleri YAZMA.
3. 'Giriş:', 'Gelişme:', 'Sonuç:' gibi bölüm başlıkları ATMA.
4. SADECE ve SADECE hikaye metnini yaz.
5. Doğrudan hikayenin ilk cümlesiyle başla.

Başlık (Sadece konu için): {title}
Tür: {genre}
Karakterler: {characters}
Tema: {theme}
Üslup: {style}
""".strip()

        if constraints:
            prompt += "\n\nKısıtlar:"
            for c in constraints:
                prompt += f"\n- {c}"

        prompt += "\n\nHikâye Taslağı:\n"
        return prompt

    def generate_draft(self, user_input: Dict) -> Dict[str, Any]:
        """
        Dönüş:
        {
           "type": "draft" | "clarification",
           "content": str (hikaye metni) | list (soru listesi)
        }
        """
        # 1) Belirsizlik kontrolü
        if self._needs_clarification(user_input):
            questions = self.build_clarifying_questions(user_input)
            return {
                "type": "clarification",
                "content": questions  # List[str] döner
            }

        # 2) Hikaye üretimi
        prompt = self._build_prompt(user_input)
        
        # LLM çıktısını al ve temizle
        raw_text = self.llm(prompt).strip()
        
        # Manuel temizlik: Model inatla "Başlık:" yazarsa silelim
        lines = raw_text.split('\n')
        cleaned_lines = []
        for line in lines:
            lower_line = line.lower().strip()
            # Başlık satırlarını atla
            if lower_line.startswith("başlık:") or lower_line.startswith("**başlık"):
                continue
            # Sohbet giriş cümlelerini atla
            if "işte taslağınız" in lower_line or "hikaye taslağı:" in lower_line:
                continue
            cleaned_lines.append(line)
            
        final_story_text = "\n".join(cleaned_lines).strip()
        
        return {
            "type": "draft",
            "content": final_story_text
        }