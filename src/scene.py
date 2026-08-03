"""
Kodun işlevi:
pLDDT skorlarını (ve varsa align.py'nin ürettiği RMSD sapma verisini) Blender'ın kullanacağı bir "sahne dosyasına" (scene.json) dönüştürür.
 
Renkler, AlphaFold'un resmi pLDDT skalasıyla aynı eşikleri kullanır:
    >90   -> mavi   (çok yüksek)
    70-90 -> turkuaz (güvenilir)
    50-70 -> sarı   (düşük)
    <50   -> turuncu (çok düşük)
 
Kullanım:
    python scene.py P69905
    python scene.py P69905 ../data/alignment_P69905_2HHB.json   (RMSD katmanı dahil)
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

# Rezidu bazli SAPMA (deviation) icin ayrı bir renk skalasi -- pLDDT
# renkleriyle karistirmamak icin yesil-sari-turuncu-kirmizi kullaniyoruz.
# Deger Angstrom cinsinden: dusuk = tahmin ve deney cok yakin, yuksek = fark var
DEVIATION_MATCH = (0.15, 0.75, 0.15)     # yesil   (<1 A,  cok yakin)
DEVIATION_CLOSE = (0.85, 0.85, 0.15)     # sari    (1-2 A, yakin)
DEVIATION_MODERATE = (0.9, 0.5, 0.1)     # turuncu (2-4 A, orta fark)
DEVIATION_HIGH = (0.8, 0.1, 0.1)         # kirmizi (>4 A,  buyuk fark)
DEVIATION_NO_DATA = (0.4, 0.4, 0.4)      # gri     (deneysel karsiligi yok)


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


def deviation_to_color(deviation: float | None) -> tuple[float, float, float]:
    """Bir rezidunun (Angstrom cinsinden) sapma degerini RGB rengine cevirir."""
    if deviation is None:
        return DEVIATION_NO_DATA
    elif deviation < 1:
        return DEVIATION_MATCH
    elif deviation < 2:
        return DEVIATION_CLOSE
    elif deviation < 4:
        return DEVIATION_MODERATE
    else:
        return DEVIATION_HIGH


def load_alignment(alignment_path: Path) -> dict:
    """align.py'nin urettigi alignment_*.json dosyasini okur."""
    with open(alignment_path) as f:
        return json.load(f)


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


def build_scene(uniprot_id: str, alignment_path: Path | None = None) -> dict:
    """
    Bir UniProt ID icin veri ceker, rezidu bazli pLDDT okur, her rezidu icin
    renk atar ve Blender'in okuyacagi sozluk yapisini dondurur.

    alignment_path verilirse, align.py'nin uretti sapma verisi de
    her rezidunun "deviation" ve "deviation_color" alanlarina eklenir --
    bu, Blender'da ikinci bir renklendirme secenegi olarak kullanilabilir.
    """
    entry = fetch_alphafold_entry(uniprot_id)
    residue_scores = load_residue_plddt(entry.pdb_path)
    ca_coordinates = load_ca_coordinates(entry.pdb_path)

    per_residue_deviation = {}
    global_rmsd = None
    if alignment_path is not None:
        alignment = load_alignment(alignment_path)
        # JSON anahtarlari string olarak gelir, int'e ceviriyoruz
        per_residue_deviation = {
            int(k): v for k, v in alignment["per_residue_deviation"].items()
        }
        global_rmsd = alignment["global_rmsd"]

    residues = []
    for res_no, res_name, plddt in residue_scores:
        deviation = per_residue_deviation.get(res_no)
        residues.append({
            "residue_number": res_no,
            "residue_name": res_name,
            "plddt": plddt,
            "color": list(plddt_to_color(plddt)),
            "position": list(ca_coordinates[res_no]),
            "deviation": deviation,
            "deviation_color": list(deviation_to_color(deviation)),
        })

    return {
        "uniprot_id": uniprot_id,
        "pdb_path": str(entry.pdb_path),
        "global_rmsd": global_rmsd,
        "residues": residues,
    }


def main():
    if len(sys.argv) not in (2, 3):
        print("Kullanim: py -3 scene.py <UNIPROT_ID> [alignment_dosyasi.json]")
        print("Ornek:    py -3 scene.py P69905 ../data/alignment_P69905_2HHB.json")
        sys.exit(1)

    uniprot_id = sys.argv[1]
    alignment_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    scene = build_scene(uniprot_id, alignment_path)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / f"scene_{uniprot_id}.json"
    with open(output_path, "w") as f:
        json.dump(scene, f, indent=2)

    print(f"Sahne dosyasi olusturuldu: {output_path}")
    print(f"Toplam rezidu: {len(scene['residues'])}")
    if scene["global_rmsd"] is not None:
        print(f"Global RMSD (sahneye gomuldu): {scene['global_rmsd']:.2f} Angstrom")


if __name__ == "__main__":
    main()
