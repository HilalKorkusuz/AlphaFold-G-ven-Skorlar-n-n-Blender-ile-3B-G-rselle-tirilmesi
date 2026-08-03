"""
Kodun işlevi:
fetch.py + parse.py adımlarını tek komutla sırayla çalıştıran birleştirici script.

Kullanim:
    python run_pipeline.py P69905
"""

import sys
from pathlib import Path

from fetch import fetch_alphafold_entry
from parse import load_residue_plddt, summarize


def run(uniprot_id: str) -> None:  # Bu dosya kendi başına bir analiz YAPMIYOR. Sadece fetch.py ve parse.py'deki hazır fonksiyonları import edip sırayla çağırıyor.
    print(f"=== Adim 1: {uniprot_id} icin veri cekiliyor ===")
    entry = fetch_alphafold_entry(uniprot_id)
    print(f"Indirildi: {entry.pdb_path}")
    print(f"Ortalama model guveni (pLDDT): {entry.model_confidence}")

    print(f"\n=== Adim 2: Rezidu bazli pLDDT okunuyor ===")
    residue_scores = load_residue_plddt(entry.pdb_path)
    summarize(residue_scores)
    #çıktı olarak terminalde görülecek kısım


def main():
    if len(sys.argv) != 2:
        print("Kullanim: py -3 run_pipeline.py <UNIPROT_ID>")
        sys.exit(1)

    run(sys.argv[1])


if __name__ == "__main__":
    main()
