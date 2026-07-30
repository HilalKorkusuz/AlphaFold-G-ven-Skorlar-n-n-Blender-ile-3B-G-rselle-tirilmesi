"""
Faz 1 - Adim 4: pLDDT skorlarini Blender'in kullanacagi bir "sahne
dosyasina" (scene.json) donusturur.

Renkler, AlphaFold'un resmi pLDDT skalasiyla ayni esikleri kullanir:
    >90   -> mavi   (cok yuksek)
    70-90 -> turkuaz (guvenilir)
    50-70 -> sari   (dusuk)
    <50   -> turuncu (cok dusuk)

Kullanim:
    py -3 scene.py P69905
"""

import json
import sys
from pathlib import Path

from Bio.PDB import PDBParser

from fetch import fetch_alphafold_entry
from parse import load_residue_plddt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# AlphaFold'un resmi renk skalasi (RGB, 0-1 araligi -- Blender materyalleri
# bu araligi bekler)
COLOR_VERY_HIGH = (0.0, 0.325, 0.843)   # mavi
COLOR_CONFIDENT = (0.325, 0.850, 0.843) # turkuaz
COLOR_LOW = (1.0, 0.851, 0.0)           # sari
COLOR_VERY_LOW = (1.0, 0.494, 0.0)      # turuncu


def plddt_to_color(plddt: float) -> tuple[float, float, float]:
    """Bir pLDDT degerini AlphaFold renk skalasindaki RGB uclusune cevirir."""
    if plddt > 90:
        return COLOR_VERY_HIGH
    elif plddt > 70:
        return COLOR_CONFIDENT
    elif plddt > 50:
        return COLOR_LOW
    else:
        return COLOR_VERY_LOW


def load_ca_coordinates(pdb_path: Path) -> dict[int, tuple[float, float, float]]:
    """
    Her rezidunun CA (alfa karbon) atomunun 3B koordinatini okur.

    Blender'in kendi Python ortaminda Biopython kurulu olmayabilir, bu
    yuzden koordinatlari burada (normal Python tarafinda) cikarip
    scene.json'un icine gomuyoruz -- Blender scripti sadece JSON okuyacak,
    baska hicbir kutuphaneye ihtiyac duymayacak.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("model", pdb_path)

    coordinates = {}
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" not in residue:
                    continue
                x, y, z = residue["CA"].get_coord()
                coordinates[residue.id[1]] = (float(x), float(y), float(z))
    return coordinates


def build_scene(uniprot_id: str) -> dict:
    """
    Bir UniProt ID icin veri ceker, rezidu bazli pLDDT okur, her rezidu icin
    renk atar ve Blender'in okuyacagi sozluk yapisini dondurur.
    """
    entry = fetch_alphafold_entry(uniprot_id)
    residue_scores = load_residue_plddt(entry.pdb_path)
    ca_coordinates = load_ca_coordinates(entry.pdb_path)

    residues = []
    for res_no, res_name, plddt in residue_scores:
        residues.append({
            "residue_number": res_no,
            "residue_name": res_name,
            "plddt": plddt,
            "color": list(plddt_to_color(plddt)),
            "position": list(ca_coordinates[res_no]),
        })

    return {
        "uniprot_id": uniprot_id,
        "pdb_path": str(entry.pdb_path),
        "residues": residues,
    }


def main():
    if len(sys.argv) != 2:
        print("Kullanim: py -3 scene.py <UNIPROT_ID>")
        sys.exit(1)

    uniprot_id = sys.argv[1]
    scene = build_scene(uniprot_id)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / f"scene_{uniprot_id}.json"
    with open(output_path, "w") as f:
        json.dump(scene, f, indent=2)

    print(f"Sahne dosyasi olusturuldu: {output_path}")
    print(f"Toplam rezidu: {len(scene['residues'])}")


if __name__ == "__main__":
    main()
