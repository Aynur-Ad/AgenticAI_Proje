import sys
import os
from llm.llm_config import get_llm
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from agents.editor_agent import EditorAgent
from core.pipeline import StoryWorkshopPipeline
from agents.safety import SafetyGuard
from app.gui_interface import create_gui


def main():
    print("==========================================")
    print("   YAPAY HIKAYE ATÖLYESİ - BAŞLATICI")
    print("==========================================")
    print("Çalışma modunu seçiniz:")
    print(" [T] Terminal Arayüzü (CLI)")
    print(" [G] Grafik Arayüz (GUI)")
    print("==========================================")

    while True:
        choice = input("Seçiminiz (T/G): ").strip().upper()
        
        if choice == 'T':
            print("\n>>> Terminal Arayüzü Başlatılıyor...\n")
            try:
                # app/interface.py dosyasındaki run_interface fonksiyonunu çağırır
                from app.interface import run_interface
                run_interface()
            except ImportError as e:
                print(f"HATA: 'app/interface.py' dosyası veya 'run_interface' fonksiyonu bulunamadı.\nDetay: {e}")
            except Exception as e:
                print(f"Beklenmeyen bir hata oluştu: {e}")
            break

        elif choice == 'G':
            print("\n>>> Grafik Arayüz (GUI) Başlatılıyor...\n")
            try:
                # app/gui_interface.py dosyasındaki create_gui fonksiyonunu çağırır
                from app.gui_interface import create_gui
                create_gui()
            except ImportError as e:
                print(f"HATA: 'app/gui_interface.py' dosyası veya 'create_gui' fonksiyonu bulunamadı.\nDetay: {e}")
            except Exception as e:
                print(f"Beklenmeyen bir hata oluştu: {e}")
            break
            
        else:
            print("Hatalı giriş! Lütfen sadece 'T' veya 'G' yazıp Enter'a basın.")

if __name__ == "__main__":
    
    create_gui()