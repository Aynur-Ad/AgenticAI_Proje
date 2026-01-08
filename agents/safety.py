from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any
import json
import re

@dataclass
class SafetyResult:
    safe: bool
    negativity_score: int
    tier: str  # "ok" | "borderline" | "block"
    message: str = ""
    suggestion: str = ""
    category: Optional[str] = None
    risk_breakdown: Optional[Dict[str, int]] = None
    reasons: Optional[list[str]] = None
    needs_theme_retry: bool = False  # tema yeniden girilmeli mi?


class SafetyGuard:
    # Regex fallback patterns
    _SELF_HARM = re.compile(
        r"\b(intihar|kendimi öldür|kendimi oldur|canıma kıy|cani\u0307ma kiy|bilek kes|self-harm)\b",
        re.IGNORECASE
    )
    _HATE = re.compile(r"\b(ırkçı|irkci|nefret|soykırım|soykirim|etnik temizlik|naz(i|izm))\b", re.IGNORECASE)
    _HARASS = re.compile(r"\b(tehdit et|şantaj|santaj|zorla|ifşa|ifsa|dox|adresini bul)\b", re.IGNORECASE)
    _ILLEGAL_VIOLENCE = re.compile(
        r"\b(bomba|silah yap|uyuşturucu üret|uyusturucu uret|hackle|phishing|kart kopya|cinayet|suç|suc|şiddet|siddet)\b",
        re.IGNORECASE
    )

    def __init__(self, llm: Optional[Callable[[str], str]] = None):
        self.llm = llm

        # TÜRKÇE HASSAS KELİME LİSTESİ (Fuzzy Matching için)
        # Format: ("kelime", "kategori", tolerans_miktarı, SKOR_ETKİSİ)
        # GÜNCELLEME: Artık her kelimenin bir 'SKOR' değeri var.
        # 8-10: Kesin Yasak (Block)
        # 5-7: Sınırda (Borderline) -> Güvenli mod sorulur
        self._FUZZY_KEYWORDS = [
            # --- KESİN BLOKLANACAKLAR (Score: 8-10) ---
            ("tecavuz", "cinsel", 2, 9),
            ("ensest", "cinsel", 1, 9),
            ("cocuk pornosu", "yasa_disi", 3, 10),
            ("pedofili", "yasa_disi", 2, 10),
            ("sapik", "cinsel", 1, 8),
            ("iskence", "siddet", 2, 8),
            ("kafa kesme", "siddet", 2, 8),
            ("snuff", "siddet", 0, 9),
            ("gercek cinayet", "siddet", 3, 9),
            ("soykirim", "nefret", 2, 9),
            ("irkci", "nefret", 1, 8),
            ("fasist", "nefret", 1, 8),

            # --- SINIRDA OLANLAR (Score: 5-7) -> Güvenli Mod Sorulacak ---
            ("cinayet", "siddet", 1, 6),
            ("olum", "siddet", 1, 6),
            ("oldurme", "siddet", 2, 6),
            ("vahset", "siddet", 1, 6),
            ("katliam", "siddet", 2, 7),
            ("kan", "siddet", 0, 5),
            ("seri katil", "siddet", 2, 6),
            ("intihar", "kendine_zarar", 2, 6), # Edebi olabilir
            ("bilek kes", "kendine_zarar", 2, 7),
            ("kendimi oldur", "kendine_zarar", 3, 7),
            ("bomba yapimi", "yasa_disi", 3, 7),
            ("uyusturucu", "yasa_disi", 3, 7),
            ("kacakcilik", "yasa_disi", 3, 6),
            ("kara borsa", "yasa_disi", 2, 5),
        ]

    # =========================
    # PUBLIC
    # =========================
    def check_and_input(self, user_input: Dict) -> Dict:
        # 1. Alanları al
        theme = str(user_input.get("theme", "") or "").strip()
        genre = str(user_input.get("genre", "") or "").strip()
        title = str(user_input.get("title", "") or "").strip()

        # Yardımcı iç fonksiyon: Fuzzy kontrolü yapıp skora göre Tier belirler
        def evaluate_field(field_name, text_val):
             hit = self._fuzzy_check_string(text_val)
             if hit is not None:
                cat, matched_kw, base_score = hit
                
                # Skor 8 ve üzeriyse -> BLOCK
                if base_score >= 8:
                    return SafetyResult(
                        safe=False, negativity_score=base_score, tier="block",
                        message=f"⛔ {field_name} alanında KESİN YASAKLI ifade: '{matched_kw}'",
                        suggestion="Bu içerik politikalarımıza aykırı.",
                        category=cat, risk_breakdown={cat: base_score},
                        reasons=[f"{field_name} alanında '{matched_kw}' tespit edildi."],
                        needs_theme_retry=True
                    )
                # Skor 5-7 arasındaysa -> BORDERLINE
                else:
                    return SafetyResult(
                        safe=False, negativity_score=base_score, tier="borderline",
                        message=f"⚠️ {field_name} alanında hassas ifade: '{matched_kw}'",
                        suggestion="Güvenli modda devam edebiliriz veya değiştirebilirsin.",
                        category=cat, risk_breakdown={cat: base_score},
                        reasons=[f"{field_name} alanında '{matched_kw}' tespit edildi."],
                        needs_theme_retry=False # Seçim hakkı ver
                    )
             return None

        # 2. Alanları Kontrol Et
        res_genre = evaluate_field("Tür (Genre)", genre)
        if res_genre: return self._to_dict(res_genre)

        res_theme = evaluate_field("Tema", theme)
        if res_theme: return self._to_dict(res_theme)

        res_title = evaluate_field("Başlık", title)
        if res_title: return self._to_dict(res_title)

        # 4. Genel Metin Kontrolü (LLM + Regex)
        text = f"Başlık: {title}\nTür: {genre}\nTema: {theme}\nKarakterler: {user_input.get('characters', '')}"
        
        res = None
        if self.llm is not None:
            try:
                res = self._score_with_llm(text)
            except Exception:
                res = None
        
        if res is None:
            res = self._score_with_regex(text)

        return self._to_dict(res)

    def _to_dict(self, res: SafetyResult) -> Dict:
        return {
            "safe": res.safe,
            "negativity_score": res.negativity_score,
            "tier": res.tier,
            "message": res.message,
            "suggestion": res.suggestion,
            "category": res.category,
            "risk_breakdown": res.risk_breakdown or {},
            "reasons": res.reasons or [],
            "needs_theme_retry": res.needs_theme_retry,
        }

    # =========================
    # LLM scoring (TR JSON)
    # =========================
    def _score_with_llm(self, text: str) -> SafetyResult:
        prompt = self._build_prompt(text)
        raw = self.llm(prompt)
        data = self._parse_json_safely(raw)

        score = int(data.get("olumsuzluk_skoru", 0))
        score = max(0, min(10, score))

        tier, safe, msg, sug = self._decide(score)

        category = data.get("kategori")
        risk = self._sanitize_breakdown(data.get("risk_dagilimi"))
        reasons = self._sanitize_reasons(data.get("gerekceler"))
        suggestion = str(data.get("oneri", "")).strip() or sug
        message = msg

        return SafetyResult(
            safe=safe,
            negativity_score=score,
            tier=tier,
            message=message,
            suggestion=suggestion,
            category=category,
            risk_breakdown=risk,
            reasons=reasons,
            needs_theme_retry=(score >= 8) # Sadece çok yüksek skorlarda zorla değiştir
        )

    def _build_prompt(self, text: str) -> str:
        return (
            "Sen bir hikaye yazma uygulamasi icin guvenlik siniflandiricisin.\n"
            "SADECE gecerli JSON dondur. JSON disinda hicbir yazi yazma.\n\n"
            "Gorev:\n"
            "- Kullanici girdisini analiz et.\n"
            "- 0 ile 10 arasinda 'olumsuzluk_skoru' uret.\n"
            "- 'kategori' sec.\n"
            "- Her kategori icin 0-10 arasi risk skoru ver.\n"
            "- Kisa gerekceler yaz.\n"
            "- Tamamen Turkce bir 'oneri' ver.\n\n"
            "KURALLAR:\n"
            "1. EDEBİ/KURGUSAL Şiddet (Cinayet romanı, savaş dramı) -> Puan: 4-6 (Borderline/Sınırda).\n"
            "2. AŞIRI VAHŞET, NEFRET, İSTİSMAR, GERÇEK ZARAR -> Puan: 8-10 (Block/Yasak).\n"
            "3. 'Tür' masum olsa bile 'Tema' vahşet içeriyorsa Puanı yükselt.\n\n"
            "Kategoriler: kendine_zarar, siddet, nefret, taciz, yasa_disi, cinsel, diger\n\n"
            "JSON semasi:\n"
            "{\n"
            '  "olumsuzluk_skoru": 0,\n'
            '  "kategori": "siddet",\n'
            '  "risk_dagilimi": {"kendine_zarar":0,"siddet":0,"nefret":0,"taciz":0,"yasa_disi":0,"cinsel":0,"diger":0},\n'
            '  "gerekceler": ["..."],\n'
            '  "oneri": "..." \n'
            "}\n\n"
            f"Kullanici girdisi:\n{text}\n"
        )

    def _parse_json_safely(self, raw: str) -> Dict[str, Any]:
        if not raw: return {}
        raw = raw.strip()
        if raw.startswith("{") and raw.endswith("}"):
            try: return json.loads(raw)
            except: pass
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except: return {}
        return {}

    def _sanitize_breakdown(self, val: Any) -> Dict[str, int]:
        base = {"kendine_zarar": 0, "siddet": 0, "nefret": 0, "taciz": 0, "yasa_disi": 0, "cinsel": 0, "diger": 0}
        if not isinstance(val, dict): return base
        for k, v in val.items():
            kk = str(k)
            if kk in base:
                try: base[kk] = max(0, min(10, int(v)))
                except: pass
        return base

    def _sanitize_reasons(self, val: Any) -> list[str]:
        if isinstance(val, list): return [str(x) for x in val][:5]
        return []

    # =========================
    # Decision (0-10) - GÜNCELLENDİ
    # =========================
    def _decide(self, score: int):
        if score <= 4:
            return "ok", True, "", ""
        if 5 <= score <= 7:
            # GÜNCELLEME: 7 Puan artık Borderline (Sınırda) kabul ediliyor.
            # Böylece hemen engellemek yerine kullanıcıya soruluyor.
            return (
                "borderline",
                False,
                "⚠️ Hassas içerik (Dram/Gerilim potansiyeli).",
                "Temayı değiştirebiliriz ya da güvenli/etik çerçevede (PG) işleyebiliriz.",
            )
        return (
            "block",
            False,
            "⛔ Tehlikeli içerik (Yüksek Risk).",
            "Bu içerik politikalarımıza aykırı (Nefret, İstismar, Vahşet).",
        )

    # =========================
    # Regex fallback scoring (TR)
    # =========================
    def _score_with_regex(self, text: str) -> SafetyResult:
        t = text.lower()
        score = 0
        category = None
        reasons = []
        breakdown = {"kendine_zarar": 0, "siddet": 0, "nefret": 0, "taciz": 0, "yasa_disi": 0, "cinsel": 0, "diger": 0}

        if self._ILLEGAL_VIOLENCE.search(t):
            score = max(score, 7) # Sınırda başlat
            category = "siddet"
            breakdown["siddet"] = 7
            reasons.append("Şiddet/yasa dışı ifade algılandı (regex).")

        if self._SELF_HARM.search(t):
            score = max(score, 7) # Sınırda başlat
            category = "kendine_zarar"
            breakdown["kendine_zarar"] = 7
            reasons.append("Kendine zarar verme ifadesi algılandı (regex).")

        if self._HATE.search(t):
            score = max(score, 8) # Direkt yasak
            category = "nefret"
            breakdown["nefret"] = 8
            reasons.append("Nefret söylemi algılandı (regex).")

        if self._HARASS.search(t):
            score = max(score, 7)
            category = "taciz"
            breakdown["taciz"] = 7
            reasons.append("Taciz/tehdit ifadesi algılandı (regex).")

        tier, safe, msg, sug = self._decide(score)
        return SafetyResult(
            safe=safe, negativity_score=score, tier=tier,
            message=msg, suggestion=sug, category=category,
            risk_breakdown=breakdown, reasons=reasons, needs_theme_retry=(score >= 8)
        )

    # =========================
    # FUZZY KONTROLLER - GÜNCELLENDİ
    # =========================
    def _fuzzy_check_string(self, text: str) -> Optional[tuple[str, str, int]]:
        if not text:
            return None
        txt = text.lower()
        
        # Liste formatı artık: (kelime, kategori, tolerans_miktarı, SKOR)
        for kw, cat, max_dist, score in self._FUZZY_KEYWORDS:
            if self._contains_fuzzy_keyword(txt, kw, max_dist=max_dist):
                return cat, kw, score
        return None

    def _contains_fuzzy_keyword(self, text: str, keyword: str, max_dist: int = 1) -> bool:
        tokens = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", text.lower())
        kw = keyword.lower()
        for t in tokens:
            if abs(len(t) - len(kw)) > max_dist:
                continue
            if self._levenshtein(t, kw) <= max_dist:
                return True
        return False

    def _levenshtein(self, a: str, b: str) -> int:
        if a == b: return 0
        if not a: return len(b)
        if not b: return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            curr = [i]
            for j, cb in enumerate(b, start=1):
                ins = curr[j - 1] + 1
                dele = prev[j] + 1
                sub = prev[j - 1] + (0 if ca == cb else 1)
                curr.append(min(ins, dele, sub))
            prev = curr
        return prev[-1]