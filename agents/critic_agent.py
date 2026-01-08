from __future__ import annotations
from typing import Callable, Dict, Any
import json
import re
from agents.safety import SafetyGuard

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

    def _clean_json_text(self, text: str) -> str:
        # Markdown kod bloklarını temizle
        text = text.replace("```json", "").replace("```", "")
        return text.strip()

    def _fix_json_with_llm(self, broken_text: str, error_msg: str) -> str:
        """
        Model bozuk JSON verirse, hatayı gösterip düzeltmesini isteriz.
        """
        repair_prompt = f"""
        Aşağıdaki JSON metninde bir format hatası var.
        Hata: {error_msg}
        
        Bozuk Metin:
        {broken_text}
        
        Görevin:
        Sadece düzeltilmiş, geçerli JSON'ı döndür. Başka açıklama yapma.
        """
        return self.llm(repair_prompt)

    def run(self, story_text: str) -> str:
        # Güvenlik reddi varsa eleştirme
        if "yardımcı olamam" in story_text.lower() or "güvenlik filtresi" in story_text.lower():
            return json.dumps({
                "general_evaluation": "Güvenlik nedeniyle içerik oluşturulamadı.",
                "strengths": [], "areas_to_improve": [], 
                "confidence_score": 0, "next_step_for_writer": "Güvenli bir tema seç."
            }, ensure_ascii=False)

        prompt = f"""
        Sen acımasız değil ama çok titiz bir EDEBİ ELEŞTİRMENSİN.
        
        Görevin: Hikayeyi analiz et ve Editörün işini kolaylaştıracak SOMUT öneriler ver.
        Sadece 'Karakter zayıf' deme. 'Murat karakteri daha çok konuşmalı' gibi net konuş.

        Çıktıyı SADECE geçerli bir JSON olarak ver. Format:
        {{
          "general_evaluation": "Genel özet",
          
          "theme": {{
            "comment": "Tema analizi",
            "suggestion": "Temayı güçlendirmek için SOMUT öneri (Örn: Şu cümleyi ekle...)"
          }},
          
          "language": {{
             "comment": "Dil kullanımı",
             "suggestion": "Dili düzeltmek için SOMUT öneri"
          }},
          
          "characters": {{
             "comment": "Karakter analizi",
             "suggestion": "Karakter gelişimi için SOMUT öneri"
          }},
          
          "plot": {{
             "comment": "Olay örgüsü",
             "suggestion": "Kurguyu düzeltmek için SOMUT öneri"
          }},
          
          "strengths": ["Güçlü yön 1", "Güçlü yön 2"],
          "areas_to_improve": ["Zayıf yön 1", "Zayıf yön 2"],
          "confidence_score": 85,
          "next_step_for_writer": "Yazarın yapması gereken tek bir net eylem."
        }}

        Hikaye:
        {story_text}
        """

        raw_response = self.llm(prompt)
        cleaned_response = self._clean_json_text(raw_response)

        # JSON PARSE VE RETRY MEKANİZMASI
        try:
            # Önce parse etmeyi dene
            parsed = json.loads(cleaned_response)
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as e:
            # Hata varsa: 1 kereye mahsus modeli tekrar çağırıp düzelttir
            print(f"⚠️ JSON hatası algılandı: {e}. Onarılıyor...")
            fixed_response = self._fix_json_with_llm(cleaned_response, str(e))
            cleaned_fixed = self._clean_json_text(fixed_response)
            
            try:
                # Tekrar dene
                parsed = json.loads(cleaned_fixed)
                return json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                # Yine olmazsa fallback (çökmemesi için)
                return json.dumps({
                    "general_evaluation": "Sistem hatası: Eleştiri formatı düzeltilemedi.",
                    "strengths": [], "areas_to_improve": [], "confidence_score": 0,
                    "next_step_for_writer": "Lütfen tekrar deneyin."
                }, ensure_ascii=False)