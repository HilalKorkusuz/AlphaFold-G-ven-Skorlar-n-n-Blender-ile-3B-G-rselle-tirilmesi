"""
Faz 0 - Adim 2: fetch.py ile indirilen .pdb dosyasindan REZIDU bazli
pLDDT okuma.

AlphaFold DB'nin PDB dosyalarinda pLDDT skoru, B-factor alanina yazilir.
Ayni residudeki tum atomlar ayni pLDDT degerine sahip oldugu icin,
her residunun CA (alfa karbon) atomundaki B-factor'u okumak yeterli.

Kullanim:
    python parse.py P69905.pdb
"""

import sys
from pathlib import Path

from Bio.PDB import PDBParser


def load_residue_plddt(pdb_path: Path) -> list[tuple[int, str, float]]:
    """
    Bir PDB dosyasini acar, her residu icin (residu_no, aminoasit_adi, pLDDT)
    ucluleri dondurur.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("model", pdb_path)

    residue_scores = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" not in residue:
                    # su molekulu, ligand gibi standart olmayan kalintilari atla
                    continue
                ca_atom = residue["CA"]
                residue_scores.append(
                    (residue.id[1], residue.resname, ca_atom.get_bfactor())
                )
    return residue_scores


def summarize(residue_scores: list[tuple[int, str, float]]) -> None:
    if not residue_scores:
        print("Hicbir residu bulunamadi.")
        return

    scores = [s for _, _, s in residue_scores]
    print(f"Toplam residu sayisi: {len(scores)}")
    print(f"Ortalama pLDDT: {sum(scores) / len(scores):.1f}")
    print(f"En dusuk: {min(scores):.1f}   En yuksek: {max(scores):.1f}")

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


def main():
    if len(sys.argv) != 2:
        print("Kullanim: python parse.py <indirilen_dosya.pdb>")
        sys.exit(1)

    pdb_path = Path(sys.argv[1])
    residue_scores = load_residue_plddt(pdb_path)
    summarize(residue_scores)


if __name__ == "__main__":
    main()
