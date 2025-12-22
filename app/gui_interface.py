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


def apply_safety_flow_with_gui(root: tk.Tk, user_input: dict):
    """
    GUI üzerinden güvenlik akışını yürütür.
    - SafetyGuard ile kontrol eder
    - Gerekirse yeni tema ister
    - Gerekirse yaş sorar
    - 18+ ve hassas tema ise constraints ekler
    DÖNÜŞ:
        (proceed: bool, safe_user_input: dict | None)
    """
    guard = SafetyGuard()
    forced_safe_mode = False

    while True:
        safety_result = guard.check_and_input(user_input)

        if safety_result.get("safe", True):
            # güvenli → döngüden çık
            break

        # güvenli değil
        msg = safety_result.get("message", "Güvenlik filtresi devreye girdi.")
        sug = safety_result.get("suggestion", "Lütfen daha güvenli bir tema düşün.")
        full_msg = f"{msg}\n\nÖneri: {sug}"

        retry = messagebox.askyesno(
            "Güvenlik Uyarısı",
            full_msg + "\n\nDaha güvenli bir tema ile tekrar denemek ister misin?"
        )

        if retry:
            # yeni tema
            new_theme = simpledialog.askstring(
                "Yeni Tema",
                "Yeni, daha güvenli bir tema yazın:"
            )
            if not new_theme:
                messagebox.showinfo(
                    "İptal",
                    "Yeni tema girilmedi, işlem iptal edildi."
                )
                return False, None
            user_input["theme"] = new_theme
            continue  # döngü başa, yeni temayı kontrol et
        else:
            # yaş sor
            age = simpledialog.askinteger(
                "Yaş Doğrulama",
                "Bu temayla devam etmek için yaşınızı girin:"
            )
            if age is None:
                messagebox.showinfo(
                    "İptal",
                    "Yaş bilgisi verilmedi, işlem iptal edildi."
                )
                return False, None

            if age < 18:
                messagebox.showwarning(
                    "Yaş Sınırı",
                    "18 yaş altı kullanıcılar için bu tema işlenemez."
                )
                return False, None

            messagebox.showinfo(
                "Devam Ediliyor",
                "18 yaş üstü onaylandı. Tema korunacak ancak "
                "güvenli/etik çerçevede işlenecek."
            )
            forced_safe_mode = True
            break  # hassas tema + 18+, döngüden çıkıyoruz

    # hassas temayla 18+ devam: ek constraint
    if forced_safe_mode:
        constraints = user_input.get("constraints") or []
        constraints.append(
            "Tema hassas: zararlı eylemleri detaylı tarif etme/teşvik etme. "
            "Duygusal-etik boyut, iyileşme, umut ve destek temasına odaklan."
        )
        user_input["constraints"] = constraints

    return True, user_input


def run_workshop_no_safety(user_input: dict) -> dict:
    """
    Sadece LLM + pipeline kısmı.
    Güvenlik daha önce apply_safety_flow_with_gui ile yapılmış olmalı.
    """
    llm = get_llm()
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
        text="Başlık/Tür/Tema gir → Güvenlik kontrolü → Taslak + Eleştiri + Final",
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
            status_var.set("Çalışıyor... (LLM çağrıları biraz sürebilir)")
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

        # 1) GÜVENLİK akışını ANA THREAD'de çalıştır
        proceed, safe_input = apply_safety_flow_with_gui(root, user_input)
        if not proceed or safe_input is None:
            # kullanıcı iptal etti veya yaş sınırı vs.
            return

        # 2) LLM + pipeline'ı BACKGROUND THREAD'de çalıştır
        set_running(True)
        safe_input = dict(safe_input)  # thread'e kopya verelim

        def worker():
            try:
                result = run_workshop_no_safety(safe_input)
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

                root.after(0, update_ui)

            except Exception as e:
                def show_err():
                    set_running(False)
                    messagebox.showerror(
                        "Hata",
                        f"İşlem sırasında hata oluştu:\n\n{e}\n\n"
                        "Not: 429 quota hatası alıyorsan, Gemini ücretsiz kotanı doldurmuş olabilirsin."
                    )
                root.after(0, show_err)

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
