from llm.llm_config import get_llm
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.editor_agent import EditorAgent
from core.pipeline import StoryWorkshopPipeline
from agents.safety import SafetyGuard


def _ask_yes_no(prompt: str) -> bool:
    """
    Kullanıcıya E/H sorar, True/False döner.
    """
    while True:
        answer = input(prompt + " (E/H): ").strip().lower()
        if answer in ("e", "evet"):
            return True
        if answer in ("h", "hayır", "hayir"):
            return False
        print("Lütfen sadece E veya H gir.")


def _ask_age() -> int:
    """
    Kullanıcıdan yaş alır, sayı girilene kadar sorar.
    """
    while True:
        val = input("Yaşınız: ").strip()
        if val.isdigit():
            return int(val)
        print("Lütfen geçerli bir sayı girin (ör. 18).")


def run_interface():
    print("\n=== YAPAY HIKAYE ATOLYESI ===\n")

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

    guard = SafetyGuard()
    forced_safe_mode = False  # 18+ olup hassas temayla devam edersek True olacak

    # 🔒 Güvenlik + tekrar deneme döngüsü
    while True:
        safety_result = guard.check_and_input(user_input)

        if safety_result.get("safe", True):
            # Güvenli istek -> direkt çık
            break

        # Güvenli DEĞİLSE:
        print("\n⚠️ Güvenlik filtresi devreye girdi.")
        msg = safety_result.get("message")
        sug = safety_result.get("suggestion")
        if msg:
            print("Mesaj:", msg)
        if sug:
            print("Öneri:", sug)

        # Kullanıcıya sor: yeni, güvenli bir tema ile devam etmek ister mi?
        retry = _ask_yes_no("\nDaha güvenli bir tema ile tekrar denemek ister misin?")
        if retry:
            new_theme = input("Yeni, daha güvenli bir tema yaz: ")
            user_input["theme"] = new_theme
            # döngü başa sarar, yeni tema ile tekrar kontrol edilir
            continue

        # Kullanıcı H dedi -> yaş sor
        age = _ask_age()
        if age < 18:
            print("\n⛔ 18 yaş altı kullanıcılar için bu tema işlenemez. Program sonlandırılıyor.\n")
            return

        print("\n✔ 18 yaş üstü onaylandı. Tema korunacak ancak güvenli/etik çerçevede işlenecek.")
        forced_safe_mode = True
        break  # döngüden çıkıp pipeline'a geçeceğiz

    # Eğer hassas temayla 18+ olarak devam ediyorsak WriterAgent'a ek kısıt ver
    if forced_safe_mode:
        constraints = user_input.get("constraints") or []
        constraints.append(
            "Tema hassas: zararlı eylemleri detaylı tarif etme veya teşvik etme. "
            "Olayın duygusal, psikolojik ve etik boyutuna; iyileşme, umut ve "
            "destek temalarına odaklan."
        )
        user_input["constraints"] = constraints
        print("\n⚠️ Hikaye zararlı eylemleri teşvik etmeyecek; "
              "duygusal ve etik boyut ile iyileşme sürecine odaklanacak.\n")

    # ✅ Buraya gelindiyse istek artık pipeline için uygun
    llm = get_llm()
    writer = WriterAgent(llm)
    critic = CriticAgent(llm)
    editor = EditorAgent(llm)

    pipeline = StoryWorkshopPipeline(writer, critic, editor)

    print("\n--- Hikaye uretiliyor... ---\n")
    result = pipeline.run(user_input)

    print("\n=== ILK TASLAK ===\n")
    print(result["draft_story"])

    print("\n=== ELESTIRMEN GERIBILDIRIMI ===\n")
    print(result["critic_feedback"])

    print("\n=== GELISTIRILMIS HIKAYE ===\n")
    print(result["final_story"])


if __name__ == "__main__":
    run_interface()
