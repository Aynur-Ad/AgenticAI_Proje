class StoryWorkshopPipeline:

  
    """
    Yapay Hikaye Atolyesi Pipeline'i

    - Writer: ilk taslak uretir
    - Critic: hikayeyi degerlendirir
    - Editor: geri bildirimleri uygulayarak hikayeyi gelistirir

    Amac:
    Yeni yazarlara adim adim rehberlik eden
    kontrollu bir atölye sureci sunmak
    """

    def __init__(self, writer, critic, editor):
        self.writer = writer
        self.critic = critic
        self.editor = editor

    def run(self, user_input: dict) -> dict:
        """
        Atolye akisini baslatir.

        Girdi:
        - user_input: WriterAgent icin girilen bilgiler

        Cikti:
        - Atolye surecinin tum adimlarini iceren dict
        """

        # 1️⃣ Hikaye taslagi
        draft_story = self.writer.generate_draft(user_input)

        # 2️⃣ Eleştirmen geri bildirimi
        critic_feedback = self.critic.run(draft_story)

        # 3️⃣ Editör düzenlemesi
        final_story = self.editor.revise(draft_story, critic_feedback)

        return {
            "draft_story": draft_story,
            "critic_feedback": critic_feedback,
            "final_story": final_story
        }
