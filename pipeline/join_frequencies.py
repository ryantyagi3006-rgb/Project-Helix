"""
join_frequencies.py
===================
Fills the gnomad_af column that build_serpina1_db.py left blank on purpose.

THE PROBLEM IT SOLVES
---------------------
serpina1_database.csv names variants in cDNA HGVS ('NM_000295.5:c.1096G>A').
gnomad_frequencies.json is keyed by GRCh38 genomic coordinate ('14-94378610-C-T').
Those two strings never match, so build_serpina1_db.py refused to fake the join.

This script does the join honestly, per variant:
  1. HGVS cDNA -> transcript SPDI            (NCBI /hgvs/{h}/contextuals)
  2. transcript SPDI -> genomic SPDI on chr14 (NCBI /spdi/{s}/all_equivalent_contextual)
  3. genomic SPDI -> gnomAD key (chr, pos+1, ref, alt)   (SPDI is 0-based; gnomAD 1-based)
  4. look the key up in the local gnomAD frequency file.

Each variant ends in exactly one of three honest states, never conflated:
  found            : a real gnomAD allele frequency
  absent           : mapped to a valid chr14 coordinate, genuinely not in gnomAD
  unmapped         : NCBI could not resolve the HGVS (kept blank, NOT called absent)

RUN (needs internet to api.ncbi.nlm.nih.gov):
    python3 join_frequencies.py
"""

import csv
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import requests

NCBI_VARIATION = "https://api.ncbi.nlm.nih.gov/variation/v0"
WORKERS = 8                       # parallel NCBI lookups; NCBI tolerates this comfortably
IN_DB = "serpina1_database.csv"
IN_FREQ = "gnomad_frequencies.json"
OUT_DB = "serpina1_database_with_freq.csv"
PROGRESS = "join_progress.log"    # flushed each variant so the run is observable


def parse_variant_name(name):
    """Pull transcript and cDNA out of 'NM_000295.5(SERPINA1):c.1096G>A (p.Glu366Lys)'."""
    transcript = name.split("(")[0].strip() if "(" in name else ""
    cdna = ""
    if ":c." in name:
        cdna = "c." + name.split(":c.")[1].split(" ")[0]
    return transcript, cdna


def genomic_key(transcript, cdna, session, retries=3):
    """
    Map an HGVS cDNA change to a gnomAD 'chr-pos-ref-alt' key, or None if unmappable.
    Two NCBI calls: HGVS->transcript SPDI, then SPDI->all equivalent contextuals,
    from which we pick the NC_000014.* (chr14) genomic placement. Retries on
    transient network errors so a single dropped call is not read as 'unmapped'.
    """
    if not transcript or not cdna:
        return None
    clean = quote(f"{transcript}:{cdna}", safe="")
    for attempt in range(retries):
        try:
            r = session.get(f"{NCBI_VARIATION}/hgvs/{clean}/contextuals", timeout=30)
            r.raise_for_status()
            spdis = r.json().get("data", {}).get("spdis", [])
            if not spdis:
                return None
            s = spdis[0]
            spdi = f"{s['seq_id']}:{s['position']}:{s['deleted_sequence']}:{s['inserted_sequence']}"
            r2 = session.get(f"{NCBI_VARIATION}/spdi/{quote(spdi, safe='')}/all_equivalent_contextual",
                             timeout=30)
            r2.raise_for_status()
            for e in r2.json().get("data", {}).get("spdis", []):
                seq = e.get("seq_id", "")
                if seq.startswith("NC_0000"):
                    chrom = str(int(seq[7:9]))            # NC_000014.9 -> 14
                    pos = e["position"] + 1               # SPDI 0-based -> gnomAD 1-based
                    return f"{chrom}-{pos}-{e['deleted_sequence']}-{e['inserted_sequence']}"
            return None                                   # resolved but no chr14 placement
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                return None                               # NCBI rejects the HGVS: genuinely unmappable
            time.sleep(0.5 * (attempt + 1))               # transient: back off and retry
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


def classify(row, freq, session, done, total, log):
    """Resolve one variant to found / absent / unmapped and record it on the row."""
    transcript, cdna = parse_variant_name(row["variant_name"])
    key = genomic_key(transcript, cdna, session)
    if key is None:
        row["gnomad_af"], row["freq_status"], row["gnomad_key"] = "", "unmapped", ""
    elif key in freq and freq[key] is not None:
        row["gnomad_af"], row["freq_status"], row["gnomad_key"] = f"{freq[key]:.6g}", "found", key
    else:
        row["gnomad_af"], row["freq_status"], row["gnomad_key"] = "0", "absent", key
    done[0] += 1
    log.write(f"[{done[0]}/{total}] {row['freq_status']:9} {row['variant_name'][:46]}\n")
    log.flush()
    return row


def main():
    freq = json.load(open(IN_FREQ))
    rows = list(csv.DictReader(open(IN_DB)))
    session = requests.Session()

    cols = list(rows[0].keys())
    if "freq_status" not in cols:
        cols.insert(cols.index("gnomad_af") + 1, "freq_status")
        cols.insert(cols.index("freq_status") + 1, "gnomad_key")

    total = len(rows)
    done = [0]
    with open(PROGRESS, "w") as log:
        log.write(f"[start] joining {total} variants with {WORKERS} workers\n")
        log.flush()
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            list(ex.map(lambda r: classify(r, freq, session, done, total, log), rows))

        found = sum(1 for r in rows if r["freq_status"] == "found")
        absent = sum(1 for r in rows if r["freq_status"] == "absent")
        unmapped = sum(1 for r in rows if r["freq_status"] == "unmapped")
        with open(OUT_DB, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        summary = (f"[done] wrote {OUT_DB}\n"
                   f"[coverage] found={found} absent={absent} unmapped={unmapped} total={total}\n")
        log.write(summary)
        log.flush()
    sys.stdout.write(summary)


if __name__ == "__main__":
    main()
