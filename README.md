📚 Yapay Hikâye Atölyesi

Üretken Yapay Zekâ ile Çok-Etmenli Hikâye Üretim Sistemi

Yapay Hikâye Atölyesi, üretken yapay zekâ modelleri ve çok-etmenli mimariyi birleştirerek kullanıcı girdilerine göre yaratıcı hikâyeler üreten bir yapıdır. Sistem; Yazar, Eleştirmen ve Editör olmak üzere üç yapay zekâ etmeninin sırayla çalıştığı bir hikâye üretim zinciri hedefler.

Bu repo, projenin temel mimari tasarımını ve geliştirme sürecini içerir.

🎯 Projenin Amacı

Kullanıcı girdilerine dayalı otomatik hikâye üretmek

Yazar → Eleştirmen → Editör sıralı etmen yapısı kurmak

Çok-etmenli yapay zekâ yaklaşımıyla daha tutarlı ve kaliteli metinler üretmek

İnsan yazı ekibine benzer bir üretim sürecini yapay zekâ ile simüle etmek

🧩 Etmen Yapısı (Hedeflenen)

✍️ Yazar Etmen

Kullanıcıdan alınan tür, karakter, tema ve uzunluk bilgilerine göre ilk hikâye taslağını oluşturması hedeflenmektedir.

🧐 Eleştirmen Etmen

Üretilen taslağı analiz ederek geliştirme önerileri ve değerlendirmeler sunması planlanmaktadır.

📝 Editör Etmen

Eleştirmen Etmenin geri bildirimlerini işleyerek geliştirilmiş son metni oluşturması hedeflenmektedir.

Bu etmenlerin her biri, kendi rolüne uygun şekilde GPT tabanlı modellerle çalışacaktır.

🔄 Planlanan Sistem Akışı

Kullanıcı arayüzünden hikâye bilgileri alınır.

Yazar Etmen ilk taslağı üretir.

Eleştirmen Etmen taslağı analiz edip geri bildirim üretir.

Editör Etmen hikâyeyi geliştirir.

Nihai çıktı kullanıcıya sunulur.

🏗 Sistem Mimarisi

Şu an için tamamlanmış tek kısım sistem mimarisidir.
Etmenlerin görev dağılımı, veri akışı ve modüler yapı tasarlanmıştır.

Mimari aşağıdaki bileşenlerden oluşmaktadır:

Kullanıcı Arayüzü (planlandı – henüz yapılmadı)

Etmen Modülleri (tasarlandı – geliştirme aşamasında)

API / Model Katmanı (GPT-4 ve HF modelleri – planlandı)

Veri Akışı (tamamlanan mimari tasarım kapsamında netleştirildi)

Mimari tasarım sayesinde tüm etmenler sırayla ve kontrollü bir şekilde birbirine bağlı çalışacaktır.

🛠 Kullanılacak Teknolojiler

📌 Henüz geliştirme aşamasındadır — ancak planlanan teknoloji yığını:

Amaç	Teknoloji
Üretim & analiz	OpenAI GPT-4, Hugging Face Transformers
Etmen yapısı	LangChain Agents / custom Python classes
Arayüz	Streamlit veya Flask
Dil	Python
Yardımcı modüller	dotenv, json, requests

🚧 Geliştirme Durumu

Bu proje aktif geliştirme aşamasındadır.

✔ Sistem mimarisi ve etmen akış tasarımı hazır

 Yazar Etmen geliştirilme sürecinde.

 Eleştirmen Etmen geliştirilme sürecinde.

❌ Editör Etmen geliştirilmedi

❌ Arayüz oluşturulmadı

❌ Etmenler arası mesaj akışı uygulanmadı

❌ Model testleri yapılmadı

❌ Tam entegrasyon yapılmadı

🎯 Mevcut durum:
Projenin yalnızca teorik ve yapısal tasarımı tamamlanmıştır. Uygulama kodları geliştirilmeye başlanmış ancak tamamlanmamıştır.

👥 Proje Ekibi

Aynur Adıbelli

Erva Nur Bostancı

📄 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.
