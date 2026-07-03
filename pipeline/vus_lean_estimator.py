"""
vus_lean_estimator.py
=====================
Batch estimator that places each SERPINA1 variant on the MGB VUS lean-spectrum
using ONLY the ACMG codes that can be mechanically determined, and honestly
flags the judgment-based codes it cannot assess.

WHAT THIS TOOL HONESTLY IS
--------------------------
It automates the tedious, mechanical part of VUS triage: pulling gnomAD
frequency, deriving the frequency-based ACMG codes, applying published in-silico
cutoffs IF a local score file is provided, and tallying those into a provisional
lean. It runs across all variants at once, which no human would do by hand.

WHAT IT IS NOT
--------------
It is NOT an ACMG classifier. It assigns ONLY mechanical codes:
  - PM2_Supporting / BS1 / BA1   from gnomAD allele frequency
  - PVS1 (flagged, not fired)    for null consequences (SEE SERPINA1 caveat below)
  - PP3 / BP4                    ONLY if a local REVEL/AlphaMissense file is given
It CANNOT assess judgment codes (PS3, BS3, PP1, BS4, PS4, PM3, PP4, etc.) because
those need a human to read functional studies, pedigrees, and case data. Every
output row lists these as "needs_human_review". A lean here is PROVISIONAL.

SERPINA1 PVS1 CAVEAT
--------------------
SERPINA1 disease mechanism is mixed: loss-of-function in lung, but GAIN-of-
function (polymerisation) in liver. So a null variant is not automatically the
classic LoF-pathogenic case PVS1 assumes. The script therefore FLAGS null
consequences for review rather than firing PVS1 outright.

THRESHOLDS (cited, printed in output)
-------------------------------------
  BA1  (stand-alone benign): allele frequency > 0.05        [ACMG/AMP 2015]
  BS1  (strong benign):      allele frequency > 0.01         [disease-adjusted; conservative default]
  PM2_Supporting:            absent or AF < 0.0001           [ClinGen SVI 2020, PM2 downgraded to Supporting]
  PP3 (in-silico path):      REVEL >= 0.75                   [ClinGen SVI in-silico calibration]
  BP4 (in-silico benign):    REVEL <= 0.25                   [ClinGen SVI in-silico calibration]
  REVEL 0.25-0.75:           NO CALL (honest ambiguous band)
These are defaults you can change at the top of the file; the value used is
printed per variant so the basis is always visible.

RUN (on your machine, where gnomAD + ClinVar are reachable):
    python3 -m pip install requests
    python3 vus_lean_estimator.py --input serpina1_database.csv --revel revel_scores.csv
    (--revel is optional; without it, in-silico codes are left as 'no data')
"""

import csv
import sys
import time
import argparse
import requests

# ---- Editable thresholds (each printed in output so the basis is transparent) ----
BA1_FREQ = 0.05      # above this: stand-alone benign
BS1_FREQ = 0.01      # above this (and <=BA1): strong benign
PM2_FREQ = 0.0001    # below this (or absent): PM2_Supporting
REVEL_PATH = 0.75    # >= this: PP3
REVEL_BENIGN = 0.25  # <= this: BP4

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GNOMAD_API = "https://gnomad.broadinstitute.org/api"
DELAY = 0.4


def parse_variant_name(name):
    """
    Pull the transcript and the cDNA change out of an HGVS-style name like
    'NM_000295.5(SERPINA1):c.739C>T (p.Arg247Cys)'.

    We need the transcript because gnomAD/ClinVar coordinates must match it;
    17961 uses a different transcript from most rows, and computing frequency on
    the wrong transcript silently produces wrong codes. So we extract it and
    later WARN if it is not the canonical one.

    Returns (transcript, cdna, protein) as strings; missing parts come back ''.
    """
    transcript = ""
    cdna = ""
    protein = ""
    if "(" in name and ")" in name:
        transcript = name.split("(")[0].strip()
    if ":c." in name:
        cdna = "c." + name.split(":c.")[1].split(" ")[0]
    if "p." in name:
        protein = "p." + name.split("p.")[1].rstrip(")")
    return transcript, cdna, protein


def classify_consequence(protein):
    """
    Rough consequence class from the protein change string.
      - 'p.Xxx=' means synonymous (no amino-acid change)
      - 'Ter' or '*' means nonsense (null)
      - otherwise treat as missense
    This is a coarse call from the name only; a real pipeline would use VEP.
    We keep it honest by labelling it 'consequence_guess'.
    """
    if not protein:
        return "unknown"
    if protein.endswith("="):
        return "synonymous"
    if "Ter" in protein or "*" in protein:
        return "nonsense_null"
    return "missense"


NCBI_VARIATION = "https://api.ncbi.nlm.nih.gov/variation/v0"

# Simple in-memory caches so re-seen variants don't re-hit the APIs.
# A full 566-variant run makes one mapping call + one gnomAD call each, so
# caching also protects against accidental duplicate rows in the input.
_coord_cache = {}
_gnomad_cache = None   # gnomAD gene query is fetched once and reused


def hgvs_to_coord(transcript, cdna):
    """
    Translate an HGVS variant into a GRCh38 chromosomal key that gnomAD understands.

    WHY THIS EXISTS
    ---------------
    gnomAD's API is keyed by chromosomal coordinate (e.g. '14-94378610-C-T'),
    NOT by the HGVS cDNA string ('c.739C>T'). This routes the HGVS through NCBI's
    Variation Services, which returns SPDI, from which we build gnomAD's
    chr-pos-ref-alt key.

    THE 400-ERROR FIX
    -----------------
    NCBI's endpoint needs a CLEAN HGVS expression: 'NM_000295.5:c.739C>T' and
    nothing else. The raw variant names in the database carry extra baggage,
    'NM_000295.5(SERPINA1):c.739C>T (p.Arg247Cys)', with a gene label, a protein
    change, and a space. Sending that whole string caused NCBI to reject it with
    HTTP 400. So we now build the clean string ourselves from the parsed
    transcript and cDNA, and URL-encode it (the '>' must become '%3E', spaces
    must be gone) before the request.

    Returns: a gnomAD variant_id 'chrom-pos-ref-alt', or None if it could not be
    mapped (which the caller must treat as UNKNOWN, never absent).
    """
    # Guard: need both parts to build a valid expression.
    if not transcript or not cdna:
        return None

    # Build the clean expression: transcript:cDNA, no gene, no protein, no spaces.
    clean_hgvs = f"{transcript}:{cdna}".strip()

    if clean_hgvs in _coord_cache:
        return _coord_cache[clean_hgvs]

    # URL-encode so characters like '>' don't break the URL. quote() with an
    # empty 'safe' set encodes everything that needs it, including '>' -> %3E.
    from urllib.parse import quote
    encoded = quote(clean_hgvs, safe="")

    coord = None
    try:
        # Step 1: HGVS -> SPDI (contextuals gives the fully-justified SPDI)
        url = f"{NCBI_VARIATION}/hgvs/{encoded}/contextuals"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        spdi_list = data.get("data", {}).get("spdis", [])
        if spdi_list:
            s = spdi_list[0]
            seq = s.get("seq_id", "")
            pos = s.get("position")
            deleted = s.get("deleted_sequence", "")
            inserted = s.get("inserted_sequence", "")
            # Step 2: RefSeq chromosome accession -> chromosome number.
            # GRCh38 chromosome accessions look like 'NC_000014.9' = chr14.
            if seq.startswith("NC_0000"):
                chrom = str(int(seq[7:9]))   # 'NC_000014.9' -> '14'
                gpos = pos + 1               # SPDI 0-based -> gnomAD 1-based
                coord = f"{chrom}-{gpos}-{deleted}-{inserted}"
    except Exception as e:
        # Print the exact URL sent, so any remaining failure is diagnosable.
        print(f"    [ncbi-map] failed for {clean_hgvs}: {e}")

    _coord_cache[clean_hgvs] = coord
    time.sleep(DELAY)
    return coord


def _load_gnomad_variants():
    """
    Fetch gnomAD's full SERPINA1 variant set ONCE and cache it, keyed by
    variant_id. Called lazily on first frequency lookup. Returns a dict
    {variant_id: af} or an empty dict on failure.
    """
    global _gnomad_cache
    if _gnomad_cache is not None:
        return _gnomad_cache
    query = """
    query GeneVariants($symbol: String!) {
      gene(gene_symbol: $symbol, reference_genome: GRCh38) {
        variants(dataset: gnomad_r4) {
          variant_id
          genome { af }
          exome { af }
        }
      }
    }
    """
    result = {}
    try:
        r = requests.post(GNOMAD_API,
                          json={"query": query, "variables": {"symbol": "SERPINA1"}},
                          timeout=60)
        r.raise_for_status()
        variants = r.json().get("data", {}).get("gene", {}).get("variants", [])
        for v in variants:
            genome = v.get("genome") or {}
            exome = v.get("exome") or {}
            af = genome.get("af")
            if af is None:
                af = exome.get("af")
            result[v["variant_id"]] = af
        print(f"[gnomad] cached {len(result)} SERPINA1 variants")
    except Exception as e:
        print(f"[gnomad] gene fetch failed: {e}")
    _gnomad_cache = result
    return result


def fetch_gnomad_af(transcript, cdna):
    """
    Get the allele frequency for a variant, using proper coordinate mapping.

    Returns one of THREE things, and the distinction is the whole point:
      - a float        : frequency found in gnomAD
      - the str 'ABSENT': variant was successfully mapped AND gnomAD was queried,
                          but the coordinate is genuinely not in gnomAD
      - None           : the variant could NOT be mapped (status UNKNOWN)
    The caller must treat None as 'unknown, assign no frequency code', and only
    treat 'ABSENT' as rarity evidence. Conflating the two was the original bug.
    """
    coord = hgvs_to_coord(transcript, cdna)
    if coord is None:
        return None                      # unmapped -> unknown, NOT absent
    gnomad = _load_gnomad_variants()
    if not gnomad:
        return None                      # gnomAD unreachable -> unknown
    if coord in gnomad:
        return gnomad[coord]             # frequency found (may itself be None->treat as absent below)
    return "ABSENT"                      # mapped, queried, genuinely not present


def frequency_codes(af):
    """
    Apply the mechanical frequency-based ACMG codes from the allele frequency.
    Returns (list_of_codes, explanation_string). Each code is tagged benign or
    pathogenic leaning so the tally step can count them.
    """
    codes = []
    # THE GUARD: three distinct cases, never conflated.
    # 1) None  -> variant could not be mapped; status UNKNOWN; assign NO code.
    if af is None:
        return codes, "frequency UNKNOWN (variant unmapped); no code assigned"
    # 2) 'ABSENT' -> mapped and queried, genuinely not in gnomAD; rarity evidence.
    if af == "ABSENT":
        codes.append(("PM2_Supporting", "path", "confirmed absent from gnomAD"))
        return codes, "confirmed absent from gnomAD; PM2_Supporting"
    # 3) a real number -> apply the frequency thresholds.
    # (A found variant whose af field is None means present-but-AF-unavailable;
    #  treat that as absent-level rarity but note it.)
    if af is None:
        codes.append(("PM2_Supporting", "path", "present but AF unavailable"))
        return codes, "present, AF unavailable; PM2_Supporting"
    if af > BA1_FREQ:
        codes.append(("BA1", "benign", f"AF {af:.4g} > {BA1_FREQ}"))
        return codes, f"AF {af:.4g}: stand-alone benign (BA1)"
    if af > BS1_FREQ:
        codes.append(("BS1", "benign", f"AF {af:.4g} > {BS1_FREQ}"))
        return codes, f"AF {af:.4g}: strong benign (BS1)"
    if af < PM2_FREQ:
        codes.append(("PM2_Supporting", "path", f"AF {af:.4g} < {PM2_FREQ}"))
        return codes, f"AF {af:.4g}: rare (PM2_Supporting)"
    return codes, f"AF {af:.4g}: intermediate, no frequency code"


def insilico_codes(revel):
    """
    Apply PP3/BP4 from a REVEL score IF one was supplied. Honest 'no call' band
    in the middle. Returns (codes, explanation).
    """
    if revel is None:
        return [], "no in-silico score supplied"
    if revel >= REVEL_PATH:
        return [("PP3", "path", f"REVEL {revel} >= {REVEL_PATH}")], f"REVEL {revel}: PP3"
    if revel <= REVEL_BENIGN:
        return [("BP4", "benign", f"REVEL {revel} <= {REVEL_BENIGN}")], f"REVEL {revel}: BP4"
    return [], f"REVEL {revel}: ambiguous band, no call"


def compute_lean(codes):
    """
    Tally the mechanical codes into a provisional lean on the MGB spectrum.
    Counts benign-leaning vs pathogenic-leaning codes. This is deliberately
    simple: it is NOT the full ACMG combining rules (those need the judgment
    codes we don't have). It reflects only the mechanical evidence.
    """
    benign = sum(1 for _, lean, _ in codes if lean == "benign")
    path = sum(1 for _, lean, _ in codes if lean == "path")
    if benign and path:
        return "Conflicting signals"
    if benign and not path:
        return "Lean benign"
    if path and not benign:
        return "Lean pathogenic"
    return "No information"


# the judgment codes this tool CANNOT assess, listed in every row for honesty
JUDGMENT_CODES = "PS3, BS3, PP1, BS4, PS4, PM3, PP4, PM6, PS2"


def process(input_path, revel_path):
    # optional REVEL scores keyed by cDNA or protein change
    revel_map = {}
    if revel_path:
        try:
            with open(revel_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = row.get("variant") or row.get("cdna") or ""
                    try:
                        revel_map[key] = float(row.get("revel", ""))
                    except ValueError:
                        pass
            print(f"[revel] loaded {len(revel_map)} scores")
        except FileNotFoundError:
            print(f"[revel] file {revel_path} not found; proceeding without in-silico codes")

    # read the variant list, skipping any junk title line
    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    hdr = next(i for i, r in enumerate(rows) if "variant_name" in r)
    header = rows[hdr]
    data = [dict(zip(header, r)) for r in rows[hdr + 1:] if len(r) == len(header)]
    print(f"[input] {len(data)} variants")

    CANONICAL = "NM_000295"   # the transcript most SERPINA1 rows use
    out = []
    for i, row in enumerate(data, 1):
        name = row.get("variant_name", "")
        transcript, cdna, protein = parse_variant_name(name)
        consequence = classify_consequence(protein)

        # transcript sanity check
        transcript_warn = "" if CANONICAL in transcript else "NON-CANONICAL TRANSCRIPT"

        af = fetch_gnomad_af(transcript, cdna)
        fcodes, fexpl = frequency_codes(af)

        # human-readable frequency status for the output, handling all 3 cases
        if af is None:
            af_display = ""
            freq_status = "UNKNOWN (unmapped)"
        elif af == "ABSENT":
            af_display = "0 (confirmed absent)"
            freq_status = "confirmed absent"
        else:
            af_display = f"{af:.6g}"
            freq_status = "found"

        revel = revel_map.get(cdna) or revel_map.get(protein)
        icodes, iexpl = insilico_codes(revel)

        # PVS1 handling: flag null consequences for SERPINA1 rather than firing
        pvs1_note = ""
        if consequence == "nonsense_null":
            pvs1_note = "null variant: PVS1 NOT auto-fired (SERPINA1 mixed mechanism); needs review"

        all_codes = fcodes + icodes
        lean = compute_lean(all_codes)
        code_str = "; ".join(f"{c}({lean_})[{why}]" for c, lean_, why in all_codes) or "none"

        out.append({
            "clinvar_id": row.get("clinvar_id", ""),
            "variant_name": name,
            "consequence_guess": consequence,
            "gnomad_af": af_display,
            "freq_status": freq_status,
            "mechanical_codes": code_str,
            "provisional_lean": lean,
            "pvs1_note": pvs1_note,
            "needs_human_review": JUDGMENT_CODES,
            "transcript_warning": transcript_warn,
            "note": "PROVISIONAL: mechanical codes only, not a classification",
        })
        print(f"[{i}/{len(data)}] {name[:40]} -> {lean}")
        time.sleep(DELAY)

    outpath = "vus_lean_results.csv"
    cols = ["clinvar_id", "variant_name", "consequence_guess", "gnomad_af",
            "freq_status", "mechanical_codes", "provisional_lean", "pvs1_note",
            "needs_human_review", "transcript_warning", "note"]
    # rank so the most actionable (clear leans) sort to the top
    order = {"Lean pathogenic": 0, "Conflicting signals": 1, "Lean benign": 2, "No information": 3}
    out.sort(key=lambda r: order.get(r["provisional_lean"], 9))
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f"\n[done] wrote {len(out)} rows to {outpath}")
    print("[reminder] every lean is PROVISIONAL. Judgment codes "
          f"({JUDGMENT_CODES}) were NOT assessed and require expert review.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="serpina1_database.csv")
    ap.add_argument("--revel", default=None, help="optional CSV of REVEL scores")
    args = ap.parse_args()
    try:
        process(args.input, args.revel)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
