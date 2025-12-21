from __future__ import annotations
from typing import Dict, List, Callable, Optional
from agents.safety import SafetyGuard


class WriterAgent:
    """
    Writer Agent
    - Yeni yazarlara yönelik hikaye taslağı üretir.
    - Güvenlik/etik kurallara uyar.
    - Belirsiz girişlerde netleştirici soru üretebilir.
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

Kurallar:
- Türkçe yaz.
- Giriş, gelişme ve sonuç olsun.
- Aşırı edebi veya karmaşık dil kullanma.
- Okuyucu için doğal ve anlaşılır bir anlatım kullan.

Başlık: {title}
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

    def generate_draft(self, user_input: Dict) -> str:
        # 1) Güvenlik ön kontrolü
         
    # Güvenlik kontrolünü burada tamamen devre dışı bırakabilir 
    # veya sadece bilgilendirme amaçlı tutabilirsiniz.
    # Çünkü ana kontrol zaten main.py içinde yapıldı.

        prompt = self._build_prompt(user_input)
        return self.llm(prompt) # Doğrudan hikaye üretimine geç

        # 2) Belirsizlik yönetimi (istersen burada soru döndürebilirsin)
        if self._needs_clarification(user_input):
            questions = self.build_clarifying_questions(user_input)
            # Bu tasarımda direkt soru listesi dönüyoruz (UI’da kullanıcıya sorup tekrar çağırabilirsin).
            return "İsteğini netleştirmek için birkaç soru:\n- " + "\n- ".join(questions)

        prompt = self._build_prompt(user_input)
        return self.llm(prompt)
