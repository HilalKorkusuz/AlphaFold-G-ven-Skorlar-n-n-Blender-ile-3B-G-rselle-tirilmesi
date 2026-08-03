"""

Kodun işlevi:
AlphaFold tahminini, RCSB'den indirilen deneysel bir PDB yapısıyla karşılaştırır ve iki yapı arasındaki farkı (RMSD) hesaplar.

Kullanim:
    python align.py P69905 2HHB B
    (son parametre: deneysel yapida hangi zinciri kullanacagimiz.Hemoglobin gibi cok-zincirli proteinlerde bunu belirtmek gerekir)
"""

import json
import sys
from pathlib import Path

import requests
from Bio.PDB import PDBParser, Superimposer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"


def download_experimental_structure(pdb_id: str, output_dir: Path = DATA_DIR) -> Path:
    # RCSB PDB'den deneysel bir yapiyi indirir.
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{pdb_id}_experimental.pdb" #experimental" eki: aynı UniProt ID'yle karışmasın diye

    url = RCSB_DOWNLOAD_URL.format(pdb_id=pdb_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    destination.write_bytes(response.content)

    return destination


def get_ca_residues(pdb_path: Path, chain_id: str) -> dict[int, tuple["Atom", str]]:
    """
    Bir PDB dosyasindaki belirli bir zincirin CA atomlarini VE aminoasit isimlerini, rezidu numarasina gore bir sozlukte toplar.
    Isim bilgisini de tutuyoruz cunku sadece numaraya guvenmek riskli. Bazi deneysel yapilarda ilk Metionin kesilmis olabilir, bu da tum numaralandirmayi kaydirir (asagidaki find_best_offset bunu duzeltir).
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("model", pdb_path)

    residues = {}
    for model in structure:
        for chain in model:
            if chain.id != chain_id:
                continue
            for residue in chain:
                if "CA" not in residue:
                    continue
                residues[residue.id[1]] = (residue["CA"], residue.resname)
        break # sadece ilk modeli kullan (deneysel yapılarda genelde tek model olur)

    return residues

 #3 harfli aminoasit kodunu (PDB dosyalarının kullandığı, örn. "MET") 1 harfli koda (örn. "M") çeviren kod.
THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def match_residues_by_sequence(
    predicted: dict[int, tuple["Atom", str]],
    experimental: dict[int, tuple["Atom", str]],
) -> list[tuple[int, int]]:
    """
    Iki rezidu kumesini, GERCEK bir dizi hizalamasi (sequence alignment) kullanarak eslestirir. Sabit bir kaymadan (offset) farkli olarak, bu yontem BOSLUKLARA izin verir -- deneysel yapilarda sik gorulen "bu bolge kristalde gorunmuyor" durumunu dogru sekilde atlar.
    """
    from Bio.Align import PairwiseAligner

    pred_seq = "".join(THREE_TO_ONE.get(predicted[i][1], "X") for i in pred_ids)  # "X": bilinmeyen/standart olmayan aminoasit
    exp_seq = "".join(THREE_TO_ONE.get(experimental[i][1], "X") for i in exp_ids)
 
    aligner = PairwiseAligner()
    aligner.mode = "global"           # dizinin BAŞTAN SONA tamamını hizala (sadece en benzer parçayı değil)
    aligner.match_score = 2           # aynı aminoasit eşleşirse puan ver
    aligner.mismatch_score = -1       # farklı aminoasit eşleşirse puan kır
    aligner.open_gap_score = -5       # yeni bir boşluk açmak pahalı (gereksiz yere boşluk açmasın diye)
    aligner.extend_gap_score = -0.5   # mevcut bir boşluğu uzatmak daha ucuz (bir kez boşluk açtıysa devam etmesi mantıklı)
 
    alignment = aligner.align(pred_seq, exp_seq)[0]  # en iyi skorlu hizalamayı al
    pred_aligned, exp_aligned = alignment.aligned
 
    # 'aligned', boşluksuz eşleşen BLOK aralıklarını (başlangıç, bitiş) verir --
    # bunları tek tek residü çiftlerine açıyoruz
    pairs = []
    for (p_start, p_end), (e_start, e_end) in zip(pred_aligned, exp_aligned):
        for p_offset, e_offset in zip(range(p_start, p_end), range(e_start, e_end)):
            pairs.append((pred_ids[p_offset], exp_ids[e_offset]))
 
    return pairs


def align_structures(
    predicted_pdb: Path,
    experimental_pdb: Path,
    predicted_chain: str = "A",
    experimental_chain: str = "A",
) -> dict:
    # İki yapıyı hizalar, global RMSD ve residü bazlı sapmayı hesaplar. Bu dosyanın ANA fonksiyonu.
    predicted_residues = get_ca_residues(predicted_pdb, predicted_chain)
    experimental_residues = get_ca_residues(experimental_pdb, experimental_chain)

    residue_pairs = match_residues_by_sequence(predicted_residues, experimental_residues)
    print(f"Dizi hizalamasiyla {len(residue_pairs)} rezidu ciftinin dogru eslestigi tespit edildi.")

    if len(residue_pairs) < 3:
        raise ValueError(
            f"Ortak rezidu sayisi cok az ({len(residue_pairs)}). "
            "Zincir ID'lerini kontrol et."
        )

    common_residue_ids = [pred_id for pred_id, _ in residue_pairs]
    predicted_list = [predicted_residues[pred_id][0] for pred_id, _ in residue_pairs]
    experimental_list = [experimental_residues[exp_id][0] for _, exp_id in residue_pairs]

    # Superimposer: predicted_list'i experimental_list'e en iyi oturacak
    # sekilde donduren/oteleyen donusumu bulur
    superimposer = Superimposer()
    superimposer.set_atoms(experimental_list, predicted_list)
    superimposer.apply(predicted_list)  # predicted atomlarin koordinatlarini gunceller

    global_rmsd = superimposer.rms

    # hizalama SONRASI, her rezidunun deneysel karsiligina ne kadar
    # uzak kaldigini (lokal sapma) hesapla
    per_residue_deviation = {}
    for res_id, pred_atom, exp_atom in zip(common_residue_ids, predicted_list, experimental_list):
        distance = (pred_atom.get_coord() - exp_atom.get_coord())
        per_residue_deviation[res_id] = float((distance ** 2).sum() ** 0.5)

    return {
        "global_rmsd": float(global_rmsd),
        "total_predicted_residues": len(predicted_residues),
        "total_experimental_residues": len(experimental_residues),
        "common_residue_count": len(common_residue_ids),
        "per_residue_deviation": per_residue_deviation,
    }


def main():
    if len(sys.argv) not in (3, 4):
        print("Kullanim: py -3 align.py <UNIPROT_ID> <PDB_ID> [DENEYSEL_ZINCIR]")
        print("Ornek:    py -3 align.py P69905 2HHB B")
        sys.exit(1)

    uniprot_id = sys.argv[1]
    pdb_id = sys.argv[2]
    experimental_chain = sys.argv[3] if len(sys.argv) == 4 else "A"

    predicted_pdb = DATA_DIR / f"{uniprot_id}.pdb"
    if not predicted_pdb.exists():
        print(f"HATA: {predicted_pdb} bulunamadi. Once fetch.py/run_pipeline.py calistir.")
        sys.exit(1)

    print(f"=== {pdb_id} deneysel yapisi indiriliyor ===")
    experimental_pdb = download_experimental_structure(pdb_id)
    print(f"Indirildi: {experimental_pdb}")

    print(f"\n=== Hizalama yapiliyor ===")
    result = align_structures(
        predicted_pdb, experimental_pdb,
        predicted_chain="A", experimental_chain=experimental_chain,
    )

    print(f"Tahmin edilen yapida toplam rezidu: {result['total_predicted_residues']}")
    print(f"Deneysel yapida toplam rezidu: {result['total_experimental_residues']}")
    print(f"Ortak rezidu sayisi: {result['common_residue_count']}")
    print(f"Global RMSD: {result['global_rmsd']:.2f} Angstrom")

    output_path = DATA_DIR / f"alignment_{uniprot_id}_{pdb_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSonuc kaydedildi: {output_path}")
    # Bu dosya, scene.py'ye ikinci parametre olarak verilip renk katmanına dönüştürülüyor

if __name__ == "__main__":
    main()
