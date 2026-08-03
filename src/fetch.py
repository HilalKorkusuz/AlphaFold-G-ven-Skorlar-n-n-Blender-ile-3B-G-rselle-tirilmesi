"""
Kodun işlevi:
AlphaFold verisetinden proteinin PDB yapısını ve rezidü bazlı pLDDT/PAE verisini indirir.

Kullanım:
    python fetch.py P69905
"""

import sys
from pathlib import Path
from dataclasses import dataclass

import requests

ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}" #uniport_id bölümüne istediğimiz proteinin ID'si gelecek. bknz: SATIR 30
DATA_DIR = Path(__file__).resolve().parent.parent / "data" # indirilen dosyalarının kaydedileceği yer.


@dataclass
class AlphaFoldEntry:
    uniprot_id: str
    pdb_path: Path
    pae_path: Path | None # opsiyonel,bazi tahminlerde PAE verisi olmayabilir.
    model_confidence: float | None  # ortalama pLDDT
    # class içinde 4 farklı bilgi saklıyor.


def _fetch_metadata(uniprot_id: str) -> dict:  #AlphaFold API'sinden, bu tahmine dair METADATA'yi ceker. Metadata Kendisi protein yapısı değil — "gerçek dosya şurada, güven skoru şu" diyen bir rehber/etiket.
    #bu fonksiyonun bir amacı da olası hataları tespit edip kullanıcıya haber vermek.
    url = ALPHAFOLD_API.format(uniprot_id=uniprot_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"'{uniprot_id}' için AlphaFold tahmini bulunamadı.")
    return results[0]
#bu fonksiyonun bir amacı da olası hataları tespit edip kullanıcıya haber vermek.

def _download_file(url: str, destination: Path) -> Path: # Verilen URL'deki HAM DOSYAYI (gercek .pdb/.json icerigi) indirilir.
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content) # write_bytes: dosyayi METIN olarak degil, HAM BAYT olarak yazilir. PDB dosyalari metin tabanli olsa da response.content zaten bayt formatinda geldigi icin bu en güveli yoldur.
    return destination

def fetch_alphafold_entry(uniprot_id: str, output_dir: Path = DATA_DIR) -> AlphaFoldEntry: # BU DOSYANIN "ANA" / DISARIYA ACIK FONKSIYONU.Bir UniProt ID için AlphaFold yapı tahminini ve güven verisini indirir.

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = _fetch_metadata(uniprot_id)

    pdb_url = metadata["pdbUrl"]
    pdb_path = output_dir / f"{uniprot_id}.pdb"
    _download_file(pdb_url, pdb_path)

    pae_path = None
    if pae_url := metadata.get("paeImageUrl") or metadata.get("paeDocUrl"):
        pae_path = output_dir / f"{uniprot_id}_pae.json"
        _download_file(pae_url, pae_path)

    return AlphaFoldEntry(
        uniprot_id=uniprot_id,
        pdb_path=pdb_path,
        pae_path=pae_path,
        model_confidence=metadata.get("globalMetricValue"),
    )


def main(): # TERMINALDEN DOGRUDAN calistirildiginda devreye giren kisim
    if len(sys.argv) != 2:
        print("Kullanım: python fetch.py <UNIPROT_ID>")
        sys.exit(1)

    uniprot_id = sys.argv[1]
    entry = fetch_alphafold_entry(uniprot_id)

    print(f"İndirildi: {entry.pdb_path}")
    print(f"Ortalama model güveni (pLDDT): {entry.model_confidence}")
    if entry.pae_path:
        print(f"PAE verisi: {entry.pae_path}")
    #Burası ekranda görülecek bilgilerin yazdırıldığı kısım


if __name__ == "__main__":
    main()
