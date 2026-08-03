# AlphaFold Güven Skorlarının Blender ile 3B Görselleştirilmesi
## Amacım
Bu projede amacım, AlphaFold'un çalışma mantığını öğrenmek, AlphaFold tarafından üretilen protein yapılarının pLDDT güven skorlarını inceleyerek  Blender 3D ile bu verileri bilimsel açıdan anlamlı 3B görsellere dönüştürmektir. Aynı zamanda bu projeyle yeni öğrenmeye başladığım Python dilini pratik etmek ve biyoinformatik odaklı ilk büyük projemi geliştirmeyi amaçladım.
Proje geliştirme sürecinde Claude gibi yapay zekâ destekli araçlardan kod geliştirme, hata ayıklama ve iyileştirme önerileri almak için yararlandım. Tüm kodlar test edilerek projeye tarafımdan entegre edilmiştir.

## AlphaFold nedir?
AlphaFold aminoasit dizisinden proteinin 3 boyutlu yapısını tahmin eden bir yapay zeka sistemidir. MSA (Çoklu Dizi Hizalaması), anlamına gelir; üç veya daha fazla protein, DNA veya RNA dizisinin aynı anda yan yana getirilip karşılaştırılması işlemidir. Bu yöntem temel olarak evrimsel ilişkileri bulma, ortak özellikleri ortaya çıkarma ve benzerlikleri inceleme amaçlarıyla kullanılır. AlphaFold gücünü MSA verilerinden alır. Yapısı bilinmeyen bir protein dizisi, yapısı laboratuvarda (X-ışını kristalografisi vb.) çözülmüş bilinen proteinlerle MSA ile hizalanır.Benzer diziye sahip bölgelerin, üç boyutlu uzayda da benzer şekilde katlanacağı varsayılarak bilinmeyen proteinin modeli çıkarılır. 

## PLDDT skoru
Model işini bitirdiğinde, kendi yaptığı tahminin doğruluğunu ölçer (pLDDT skoru).
Güven dağılımı:
🟦 Çok yüksek (>90): 206
🟩 Güvenilir (70–90): 27
🟨 Düşük (50–70): 43
🟥 Çok düşük (<50): 117

## Örnek AlphaFold Çıktıları

| Hemoglobin (P69905) | p53 (P04637) | İnsülin (P01308) |
|---|---|---|
| <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/df675e2e-dcd7-4ea4-8cb4-b160a76f4f6b" /> | <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/a840d646-785d-45de-8e3b-0af0b6138067" /> | <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/d2e3b78c-4027-413f-81a4-d76c4e28f12b" />
| ortalama pLDDT: 92.21| ortalama pLDDT: 82.94| ortalama pLDDT: 52.91|
|çok yüksek güven|yüksek güven|düşük güven|

## Proje Çıktıları
| Hemoglobin (P69905) | p53 (P04637) | İnsülin (P01308) |
|---|---|---|
| <img width="1200" height="900" alt="scene_P69905_render_plddt" src="https://github.com/user-attachments/assets/5b6e1fa8-9b06-42e3-a792-95ed22470b2e" /> |<img width="1200" height="900" alt="scene_P04637_render_plddt" src="https://github.com/user-attachments/assets/956ad080-59de-4c87-8b53-1159feb62ab1" /> | <img width="1200" height="900" alt="scene_P01308_render_plddt" src="https://github.com/user-attachments/assets/02c93fcd-73c3-44a9-91f8-ad221981a50f" />

## Kurulum

```bash
git clone <https://github.com/HilalKorkusuz/AlphaFold-G-ven-Skorlar-n-n-Blender-ile-3B-G-rselle-tirilmesi.git>
cd protein-confidence-renderer
pip install -r requirements.txt
```
Ayrıca [Blender](https://www.blender.org/download/) kurulu olmalı (4.x sürümü önerilir).

## Kullanım
 
Sıfırdan başlayan biri için, terminale sırayla yazılması gerekenler:
 
```bash
# 0. Repoyu indir, bağımlılıkları kur
git clone <https://github.com/HilalKorkusuz/AlphaFold-G-ven-Skorlar-n-n-Blender-ile-3B-G-rselle-tirilmesi.git>
cd protein-confidence-renderer/src
pip install -r ../requirements.txt
 
# 1. AlphaFold DB'den bir proteinin PDB dosyasını ve güven verisini indirir
python fetch.py P69905
 
# 2. fetch.py ile indirilen .pdb dosyasından REZİDÜ bazlı pLDDT bilgilerini okur
python parse.py ../data/P69905.pdb
 
# 1 ve 2'yi tek komutla çalıştırmak istersen (ikisini ayrı ayrı yazmana gerek kalmaz)
python run_pipeline.py P69905
 >python run_pipeline.py P69905
=== Adim 1: P69905 icin veri cekiliyor ===
Indirildi: ..\data\P69905.pdb
Ortalama model guveni (pLDDT): 98.06

=== Adim 2: Rezidu bazli pLDDT okunuyor ===
Toplam residu sayisi: 142
Ortalama pLDDT: 98.1
En dusuk: 65.4   En yuksek: 98.9

Dagilim:
  Cok yuksek (>90):  141
  Guvenilir (70-90): 0
  Dusuk (50-70):     1
  Cok dusuk (<50):   0

Ilk 5 residu:
     1 MET  pLDDT=65.4
     2 VAL  pLDDT=91.1
     3 LEU  pLDDT=97.9
     4 SER  pLDDT=98.5
     5 PRO  pLDDT=98.5

# 3. pLDDT'yi Blender'ın okuyacağı bir sahne dosyasına dönüştürür.
python scene.py P69905
 >python scene.py P69905
Sahne dosyasi olusturuldu: ..\data\scene_P69905.json
Toplam rezidu: 142
# 4. Blender'ı arka planda çalıştırıp renklendirilmiş 3B render alır.
Kodu,kendi Blender kurulum yoluna göre düzenle.
"<blender_yolu>/blender.exe" --background --python blender_render.py
 > Blender 4.5\blender.exe" --background --python blender_render.py -- ../data/scene_P69905.json plddt
Blender 4.5.4 LTS (hash b3efe983cc58 built 2025-10-28 14:22:47)
Fra:1 Mem:109.56M (Peak 116.98M) | Time:00:01.39 | Rendering 1 / 64 samples
Fra:1 Mem:109.56M (Peak 116.98M) | Time:00:01.48 | Rendering 25 / 64 samples
Fra:1 Mem:109.56M (Peak 116.98M) | Time:00:01.58 | Rendering 50 / 64 samples
Fra:1 Mem:109.56M (Peak 116.98M) | Time:00:01.63 | Rendering 64 / 64 samples
Saved: ..\data\scene_P69905_render_plddt.png'
Time: 00:01.86 (Saving: 00:00.20)
Render kaydedildi: ..\data\scene_P69905_render_plddt.png
Blender quit
```
 
**Notlar:**
- Windows + Anaconda Prompt kullanıyorsan, `python` yerine `py -3` yazmanız gerekebilir (sistemde birden fazla Python sürümü varsa)
- Çıktı, `data/scene_<UNIPROT_ID>_render_<renk_modu>.png` olarak kaydedilir.

## Kullanılan Teknolojiler

- Python 3
- Biopython
- AlphaFold DB
- UniProt
- RCSB Protein Data Bank
- Blender 4.x
## Geliştirme Araçları

- Anaconda
- Git
- Claude
- ChatGPT
- 
# Kaynakça
- https://www.uniprot.org/
- https://alphafold.ebi.ac.uk/
- https://www.nature.com/articles/s41586-021-03819-2
## Yazar
 
*Hilal Korkusuz- Ytü MBG mezunu- www.linkedin.com/in/hilal-korkusuz-404039237 *
