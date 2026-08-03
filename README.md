# AlphaFold Güven Skorlarının Blender ile 3B Görselleştirilmesi
## Amacım
** AlphaFold u öğrenmek ve yeni öğrenmeye başladığıkm pyhton dilini kullanarak Cloude yardımıyla kod oluşturmak ve terminal(anaconda) sistemini kullanarak kodumu çalıştırmak. Ardından hobim olan Blender3d yardımıyla görsel sonuç elde etmek.
## AlphaFold nedir?
AlphaFold aminoasit dizisinden proteinin 3 boyutlu yapısını tahmin eden bir yapay zeka sistemidir. 
Uniport (protein dizileri ve açıklamalarının standart deposu) ise AlphaFold'un tahminlerini içeren (200 milyonu aşan tahmin) veritabanıdır. 
MSA (Çoklu Dizi Hizalaması), anlamına gelir; üç veya daha fazla protein, DNA veya RNA dizisinin aynı anda yan yana getirilip karşılaştırılması işlemidir. Bu yöntem temel olarak evrimsel ilişkileri bulma, ortak özellikleri ortaya çıkarma ve benzerlikleri inceleme amaçlarıyla kullanılır. AlphaFold gücünü MSA verilerinden alır. Yapısı bilinmeyen bir protein dizisi, yapısı laboratuvarda (X-ışını kristalografisi vb.) çözülmüş bilinen proteinlerle MSA ile hizalanır.Benzer diziye sahip bölgelerin, üç boyutlu uzayda da benzer şekilde katlanacağı varsayılarak bilinmeyen proteinin modeli çıkarılır. 
Model işini bitirdiğinde, kendi yaptığı tahminin doğruluğunu ölçer (pLDDT skoru).

## Örnek AlphaFold Çıktılar
 
| Hemoglobin (P69905) | p53 (P04637) | İnsülin (P01308) |
|---|---|---|
| <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/df675e2e-dcd7-4ea4-8cb4-b160a76f4f6b" /> | <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/a840d646-785d-45de-8e3b-0af0b6138067" /> | <img width="550" height="385" alt="image" src="https://github.com/user-attachments/assets/d2e3b78c-4027-413f-81a4-d76c4e28f12b" />
| ortalama pLDDT: 92.21| ortalama pLDDT: 82.94| ortalama pLDDT: 52.91|
|çok yüksek güven|yüksek güven|düşük güven|

## Proje Çıktıları
| Hemoglobin (P69905) | p53 (P04637) | İnsülin (P01308) |
|---|---|---|
| <img width="1200" height="900" alt="scene_P69905_render_plddt" src="https://github.com/user-attachments/assets/a90835c7-0e25-49cb-88ed-68b43638f380" /> | <img  width="1200" height="900" alt="scene_P04637_render_plddt" src="https://github.com/user-attachments/assets/5180a280-b124-4c87-9eb9-5fc34b4f2119" /> | <img width="1200" height="900" alt="scene_P01308_render_plddt" src="https://github.com/user-attachments/assets/d941ff0c-9daf-4014-808f-8e83fa757658" />
| ortalama pLDDT: 92.21| ortalama pLDDT: 82.94| ortalama pLDDT: 52.91|
|çok yüksek güven|yüksek güven|düşük güven|

##İsteğe bağlı kısım


## Kurulum
 
```bash
git clone <repo-url>
cd protein-confidence-renderer
pip install -r requirements.txt
```
Ayrıca [Blender](https://www.blender.org/download/) kurulu olmalı (4.x sürümü önerilir).

## Kullanım
 
Sıfırdan başlayan biri için, terminale sırayla yazılması gerekenler:
 
```bash
# 0. Repoyu indir, bağımlılıkları kur
git clone <repo-url>
cd protein-confidence-renderer/src
pip install -r ../requirements.txt
 
# 1. AlphaFold DB'den bir proteinin PDB dosyasını ve güven verisini indirir
python fetch.py P69905
 
# 2. fetch.py ile indirilen .pdb dosyasından REZİDÜ bazlı pLDDT bilgilerini okur
python parse.py ../data/P69905.pdb
 
# 1 ve 2'yi tek komutla çalıştırmak istersen (ikisini ayrı ayrı yazmana gerek kalmaz)
python run_pipeline.py P69905
 
# 3. pLDDT'yi Blender'ın okuyacağı bir sahne dosyasına dönüştürür.
python scene.py P69905
 
# 4. Blender'ı arka planda çalıştırıp renklendirilmiş 3B render alır.
Kodu,kendi Blender kurulum yoluna göre düzenle.
"<blender_yolu>/blender.exe" --background --python blender_render.py 
```
 
**Notlar:**
- Windows + Anaconda Prompt kullanıyorsan, `python` yerine `py -3` yazmanız gerekebilir (sistemde birden fazla Python sürümü varsa)
- Çıktı, `data/scene_<UNIPROT_ID>_render_<renk_modu>.png` olarak kaydedilir.

## Kullanılan Teknolojiler
- **Python** — pipeline'ın omurgası
- **Biopython** — PDB dosyalarını okuma, rezidü/atom düzeyinde veri çıkarma, `Superimposer` ile yapısal hizalama, `PairwiseAligner` ile dizi hizalama
- **AlphaFold DB API** — yapı tahminlerine ve güven verisine erişim
- **RCSB PDB API** — deneysel referans yapılarına erişim
- **Blender (bpy)** — headless, script-tabanlı 3B sahne kurulumu ve render alma
- **Claude** - kod yazma ve konuyu anlatma konusunda kullandım

# Kaynakça
https://www.uniprot.org/
https://alphafold.ebi.ac.uk/
https://www.nature.com/articles/s41586-021-03819-2
## Yazar
 
*Hilal Korkusuz- Ytü MBG mezunu- www.linkedin.com/in/hilal-korkusuz-404039237 *
