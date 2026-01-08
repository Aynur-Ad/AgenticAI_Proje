import sys
import os

# Proje dizinini yola ekle (Import hatası almamak için şart)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("==========================================")
    print("   YAPAY HIKAYE ATÖLYESİ - BAŞLATICI")
    print("==========================================")
    print(" [T] Terminal Modu")
    print(" [G] Grafik Arayüz (GUI)")
    print("==========================================")

    while True:
        secim = input("Seçiminiz (T/G): ").strip().upper()
        
        if secim == 'T':
            print("\n>>> Terminal başlatılıyor...\n")
            try:
                # app/interface.py içindeki ana fonksiyonunu çağırıyoruz
                # NOT: interface.py dosyanın içinde kodların bir fonksiyon (örn: run_interface) içinde olmalı.
                from app.interface import run_interface
                run_interface()
            except ImportError:
                print("HATA: app/interface.py dosyasında 'run_interface' fonksiyonu bulunamadı.")
            except Exception as e:
                print(f"HATA: {e}")
            break

        elif secim == 'G':
            print("\n>>> GUI başlatılıyor...\n")
            try:
                # app/gui_interface.py içindeki ana fonksiyonu çağırıyoruz
                from app.gui_interface import create_gui
                create_gui()
            except ImportError:
                print("HATA: app/gui_interface.py dosyasında 'create_gui' fonksiyonu bulunamadı.")
            except Exception as e:
                print(f"HATA: {e}")
            break
            
        else:
            print("Lütfen sadece T veya G giriniz.")

if __name__ == "__main__":
    main()