"""
Kodun işlevi:
fetch.py ile indirilen .pdb dosyasından REZİDÜ bazlı pLDDT (güven skoru) okur.
AlphaFold, pLDDT skorunu PDB dosyasının B-factor alanına yazar. Aynı residüdeki tüm atomlar aynı pLDDT değerine sahip olduğu için, her residünün CA (alfa karbon) atomundaki B-factor'u okumak yeterli.

Kullanim:
    python parse.py P69905.pdb
"""

import sys
from pathlib import Path

from Bio.PDB import PDBParser


def load_residue_plddt(pdb_path: Path) -> list[tuple[int, str, float]]:
    # Bir PDB dosyasini acar, her residu icin (residu_no, aminoasit_adi, pLDDT) ucluleri dondurur.

    parser = PDBParser(QUIET=True) # QUIET=True: bozuk/eksik PDB satırlarında konsolu uyarı mesajlarıyla doldurmasın
    structure = parser.get_structure("model", pdb_path) # model, Biopython'un istediği bir isim etiketi
 
    residue_scores = []
    for model in structure: # PDB dosyaları birden fazla model içerebilir (NMR yapılarında olur), biz genelde tek model bekliyoruz
        for chain in model:  # bir model, birden fazla zincirden oluşabilir (örn. hemoglobin: A, B, C, D)
            for residue in chain:  # bir zincir, sırayla dizilmiş residülerden (aminoasitlerden) oluşur
                if "CA" not in residue:  # su molekülü, ligand gibi standart olmayan kalıntıları atla-- bunların CA (alfa karbon) atomu yok
                    continue
                ca_atom = residue["CA"]
                residue_scores.append(
                    (residue.id[1], residue.resname, ca_atom.get_bfactor())
                    # residue.id[1] = residü numarası, 
                    # residue.resname = aminoasit adı (örn. "MET"), 
                    # get_bfactor() = pLDDT değeri
                )
    return residue_scores


def summarize(residue_scores: list[tuple[int, str, float]]) -> None: # residue_scores listesini alıp ortalama/min/max/dağılım özetini ekrana yazdırır.
    if not residue_scores:
        print("Hicbir residu bulunamadi.")
        return

    scores = [s for _, _, s in residue_scores] # listedeki her üçlüden sadece pLDDT değerini (3. eleman) ayıklıyor
    print(f"Toplam residu sayisi: {len(scores)}")
    print(f"Ortalama pLDDT: {sum(scores) / len(scores):.1f}")
    print(f"En dusuk: {min(scores):.1f}   En yuksek: {max(scores):.1f}")

    # AlphaFold'un resmi pLDDT eşiklerine göre kaç residü hangi kategoride, onu sayıyoruz
    very_high = sum(1 for s in scores if s > 90)
    confident = sum(1 for s in scores if 70 < s <= 90)
    low = sum(1 for s in scores if 50 < s <= 70)
    very_low = sum(1 for s in scores if s <= 50)

    print("\nDagilim:")
    print(f"  Cok yuksek (>90):  {very_high}")
    print(f"  Guvenilir (70-90): {confident}")
    print(f"  Dusuk (50-70):     {low}")
    print(f"  Cok dusuk (<50):   {very_low}")

    print("\nIlk 5 residu:")
    for res_no, res_name, score in residue_scores[:5]:
        print(f"  {res_no:>4} {res_name:>3}  pLDDT={score:.1f}")


def main(): # TERMINALDEN DOGRUDAN calistirildiginda devreye giren kisim
    if len(sys.argv) != 2:
        print("Kullanim: python parse.py <indirilen_dosya.pdb>")
        sys.exit(1)

    pdb_path = Path(sys.argv[1])
    residue_scores = load_residue_plddt(pdb_path)
    summarize(residue_scores)
    # Burası ekranda görülecek özet bilgilerin yazdırıldığı kısım.
if __name__ == "__main__":
    main()
