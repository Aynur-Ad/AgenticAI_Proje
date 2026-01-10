from __future__ import annotations
from typing import Callable


class EditorAgent:
    """
    Eleştirmen geri bildirimlerini uygulayarak hikayeyi geliştiren Editör Etmeni.
    - Güvenlik kurallarına uyar.
    - Hikayeyi tamamen baştan yazmaz; temel fikri korur.
    - Çıktıda başlık veya giriş cümlesi (meta-text) bulunmasını engeller.
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
- Eleştirmenin JSON içindeki "suggestion" (öneri) kısımlarını MUTLAKA uygula.
- Hikayenin akışını bozmadan, temel fikri KORUYARAK dili daha edebi ve profesyonel hale getir.
- Yeni yazarı korkutacak aşırı değişiklikler yapma.

ÇOK ÖNEMLİ BİÇİM KURALLARI (BUNA KESİNLİKLE UY):
1. Çıktıda ASLA 'Başlık: ...', 'Revize Edilmiş Metin' veya '**Başlık**' satırı yazma.
2. 'İşte düzenlenmiş hali', 'Önerileri uyguladım' gibi giriş cümleleri YAZMA.
3. SADECE ve SADECE revize edilmiş hikaye metnini yaz.
4. Doğrudan hikayenin ilk cümlesiyle başla.
5. Eleştiriyi tekrar etme veya açıklama yapma.

Hikaye Taslağı:
{story_text}

Eleştirmen Geri Bildirimi (JSON):
{critic_feedback_json}

Geliştirilmiş Hikaye:
""".strip()

        # LLM'i çağır ve boşlukları temizle
        raw_text = self.llm(prompt).strip()

        # Manuel Temizlik (Fallback): Eğer model hala inatla "Başlık:" veya "Revize Metin:" gibi şeyler yazarsa onları siliyoruz.
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            lower_line = line.lower().strip()
            
            # Başlık satırlarını atla
            if lower_line.startswith("başlık:") or lower_line.startswith("**başlık"):
                continue
            
            # "Revize edilmiş metin:" gibi başlıkları atla
            if lower_line.startswith("revize") or lower_line.startswith("geliştirilmiş"):
                continue
                
            # "İşte hikayeniz" tarzı sohbet cümlelerini atla
            if "işte" in lower_line and "hikaye" in lower_line:
                continue
                
            cleaned_lines.append(line)

        # Temizlenmiş satırları birleştir
        final_story_text = "\n".join(cleaned_lines).strip()

        return final_story_text