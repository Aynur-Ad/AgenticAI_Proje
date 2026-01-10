import threading
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from tkinter import ttk

from llm.llm_config import get_llm
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.editor_agent import EditorAgent
from core.pipeline import StoryWorkshopPipeline
from agents.safety import SafetyGuard

# --- YAZIM HATASI DÜZELTİCİ ---
def correct_typos_with_llm(user_input: dict, llm) -> dict:
    """
    Kullanıcı girdisindeki bariz yazım hatalarını (Typos) düzeltir.
    Örn: "öümcek" -> "Örümcek", "korku evi" -> "Korku Evi"
    """
    try:
        # LLM'e sadece JSON verip düzeltmesini istiyoruz
        prompt = f"""
Sen bir Türkçe İmla Denetçisisin.
Aşağıdaki JSON verisindeki "title", "genre", "theme" ve "characters" alanlarını düzelt.

KURALLAR:
1. Başlıkları "Title Case" yap (İlk harfler büyük).
2. "characters" listesindeki HER İSMİN baş harfini büyüt (Örn: ["elif", "can"] -> ["Elif", "Can"]).
3. Sadece JSON formatında yanıt ver. Başka hiçbir şey yazma.
4. Anlamı bozma, sadece imla düzelt.

Girdi JSON:
{json.dumps(user_input, ensure_ascii=False)}
"""
        response = llm(prompt).strip()
        
        # JSON temizleme (Markdown ```json ... ``` varsa siler)
        if "```" in response:
            response = response.split("```")[1].replace("json", "").strip()
        elif response.startswith("json"):
            response = response[4:].strip()

        corrected_data = json.loads(response)
        
        # Eski veriyle birleştirir
        user_input.update(corrected_data)
        return user_input

    except Exception as e:
        print(f"Typo düzeltme hatası: {e}")
        return user_input # Hata olursa orijinalini döndürür

def apply_safety_flow_with_gui(root: tk.Tk, user_input: dict, llm):

    # GUI üzerinden güvenlik akışını yürütür.
    
    guard = SafetyGuard(llm)
    forced_safe_mode = False

    while True:
        safety_result = guard.check_and_input(user_input)

        # Güvenli ise çık
        if safety_result.get("safe", True):
            break

        tier = safety_result.get("tier", "borderline")
        score = safety_result.get("negativity_score", "?")
        msg = safety_result.get("message", "Güvenlik filtresi devreye girdi.")
        sug = safety_result.get("suggestion", "Lütfen daha güvenli bir içerik düşün.")
        full_msg = f"Skor: {score}/10 | Seviye: {tier}\n\n{msg}\n\nÖneri: {sug}"

        # Hangi alanın hatalı olduğunu tespit ediyoruz
        target_field = "theme"   # Varsayılan olarak Tema
        display_label = "Tema"
        
        # Mesajın içinde "Tür" veya "Başlık" geçiyorsa hedefi değiştiriyoruz
        if "Tür" in msg or "Genre" in msg:
            target_field = "genre"
            display_label = "Tür (Genre)"
        elif "Başlık" in msg or "Title" in msg:
            target_field = "title"
            display_label = "Başlık"
            
        # Başlık girilirse otomatik baş harfleri büyütme fonksiyonu
        def clean_input(val):
            if not val: return val
            if target_field == "title": # Sadece başlık ise Title Case yap
                return val.strip().title()
            return val.strip()

        # ✅ 0) Yazim hatali bile olsa hassas kelime yakalandiysa
        if safety_result.get("needs_theme_retry", False):
            messagebox.showwarning(
                f"{display_label} Değiştirilmeli",
                full_msg + f"\n\nBu ifade hassas sayılır. Devam etmek için '{display_label}' alanını değiştirmelisin."
            )
            new_val = simpledialog.askstring(f"Yeni {display_label}", f"Yeni, daha güvenli bir {display_label} yazın:")
            
            if not new_val:
                messagebox.showinfo("İptal", "Değişiklik yapılmadı, işlem iptal edildi.")
                return False, None
            
            user_input[target_field] = clean_input(new_val) 
            continue

        # 1) HIGH RISK: block -> sadece ilgili alanı değiştir
        if tier == "block":
            messagebox.showwarning("Güvenlik Uyarısı", full_msg + "\n\nBu içerik ile devam edemeyiz.")
            new_val = simpledialog.askstring(f"Yeni {display_label}", f"Yeni, daha güvenli bir {display_label} yazın:")
            
            if not new_val:
                messagebox.showinfo("İptal", "Değişiklik yapılmadı, işlem iptal edildi.")
                return False, None
            
            user_input[target_field] = clean_input(new_val) 
            continue

        # 2) BORDERLINE: değiştir mi, yoksa safe mode ile devam mı?
        retry = messagebox.askyesno(
            "Güvenlik Uyarısı",
            full_msg + f"\n\nDaha güvenli bir {display_label} ile tekrar denemek ister misin?\n"
                       f"(Evet: Yeni {display_label})  (Hayır: Güvenli modda devam)"
        )

        if retry:
            new_val = simpledialog.askstring(f"Yeni {display_label}", f"Yeni, daha güvenli bir {display_label} yazın:")
            if not new_val:
                messagebox.showinfo("İptal", "İşlem iptal edildi.")
                return False, None
            
            user_input[target_field] = clean_input(new_val) 
            continue

        # Hayır -> safe mode ile devam (isteğe bağlı yaş sorusu)
        
        age = simpledialog.askinteger("Yaş (Opsiyonel)", "Daha uygun bir ton için yaşınızı girin (iptal = sorma):")
        if age is not None and age < 13:
            constraints = user_input.get("constraints") or []
            constraints.append("Çocuk dostu: korku/şiddet yok, yumuşak dil, umut ve yardımlaşma odaklı.")
            user_input["constraints"] = constraints

        messagebox.showinfo(
            "Güvenli Mod",
            "Aynı konu korunacak ama güvenli/etik çerçevede (PG) işlenecek."
        )
        forced_safe_mode = True
        break

    # safe mode constraint
    if forced_safe_mode:
        constraints = user_input.get("constraints") or []
        constraints.append(
            "Güvenli mod: zararlı eylemleri detaylı tarif etme/teşvik etme. "
            "Grafik detay verme. Etik boyut, iyileşme, umut ve destek temasına odaklan."
        )
        user_input["constraints"] = constraints
        user_input["style"] = (user_input.get("style") or "") + " | PG, grafik detaysız"

    return True, user_input

def run_workshop_no_safety(user_input: dict, llm) -> dict:
    writer = WriterAgent(llm)
    critic = CriticAgent(llm)
    editor = EditorAgent(llm)
    pipeline = StoryWorkshopPipeline(writer, critic, editor)
    return pipeline.run(user_input)

def _pretty_json_if_possible(text: str) -> str:
    try:
        obj = json.loads(text)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return text


def _copy_to_clipboard(root: tk.Tk, text: str):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()


def create_gui():
    root = tk.Tk()
    
    BG_COLOR = "#f5f7fa"   # açık modern arka plan
    root.configure(bg=BG_COLOR)

    root.title("Yapay Hikaye Atölyesi")
    root.geometry("980x720")
    root.minsize(900, 650)

    # ---- ttk theme
    style = ttk.Style()
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    style.configure("TLabel", padding=(2, 2))
    style.configure("TButton", padding=(10, 6))
    style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
    style.configure("Sub.TLabel", font=("Segoe UI", 10))

    # ---- üst header
    header = ttk.Frame(root, padding=12)
    header.pack(fill="x")
    ttk.Label(header, text="Yapay Hikaye Atölyesi", style="Header.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text="Başlık/Tür/Tema gir → Yazım Hatası Kontrolü → Güvenlik Kontrolü → Taslak + Eleştiri + Final",
        style="Sub.TLabel"
    ).pack(anchor="w", pady=(4, 0))

    # ---- ana içerik
    main = ttk.Frame(root, padding=12)
    main.pack(fill="both", expand=True)

    main.columnconfigure(0, weight=1, uniform="cols")
    main.columnconfigure(1, weight=2, uniform="cols")
    main.rowconfigure(0, weight=1)

    form_card = ttk.Labelframe(main, text="Girdi", padding=12)
    form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    out_card = ttk.Labelframe(main, text="Çıktılar", padding=12)
    out_card.grid(row=0, column=1, sticky="nsew")

    # ---- form alanları
    form_card.columnconfigure(1, weight=1)

    ttk.Label(form_card, text="Hikaye Başlığı").grid(row=0, column=0, sticky="w")
    entry_title = ttk.Entry(form_card)
    entry_title.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(form_card, text="Tür (dram, fantastik...)").grid(row=1, column=0, sticky="w")
    entry_genre = ttk.Entry(form_card)
    entry_genre.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(form_card, text="Karakterler (virgülle)").grid(row=2, column=0, sticky="w")
    entry_chars = ttk.Entry(form_card)
    entry_chars.grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(form_card, text="Tema").grid(row=3, column=0, sticky="w")
    entry_theme = ttk.Entry(form_card)
    entry_theme.grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(form_card, text="Uzunluk").grid(row=4, column=0, sticky="w")
    length_var = tk.StringVar(value="short")
    length_menu = ttk.Combobox(
        form_card,
        textvariable=length_var,
        values=["short", "medium", "long"],
        state="readonly",
    )
    length_menu.grid(row=4, column=1, sticky="w", pady=4)

    ttk.Label(form_card, text="Stil").grid(row=5, column=0, sticky="w")
    style_var = tk.StringVar(value="sade ve akıcı Türkçe")
    entry_style = ttk.Entry(form_card, textvariable=style_var)
    entry_style.grid(row=5, column=1, sticky="ew", pady=4)

    # ---- status & progress
    status_var = tk.StringVar(value="Hazır")
    status_line = ttk.Label(form_card, textvariable=status_var)
    status_line.grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))

    progress = ttk.Progressbar(form_card, mode="indeterminate")
    progress.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    # ---- outputs: notebook
    out_card.columnconfigure(0, weight=1)
    out_card.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(out_card)
    notebook.grid(row=0, column=0, sticky="nsew")

    tab_draft = ttk.Frame(notebook, padding=8)
    tab_critic = ttk.Frame(notebook, padding=8)
    tab_final = ttk.Frame(notebook, padding=8)

    notebook.add(tab_draft, text="Taslak")
    notebook.add(tab_critic, text="Eleştiri")
    notebook.add(tab_final, text="Final")

    for tab in (tab_draft, tab_critic, tab_final):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

    ttk.Label(tab_draft, text="İlk taslak metin").grid(row=0, column=0, sticky="w")
    text_draft = scrolledtext.ScrolledText(tab_draft, wrap="word")
    text_draft.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
    ttk.Button(
        tab_draft,
        text="Kopyala",
        command=lambda: _copy_to_clipboard(root, text_draft.get("1.0", "end-1c")),
    ).grid(row=2, column=0, sticky="e", pady=(8, 0))

    ttk.Label(tab_critic, text="Eleştirmen geri bildirimi (JSON olarak)").grid(row=0, column=0, sticky="w")
    text_feedback = scrolledtext.ScrolledText(tab_critic, wrap="word")
    text_feedback.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
    ttk.Button(
        tab_critic,
        text="Kopyala",
        command=lambda: _copy_to_clipboard(root, text_feedback.get("1.0", "end-1c")),
    ).grid(row=2, column=0, sticky="e", pady=(8, 0))

    ttk.Label(tab_final, text="Geliştirilmiş final hikaye").grid(row=0, column=0, sticky="w")
    text_final = scrolledtext.ScrolledText(tab_final, wrap="word")
    text_final.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
    ttk.Button(
        tab_final,
        text="Kopyala",
        command=lambda: _copy_to_clipboard(root, text_final.get("1.0", "end-1c")),
    ).grid(row=2, column=0, sticky="e", pady=(8, 0))

    # ---- butonlar
    btn_row = ttk.Frame(form_card)
    btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    btn_row.columnconfigure(0, weight=1)
    btn_row.columnconfigure(1, weight=1)

    def clear_outputs():
        text_draft.delete("1.0", tk.END)
        text_feedback.delete("1.0", tk.END)
        text_final.delete("1.0", tk.END)

    def set_running(is_running: bool):
        if is_running:
            run_button.config(state="disabled")
            clear_button.config(state="disabled")
            progress.start(12)
            # Not: status mesajını çağıran yere bırakalım
        else:
            progress.stop()
            run_button.config(state="normal")
            clear_button.config(state="normal")
            status_var.set("Hazır")

    def on_run():
        title = entry_title.get().strip()
        genre = entry_genre.get().strip()
        chars = entry_chars.get().strip()
        theme = entry_theme.get().strip()
        length = length_var.get().strip()
        story_style = entry_style.get().strip() or "sade ve akıcı Türkçe"

        if not title or not genre or not theme:
            messagebox.showwarning(
                "Eksik Bilgi",
                "Lütfen en az başlık, tür ve tema alanlarını doldurun."
            )
            return

        chars_list = [c.strip() for c in chars.split(",") if c.strip()]

        user_input = {
            "title": title,
            "genre": genre,
            "characters": chars_list,
            "theme": theme,
            "length": length,
            "style": story_style,
        }

        clear_outputs()

        # ==========================================
        # 0) LLM YÜKLEME VE YAZIM HATASI DÜZELTME
        # ==========================================
        llm = get_llm()
        
        # Kullanıcıya bilgi ver
        status_var.set("Yazım hataları kontrol ediliyor...")
        progress.start(10)
        root.update()

        # Typo düzeltme çağrısı
        corrected_input = correct_typos_with_llm(user_input, llm)

        # Düzeltilenleri ekrana yansıtır (GUI Update)
        entry_title.delete(0, tk.END)
        entry_title.insert(0, corrected_input.get("title", ""))

        entry_genre.delete(0, tk.END)
        entry_genre.insert(0, corrected_input.get("genre", ""))

        entry_theme.delete(0, tk.END)
        entry_theme.insert(0, corrected_input.get("theme", ""))
        
        # Karakter listesini "Ali, Veli" formatına çevirip kutuya yaz
        c_list = corrected_input.get("characters", [])
        if isinstance(c_list, list):
            c_str = ", ".join(c_list)
        else:
            c_str = str(c_list)
            
        entry_chars.delete(0, tk.END)
        entry_chars.insert(0, c_str)
        
        root.update() # Ekranı yenile

        # ==========================================
        # 1) GÜVENLİK AKIŞI (Düzeltilmiş veriyle)
        # ==========================================
        status_var.set("Güvenlik kontrolü yapılıyor...")
        root.update()

        proceed, safe_input = apply_safety_flow_with_gui(root, corrected_input, llm)

        if not proceed or safe_input is None:
            # Kullanıcı iptal etti
            progress.stop()
            status_var.set("İptal edildi.")
            return

        # ==========================================
        # 2) LLM + PIPELINE (Arka Planda)
        # ==========================================
        set_running(True)
        status_var.set("Hikaye üretiliyor...")
        
        safe_input = dict(safe_input)  # thread'e kopya verelim

        def worker():
            try:
                result = run_workshop_no_safety(safe_input, llm)
                if result is None:
                    root.after(0, lambda: set_running(False))
                    return

                draft = result.get("draft_story", "")
                critic = result.get("critic_feedback", "")
                final = result.get("final_story", "")

                def update_ui():
                    text_draft.insert(tk.END, draft)
                    text_feedback.insert(tk.END, _pretty_json_if_possible(critic))
                    text_final.insert(tk.END, final)
                    notebook.select(tab_final)
                    set_running(False)
                    status_var.set("Tamamlandı.")

                root.after(0, update_ui)
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Hata", str(e)))
                root.after(0, lambda: set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    run_button = ttk.Button(btn_row, text="Atölyeyi Başlat", command=on_run)
    run_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

    clear_button = ttk.Button(btn_row, text="Temizle", command=clear_outputs)
    clear_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    # örnek default değerler
    entry_title.insert(0, "Kırık Pencere")
    entry_genre.insert(0, "dram")
    entry_chars.insert(0, "Elif, Murat")
    entry_theme.insert(0, "umut")

    root.mainloop()


if __name__ == "__main__":
    create_gui()