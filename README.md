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
| <img width="557" height="387" alt="image" src="https://github.com/user-attachments/assets/df675e2e-dcd7-4ea4-8cb4-b160a76f4f6b" /> | <img width="622" height="382" alt="image" src="https://github.com/user-attachments/assets/a840d646-785d-45de-8e3b-0af0b6138067" /> | <img width="607" height="392" alt="image" src="https://github.com/user-attachments/assets/d2e3b78c-4027-413f-81a4-d76c4e28f12b" />
| average pLDDT: 92.21| average pLDDT: 82.94| average pLDDT: 52.91|
|çok yüksek güven|yüksek güven|düşük güven|

# Kaynakça
https://www.uniprot.org/
https://alphafold.ebi.ac.uk/
https://www.nature.com/articles/s41586-021-03819-2
