# 📚 Yapay Hikâye Atölyesi
### Üretken Yapay Zekâ, Güvenlik Koruması ve Çok-Etmenli Mimari

**Yapay Hikâye Atölyesi**, üretken yapay zekâ modellerini, çok-etmenli (multi-agent) mimariyi ve gelişmiş güvenlik filtrelerini birleştirerek kullanıcı girdilerine göre yaratıcı, güvenli ve edebi hikâyeler üreten bir sistemdir.

Sistem; kullanıcı hatalarını otomatik düzelten bir ön işleyici, içerik güvenliğini sağlayan bir denetçi ve hikâyeyi adım adım oluşturan **Yazar, Eleştirmen ve Editör** etmenlerinden oluşur.

---

## 🎯 Projenin Amacı
* **Otomatik Hikâye Üretimi:** Kullanıcı girdilerine (Başlık, Tür, Karakterler, Tema) dayalı özgün hikâyeler oluşturmak.
* **İnsan-Yapay Zeka İşbirliği:** Bir yayın evindeki yazı ekibini (Yazar → Eleştirmen → Editör) yapay zeka ajanlarıyla simüle etmek.
* **Güvenlik ve Etik:** Zararlı içerikleri (şiddet, nefret söylemi vb.) filtreleyerek veya "Güvenli Mod" (PG-13) çerçevesinde işleyerek sorumlu yapay zeka kullanımı sağlamak.
* **Akıllı Kullanıcı Deneyimi:** Kullanıcının yazım hatalarını (Typo) tolere eden ve otomatik düzelten akıllı bir arayüz sunmak.

---

## 🧩 Etmen ve Modül Yapısı
Sistem, özelleşmiş görevlere sahip yapay zekâ etmenlerinin iş birliği ile çalışır:

### 🧠 1. Akıllı Düzeltmen (Typo Fixer)
Sistemin giriş kapısıdır. Kullanıcının girdiği verileri (örn: "kucuk prns", "drma") analiz eder; bunları doğru Türkçe formuna, kitap/film adlarına ve Title Case formatına otomatik olarak çevirir.

### 🛡️ 2. Güvenlik Görevlisi (Safety Guard)
Düzeltilmiş içeriği tarar ve analiz eder:
* **Fuzzy Matching:** Yazım hatalı yasaklı kelimeleri (Regex + Levenshtein) yakalar.
* **LLM Analizi:** Tür masum olsa bile (örn: Masal) temanın şiddet içerip içermediğini kontrol eder.
* **Güvenli Mod:** Sınırda (borderline) içerikler için kullanıcı onayıyla içeriği yumuşatır (PG-13).

### ✍️ 3. Yazar Etmen (Writer Agent)
Doğrulanmış ve güvenli girdilere göre hikâyenin ilk taslağını oluşturur. Başlık tekrarlarından kaçınır ve doğrudan kurguya odaklanır.

### 🧐 4. Eleştirmen Etmen (Critic Agent)
Taslağı edebi açıdan (akış, karakter gelişimi, tutarlılık) inceler ve JSON formatında somut geliştirme önerileri sunar.

### 📝 5. Editör Etmen (Editor Agent)
Yazarın taslağını ve Eleştirmenin notlarını alarak hikâyeyi revize eder, parlatır ve son haline getirir.

---

## 🔄 Sistem Akışı

Verinin kullanıcıdan çıktıya kadar izlediği yol aşağıdadır:

```text
+---------------------+
|  👤 Kullanıcı       |
| (Başlık/Tür/Tema)   |
+----------+----------+
           |
           v
+-----------------------------+
| 🧠 Akıllı Düzeltmen (Typo)  | <--- Yazım hatalarını düzeltir
|     (LLM-Based Fixer)       |      ("kucuk" -> "Küçük")
+----------+------------------+
           |
           v
+-----------------------------+
| 🛡️ Güvenlik Görevlisi       | <--- İçerik Denetimi
| (Regex + Fuzzy + LLM Score) |
+----------+------------------+
           |
    +------+-------+
    |              |
 ⛔ Yasaklı     ✅ Güvenli / ⚠️ Onaylı (Güvenli Mod)
    |              |
    v              v
+-------+   +-----------------------------+
| İPTAL |   | 🏭 YAPAY HİKAYE ATÖLYESİ    |
+-------+   |                             |
            |  1. ✍️ Yazar (Taslak)       |
            |             ⬇               |
            |  2. 🧐 Eleştirmen (Analiz)  |
            |             ⬇               |
            |  3. 📝 Editör (Revize)      |
            +-------------+---------------+
                          |
                          v
                  +-------+-------+
                  | 📚 FİNAL ÇIKTI|
                  +---------------+

🏗 Sistem Mimarisi ve Teknoloji
Proje modüler bir yapıda geliştirilmiştir ve aşağıdaki katmanlardan oluşur:

Arayüz Katmanı:

app/gui_interface.py: Tkinter tabanlı, sekmeli ve modern masaüstü arayüzü.

app/interface.py: Komut satırı (CLI) arayüzü.

Çekirdek Katmanı (core/): Etmenlerin sırasını ve veri akışını yöneten Pipeline yapısı.

Etmenler Katmanı (agents/): Her biri özelleşmiş Prompt mühendisliği ile donatılmış sınıflar.

LLM Katmanı: OpenAI (GPT) veya Google (Gemini) modelleriyle entegre yapı.

🛠 Kullanılan Teknolojiler
Dil: Python 3.10+

Yapay Zeka: LangChain, OpenAI API / Google Gemini API

Arayüz: Tkinter (Python yerleşik GUI), Threading (Asenkron işlemler için)

Veri İşleme: Regex, Fuzzy Logic (Levenshtein Distance), JSON Parsing

🚧 Geliştirme Durumu
Proje, temel fonksiyonlarını yerine getiren çalışan bir prototip sürümündedir.

✅ Sistem Mimarisi: Pipeline ve Modüler yapı tamamlandı.

✅ Etmenler: Yazar, Eleştirmen, Editör ve Güvenlik etmenleri aktif.

✅ Güvenlik: Regex, Fuzzy ve LLM tabanlı hibrit filtreleme sistemi eklendi.

✅ Otomatik Düzeltme: Yazım hatalarını ve karakter isimlerini düzelten akıllı modül eklendi.

✅ Arayüz: Hem Terminal hem de Pencereli (GUI) arayüz tamamlandı.

✅ Entegrasyon: Tüm modüller birbirine bağlandı ve test edildi.

👥 Proje Ekibi

Aynur Adıbelli
Erva Nur Bostancı

📄 Lisans
Bu proje eğitim ve araştırma amaçlı geliştirilmiştir.
