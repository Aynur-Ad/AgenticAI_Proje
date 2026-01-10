from __future__ import annotations

class StoryWorkshopPipeline:
    """
    Yapay Hikaye Atolyesi Pipeline'i
    """

    def __init__(self, writer, critic, editor):
        self.writer = writer
        self.critic = critic
        self.editor = editor

    def run(self, user_input: dict) -> dict:

        """
        Atolye akisini baslatir.
        Başlık, Baş Harfleri Büyük (Title Case) formatında eklenir.
        
        """

        # Başlığı al ve düzgün formatla (Örn: "kırık pencere" -> "Kırık Pencere")
        raw_title = user_input.get("title", "Başlıksız")
        display_title = raw_title.strip().title()

        # 1️⃣ Writer: Hikaye taslagi
        writer_output = self.writer.generate_draft(user_input)
        
        # Eğer soru sorma durumu varsa (Belirsizlik):
        if isinstance(writer_output, dict) and writer_output.get("type") == "clarification":
            # Soruları olduğu gibi döndür
            questions = "\n".join(f"- {q}" for q in writer_output["content"])
            return {
                "status": "needs_clarification",
                "draft_story": questions,
                "critic_feedback": "",
                "final_story": ""
            }
        
        # İçeriği al
        draft_text = ""
        if isinstance(writer_output, dict):
            draft_text = writer_output.get("content", "")
        else:
            draft_text = writer_output

        # --- Başlığı Taslağın Başına Ekle ---
        full_draft_story = f"📄 {display_title}\n{'-'*len(display_title)}\n\n{draft_text}"

        # 2️⃣ Eleştirmen: (Orijinal metni değerlendirsin)
        critic_feedback = self.critic.run(draft_text)

        # 3️⃣ Editör: Düzenleme
        final_text = self.editor.revise(draft_text, critic_feedback)

        # --- Başlığı Finalin Başına Ekle ---
        full_final_story = f"📖 {display_title}\n{'-'*len(display_title)}\n\n{final_text}"

        return {
            "status": "complete",
            "draft_story": full_draft_story,
            "critic_feedback": critic_feedback,
            "final_story": full_final_story
        }