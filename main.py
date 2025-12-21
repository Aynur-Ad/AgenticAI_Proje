from llm.llm_config import get_llm
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.editor_agent import EditorAgent
from core.pipeline import StoryWorkshopPipeline
from agents.safety import SafetyGuard

def main():
    # 1. Modelleri ve Pipeline'ı Hazırla
    llm = get_llm()
    writer = WriterAgent(llm)
    critic = CriticAgent(llm)
    editor = EditorAgent(llm)
    pipeline = StoryWorkshopPipeline(writer, critic, editor)

    # 2. Kullanıcı Girişi
    user_input = {
        "title": "Kırık Pencere",
        "genre": "üzüntü",
        "characters": ["Elif", "Murat"],
        "theme": "bomba",  # Test için hassas bir kelime
        "length": "short",
        "style": "sade ve hüzünlü Turkce"
    }

    # 3. Güvenlik ve Yönlendirme Kontrolü
    # SafetyGuard sınıfını başlatıyoruz
    guard = SafetyGuard()
    
    # check_and_input metodu ile tarama yapıyoruz
    check = guard.check_and_input(user_input)

    if not check["safe"]:
        # Eğer içerik hassas ise uyarıyı ve öneriyi göster
        print(f"\n{check['message']}")
        print(f"ÖNERİ: {check['suggestion']}")
        
        # Kullanıcıdan onay al
        secim = input("\nÖneriyi kabul edip hikayeyi bu etik açıyla yazmak ister misiniz? (E/H): ")
        
        if secim.lower() == 'h':
            # Temayı etik bir çerçeveye çekerek güncelle
            user_input["theme"] += " (etik ve toplumsal sonuçları çerçevesinde, şiddeti övmeden)"
            print("\n--- Hikaye öneri doğrultusunda hazırlanıyor... ---\n")
        else:
            # Kullanıcı reddederse programı güvenli bir şekilde kapat
            print("İşlem durduruldu. Lütfen daha uygun bir tema seçiniz.")
            return

    # 4. Pipeline'ı Çalıştır (Sadece onay verildiyse veya içerik güvenliyse buraya geçer)
    result = pipeline.run(user_input)

    # 5. Sonuçları Yazdır
    print("\n" + "="*20 + " TASLAK " + "="*20)
    print(result.get("draft_story", "Taslak oluşturulamadı."))

    print("\n" + "="*20 + " ELESTIRI " + "="*20)
    print(result.get("critic_feedback", "Eleştiri alınamadı."))

    print("\n" + "="*20 + " FINAL HIKAYE " + "="*20)
    print(result.get("final_story", "Final metni oluşturulamadı."))

if __name__ == "__main__":
    main()