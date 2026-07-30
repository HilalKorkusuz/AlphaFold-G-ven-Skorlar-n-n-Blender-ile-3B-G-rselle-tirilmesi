"""
Faz 0: AlphaFold DB'den yapı (PDB) ve rezidü bazlı pLDDT/PAE verisini indirir.

Kullanım:
    python fetch.py P69905
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass

import requests

ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class AlphaFoldEntry:
    """Tek bir AlphaFold tahminine ait dosya yolları ve metadata."""
    uniprot_id: str
    pdb_path: Path
    pae_path: Path | None
    model_confidence: float | None  # ortalama pLDDT


def _fetch_metadata(uniprot_id: str) -> dict:
    """AlphaFold API'sinden tahmine ait metadata'yı çeker (PDB ve PAE URL'leri dahil)."""
    url = ALPHAFOLD_API.format(uniprot_id=uniprot_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"'{uniprot_id}' için AlphaFold tahmini bulunamadı.")

    # API bir liste döner (izoformlar için); ilk/en güncel modeli alıyoruz
    return results[0]


def _download_file(url: str, destination: Path) -> Path:
    """Verilen URL'deki dosyayı destination yoluna indirir."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def fetch_alphafold_entry(uniprot_id: str, output_dir: Path = DATA_DIR) -> AlphaFoldEntry:
    """
    Bir UniProt ID için AlphaFold yapı tahminini ve güven verisini indirir.

    Adım 1 (pipeline diyagramındaki 'Veri çekme') bu fonksiyonla karşılanır.
    Adım 2'de (pLDDT ayrıştırma) bu PDB dosyası parse edilecek.
    """
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


def main():
    if len(sys.argv) != 2:
        print("Kullanım: python fetch.py <UNIPROT_ID>")
        sys.exit(1)

    uniprot_id = sys.argv[1]
    entry = fetch_alphafold_entry(uniprot_id)

    print(f"İndirildi: {entry.pdb_path}")
    print(f"Ortalama model güveni (pLDDT): {entry.model_confidence}")
    if entry.pae_path:
        print(f"PAE verisi: {entry.pae_path}")


if __name__ == "__main__":
    main()
