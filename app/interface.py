import sys
import json
from llm.llm_config import get_llm
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.editor_agent import EditorAgent
from core.pipeline import StoryWorkshopPipeline
from agents.safety import SafetyGuard

# --- GÜNCELLENMİŞ FONKSİYON: DAHA AKILLI DÜZELTİCİ ---
def correct_typos_with_llm(user_input: dict, llm) -> dict:
    """
    Kullanıcı girdisindeki bozuk yazımları, eksik harfleri ve karakter isimlerini düzeltir.
    Örn: "Kucuk Prns" -> "Küçük Prens", "drma" -> "Dram", "nurhgül" -> "Nurgül"
    """
    print("⏳  Yapay zeka başlık ve isimleri analiz edip düzeltiyor...")
    try:
        # Prompt'u GÜÇLENDİRDİK: Sadece imla değil, "Tahmin Etme" yeteneği ekledik.
        prompt = f"""
Sen uzman bir Türkçe Editörü ve Düzeltmenisin.
Görevin: Aşağıdaki JSON verisindeki alanları analiz et ve hatalı/eksik yazımları EN DOĞRU Türkçe haline çevir.

KURALLAR:
1. "Kucuk prns", "Harry pottr" gibi bilinen kitap/film adlarını tanı ve tam doğrusunu yaz (Küçük Prens, Harry Potter).
2. "drma", "fantstik", "korku" gibi türleri düzelt (Dram, Fantastik, Korku).
3. Karakter isimlerindeki yazım yanlışlarını gider ve Baş Harflerini Büyüt (Örn: "nurhgül" -> "Nurgül", "aynur" -> "Aynur").
4. İngilizce karakterlerle yazılmış Türkçe kelimeleri düzelt (s -> ş, i -> ı, g -> ğ, c -> ç vb. bağlama göre).
5. SADECE JSON formatında yanıt ver.

Örnek Davranış:
Girdi: {{"title": "kucuk prns", "genre": "drma", "characters": ["aynur", "nurhgul"]}}
Çıktı: {{"title": "Küçük Prens", "genre": "Dram", "characters": ["Aynur", "Nurgül"]}}

ŞİMDİ BU VERİYİ DÜZELT:
{json.dumps(user_input, ensure_ascii=False)}
"""
        response = llm(prompt).strip()
        
        # JSON temizleme
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        elif response.startswith("json"):
            response = response[4:].strip()

        corrected_data = json.loads(response)
        
        # Eski veriyle birleştir
        user_input.update(corrected_data)
        return user_input

    except Exception as e:
        print(f"⚠️  Düzeltme sırasında hata oluştu (önemsiz): {e}")
        return user_input

def _ask_yes_no(prompt: str) -> bool:
    """Kullanıcıya E/H sorar, True/False döner."""
    while True:
        answer = input(prompt + " (E/H): ").strip().lower()
        if answer in ("e", "evet"):
            return True
        if answer in ("h", "hayır", "hayir"):
            return False
        print("Lütfen sadece E veya H gir.")

def _ask_age() -> int:
    """Kullanıcıdan yaş alır."""
    while True:
        val = input("Yaşınız: ").strip()
        if val.isdigit():
            return int(val)
        print("Lütfen geçerli bir sayı girin (ör. 18).")

def run_interface():
    # 1. LLM'i en başta alıyoruz
    llm = get_llm()

    print("\n=== YAPAY HIKAYE ATOLYESI (TERMINAL) ===\n")

    title = input("Hikaye basligi: ")
    genre = input("Tur (orn: dram, fantastik): ")
    characters = input("Karakterler (virgulle ayir): ")
    theme = input("Tema (orn: umut, kayip, degisim): ")
    length = input("Uzunluk (short / medium / long): ")

    characters_list = [c.strip() for c in characters.split(",") if c.strip()]

    user_input = {
        "title": title,
        "genre": genre,
        "characters": characters_list,
        "theme": theme,
        "length": length,
        "style": "sade ve akici Turkce"
    }

    # --- 1. ADIM: TYPO VE KARAKTER DÜZELTME ---
    user_input = correct_typos_with_llm(user_input, llm)
    
    # Kullanıcıya neyin düzeltildiğini gösterelim
    print(f"\n✅  Algılanan Başlık: {user_input['title']}")
    print(f"✅  Algılanan Tür: {user_input['genre']}")
    # Karakter listesini string olarak göster
    c_str = ", ".join(user_input['characters']) if isinstance(user_input['characters'], list) else str(user_input['characters'])
    print(f"✅  Algılanan Karakterler: {c_str}")
    print("-" * 30)

    # SafetyGuard'a llm veriyoruz
    guard = SafetyGuard(llm)
    forced_safe_mode = False 

    # 🔒 Güvenlik + Tekrar Deneme Döngüsü
    while True:
        safety_result = guard.check_and_input(user_input)

        if safety_result.get("safe", True):
            break

        tier = safety_result.get("tier", "borderline")
        score = safety_result.get("negativity_score", "?")
        msg = safety_result.get("message", "Güvenlik filtresi devreye girdi.")
        sug = safety_result.get("suggestion", "Lütfen daha güvenli bir tema düşün.")

        print(f"\n⚠️  GÜVENLİK UYARISI | Skor: {score}/10 | Seviye: {tier}")
        print(f"Mesaj: {msg}")
        print(f"Öneri: {sug}")

        target_field = "theme"
        display_label = "Tema"
        
        if "Tür" in msg or "Genre" in msg:
            target_field = "genre"
            display_label = "Tür (Genre)"
        elif "Başlık" in msg or "Title" in msg:
            target_field = "title"
            display_label = "Başlık"

        def get_cleaned_input(prompt_text):
            val = input(prompt_text).strip()
            if target_field == "title":
                return val.title()
            return val
        
        if safety_result.get("needs_theme_retry", False):
            print(f"\n⛔ '{display_label}' alanında hassas bir ifade (veya yazım hatası) var.")
            print(f"Devam etmek için {display_label} alanını değiştirmelisiniz.")
            new_val = get_cleaned_input(f"Yeni {display_label}: ")
            user_input[target_field] = new_val
            continue

        if tier == "block":
            print(f"\n⛔ Bu {display_label} ile devam edilemez (Yüksek Risk).")
            new_val = get_cleaned_input(f"Lütfen daha güvenli bir {display_label} girin: ")
            user_input[target_field] = new_val
            continue

        retry = _ask_yes_no(f"\nDaha güvenli bir {display_label} ile tekrar denemek ister misin?")
        
        if retry:
            new_val = get_cleaned_input(f"Yeni {display_label}: ")
            user_input[target_field] = new_val
            continue
        
        age = _ask_age()
        if age < 18: 
            print("\n⛔ 18 yaş altı kullanıcılar için bu tema işlenemez. Program sonlandırılıyor.\n")
            return

        print("\n✔ 18 yaş üstü onaylandı. İçerik 'Güvenli Mod' (PG-13) çerçevesinde işlenecek.")
        forced_safe_mode = True
        break 

    if forced_safe_mode:
        constraints = user_input.get("constraints") or []
        constraints.append(
            "Güvenli mod: zararlı eylemleri detaylı tarif etme/teşvik etme. "
            "Grafik detay verme. Etik boyut, iyileşme, umut ve destek temasına odaklan."
        )
        user_input["constraints"] = constraints
        user_input["style"] = (user_input.get("style") or "") + " | PG, grafik detaysız"
        print("⚠️ Not: Hikaye duygusal ve etik boyuta odaklanacak.\n")

    writer = WriterAgent(llm)
    critic = CriticAgent(llm)
    editor = EditorAgent(llm)
    pipeline = StoryWorkshopPipeline(writer, critic, editor)

    print("\n--- Hikaye üretiliyor... ---\n")
    result = pipeline.run(user_input)

    if result.get("status") == "needs_clarification":
        print("\n❓ YAZARIN SORULARI VAR:\n")
        print(result.get("draft_story"))
    else:
        print("\n" + "="*20 + " TASLAK " + "="*20)
        print(result.get("draft_story", ""))

        print("\n" + "="*20 + " ELESTIRI " + "="*20)
        print(result.get("critic_feedback", ""))

        print("\n" + "="*20 + " FINAL HIKAYE " + "="*20)
        print(result.get("final_story", ""))

if __name__ == "__main__":
    run_interface()