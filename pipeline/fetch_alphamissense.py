"""
fetch_alphamissense.py
======================
Adds the in-silico axis the retired VUS-lean estimator was missing.

WHAT IT DOES
------------
For each SERPINA1 variant it asks the Ensembl VEP REST API for the AlphaMissense
prediction (am_pathogenicity 0..1 and am_class: likely_benign / ambiguous /
likely_pathogenic). AlphaMissense is a missense-only predictor, so synonymous,
intronic, nonsense and structural variants correctly get no score.

It then derives the ClinGen-style in-silico ACMG code:
  am_class likely_pathogenic  -> PP3  (in-silico pathogenic)
  am_class likely_benign      -> BP4  (in-silico benign)
  am_class ambiguous / none   -> no call (honest middle band)

and combines that with the frequency code already on each row into a PROVISIONAL
lean, using the same benign-vs-pathogenic tally the estimator used:
  benign points : BA1, BS1, BP4
  path points   : PM2_Supporting, PP3
  both -> Conflicting signals ; benign only -> Lean benign ;
  path only -> Lean pathogenic ; none -> No information

Every lean stays PROVISIONAL. Judgment codes (PS3, PP1, PM3, BS4, PS4, functional
and segregation evidence) are human-only and are never assessed here.

RUN (needs internet to rest.ensembl.org):
    python3 fetch_alphamissense.py
"""

import csv
import re
import json
import time
import requests

IN_DB = "serpina1_database_with_freq.csv"
OUT_DB = "serpina1_database_scored.csv"
VEP = "https://rest.ensembl.org/vep/human/hgvs"
BATCH = 150


def clean_hgvs(name):
    """Return 'NM_000295.5:c.1096G>A' from the full ClinVar title, or None."""
    if "(" not in name or ":c." not in name:
        return None
    transcript = name.split("(")[0].strip()
    cdna = "c." + name.split(":c.")[1].split(" ")[0]
    return f"{transcript}:{cdna}"


def am_for_result(res):
    """Pull one AlphaMissense call from a VEP result's missense consequences."""
    best = None
    for tc in res.get("transcript_consequences", []):
        if "missense_variant" not in (tc.get("consequence_terms") or []):
            continue
        am = tc.get("alphamissense")
        if am and am.get("am_pathogenicity") is not None:
            # AM is protein-level and consistent across transcripts; take the first.
            best = (am.get("am_pathogenicity"), am.get("am_class", ""))
            break
    return best


def insilico_code(am_class):
    if am_class == "likely_pathogenic":
        return ("PP3", "path")
    if am_class == "likely_benign":
        return ("BP4", "benign")
    return (None, None)


def freq_call(freq_status, af):
    """'common' (BA1/BS1 territory), 'rare' (PM2 territory), or '' (no code)."""
    if freq_status == "absent":
        return "rare"
    if freq_status == "unmapped":
        return ""
    try:
        v = float(af)
    except (TypeError, ValueError):
        return ""
    if v > 0.01:
        return "common"
    if v < 0.0001:
        return "rare"
    return ""


def lean(fc, insil_lean):
    """
    Combine the two axes. In-silico (AlphaMissense) is the primary driver.

    SERPINA1 caveat: the Z and S alleles are common yet pathogenic founder
    variants, so population frequency alone may NOT assert benign here. A benign
    lean therefore requires the in-silico axis to agree (BP4); a bare 'common'
    frequency with no in-silico call is 'insufficient', not benign.
    """
    pp3 = insil_lean == "path"
    bp4 = insil_lean == "benign"
    common = fc == "common"
    rare = fc == "rare"
    if pp3:
        return "Conflicting signals" if common else "Lean pathogenic"
    if bp4:
        return "Conflicting signals" if rare else "Lean benign"
    if rare:
        return "Insufficient (rarity only)"
    if common:
        return "Insufficient (frequency unreliable here)"
    return "No information"


def main():
    rows = list(csv.DictReader(open(IN_DB)))
    hgvs_map = {}                      # hgvs string -> row
    for r in rows:
        h = clean_hgvs(r["variant_name"])
        if h:
            hgvs_map.setdefault(h, []).append(r)

    hgvs_list = list(hgvs_map.keys())
    print(f"[input] {len(rows)} variants, {len(hgvs_list)} with a clean cDNA HGVS")

    am_result = {}                     # hgvs -> (score, class)
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    for i in range(0, len(hgvs_list), BATCH):
        chunk = hgvs_list[i:i + BATCH]
        for attempt in range(4):
            try:
                resp = sess.post(f"{VEP}?AlphaMissense=1",
                                 data=json.dumps({"hgvs_notations": chunk}), timeout=120)
                if resp.status_code == 429:
                    time.sleep(2 * (attempt + 1)); continue
                resp.raise_for_status()
                for res in resp.json():
                    inp = res.get("input")
                    am = am_for_result(res)
                    if inp and am:
                        am_result[inp] = am
                break
            except Exception as e:
                print(f"  [batch {i}] retry {attempt}: {e}")
                time.sleep(2 * (attempt + 1))
        print(f"[vep] {min(i+BATCH,len(hgvs_list))}/{len(hgvs_list)} done, "
              f"{len(am_result)} AM scores so far")
        time.sleep(0.3)

    cols = list(rows[0].keys()) + ["am_pathogenicity", "am_class", "insilico_code", "provisional_lean"]
    n_am = n_pp3 = n_bp4 = 0
    counts = {}
    for r in rows:
        h = clean_hgvs(r["variant_name"])
        am = am_result.get(h)
        if am:
            score, amcls = am
            r["am_pathogenicity"] = f"{score:.4f}"
            r["am_class"] = amcls
            icode, ilean = insilico_code(amcls)
            n_am += 1
        else:
            r["am_pathogenicity"] = ""
            r["am_class"] = ""
            icode, ilean = (None, None)
        r["insilico_code"] = icode or ""
        if icode == "PP3":
            n_pp3 += 1
        if icode == "BP4":
            n_bp4 += 1
        prov = lean(freq_call(r["freq_status"], r["gnomad_af"]), ilean)
        r["provisional_lean"] = prov
        counts[prov] = counts.get(prov, 0) + 1

    with open(OUT_DB, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"\n[done] wrote {OUT_DB}")
    print(f"[in-silico] AlphaMissense scored {n_am} variants  (PP3={n_pp3}, BP4={n_bp4})")
    print(f"[lean] " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
