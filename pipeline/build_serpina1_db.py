"""
build_serpina1_db.py
=====================
Reconstructs a SERPINA1 variant database by querying ClinVar (via NCBI
E-utilities) and gnomAD (via its GraphQL API), then writes the result to CSV.

WHY THIS SCRIPT EXISTS
----------------------
The previous database stored only the FINAL ClinVar label. That is why the
"resolvability" idea could not be built: it needed the individual ACMG inputs,
and they were never captured. This rebuild captures the RAW INPUTS
(frequency, review/conflict status) so richer questions stay possible later.

WHAT THIS SCRIPT DOES *NOT* DO
------------------------------
It does not fill the reclassification-history columns (old_class, new_class,
evidence_that_moved_it). Those do not exist in ClinVar or gnomAD in any
queryable form. They are your hand-curated, original asset. The script writes
those columns as EMPTY on purpose, so you fill them by hand from the
literature. It does not silently drop them.

HOW TO RUN (on your own machine, not in a restricted sandbox):
    pip install requests
    python build_serpina1_db.py

Requires internet access to eutils.ncbi.nlm.nih.gov and gnomad.broadinstitute.org.
"""

import csv
import sys
import time
import json
import requests   # the standard Python HTTP library; install with: pip install requests

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# The gene we are building the database around. Kept as a constant so there is
# a single place to change it if you ever extend to another gene.
GENE = "SERPINA1"

# NCBI politely asks that you identify yourself and stay under ~3 requests/sec
# without an API key. We add a small delay between calls to respect that.
# (If you register a free NCBI API key you may raise this rate; not required.)
NCBI_DELAY_SECONDS = 0.4

# The base URLs for the two data sources.
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GNOMAD_API = "https://gnomad.broadinstitute.org/api"

# The output file. Written to the same folder the script runs in.
OUTPUT_CSV = "serpina1_database.csv"


# ---------------------------------------------------------------------------
# STEP 1: CLINVAR — find every SERPINA1 variant ID
# ---------------------------------------------------------------------------
def clinvar_search_ids(gene):
    """
    ClinVar access is a TWO-STEP process. This is step one.

    'esearch' takes a text query and returns a list of ClinVar internal IDs
    (numbers), NOT the actual variant data. We ask for all records linked to
    the gene. retmax caps how many IDs come back; SERPINA1 has a few hundred
    records, so 2000 is a safe ceiling.

    Returns: a list of ID strings.
    """
    params = {
        "db": "clinvar",              # which NCBI database to search
        "term": f"{gene}[gene]",      # restrict the query to this gene symbol
        "retmax": 2000,               # max number of IDs to return
        "retmode": "json",            # ask for JSON rather than XML
    }
    resp = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    resp.raise_for_status()           # raise a clear error if the request failed
    ids = resp.json()["esearchresult"]["idlist"]
    print(f"[ClinVar] found {len(ids)} variant records for {gene}")
    return ids


def clinvar_fetch_summaries(ids):
    """
    Step two of ClinVar access.

    'esummary' takes the IDs from step one and returns the actual records.
    We request them in BATCHES of 200 because sending 500 IDs in one URL can
    exceed length limits and get rejected. Batching is the reliable way.

    From each record we pull three things:
      - the variant title (contains the HGVS-style name)
      - the clinical significance (Pathogenic / VUS / Benign / etc.)
      - the review status  <-- this is where the CONFLICT flag lives.
        ClinVar phrases conflicts as "conflicting classifications", so we
        detect that string. A conflicted VUS is a different object from a
        quiet VUS, which is exactly the distinction the old database lost.

    Returns: a list of dicts, one per variant.
    """
    records = []
    BATCH = 200
    for start in range(0, len(ids), BATCH):
        batch_ids = ids[start:start + BATCH]
        params = {
            "db": "clinvar",
            "id": ",".join(batch_ids),   # comma-joined IDs, as the API expects
            "retmode": "json",
        }
        resp = requests.get(f"{EUTILS}/esummary.fcgi", params=params, timeout=30)
        resp.raise_for_status()
        result = resp.json()["result"]

        # result["uids"] lists the IDs; every other key is a record keyed by ID.
        for uid in result.get("uids", []):
            rec = result[uid]
            # germline_classification holds the significance + review status in
            # current ClinVar summaries. We guard with .get() so a missing
            # field yields "" instead of crashing the whole run.
            classification = rec.get("germline_classification", {})
            significance = classification.get("description", "")
            review_status = classification.get("review_status", "")
            is_conflicted = "conflicting" in review_status.lower()

            records.append({
                "variant_name": rec.get("title", ""),
                "clinvar_significance": significance,
                "clinvar_review_status": review_status,
                "clinvar_conflicting": "yes" if is_conflicted else "no",
            })

        print(f"[ClinVar] fetched summaries {start}-{start + len(batch_ids)}")
        time.sleep(NCBI_DELAY_SECONDS)   # stay under the rate limit
    return records


# ---------------------------------------------------------------------------
# STEP 2: GNOMAD — get population frequency for the gene's variants
# ---------------------------------------------------------------------------
def gnomad_fetch_frequencies(gene):
    """
    gnomAD uses GraphQL, not REST. Instead of a URL with parameters, we POST a
    QUERY STRING describing exactly the fields we want back. This asks for every
    variant in the gene and, for each, its genome allele frequency (af) and
    allele count (ac). Frequency is the raw material for the ACMG 'PM2' criterion
    (a variant being rare supports pathogenicity), which is precisely an input
    the old database failed to keep.

    dataset gnomad_r4 is the current major release at time of writing; if gnomAD
    publishes a newer one, update this string.

    Returns: a dict mapping variant_id -> allele frequency, for fast lookup.
    """
    query = """
    query VariantsInGene($gene: String!) {
      gene(gene_symbol: $gene, reference_genome: GRCh38) {
        variants(dataset: gnomad_r4) {
          variant_id
          genome { af ac an }
        }
      }
    }
    """
    resp = requests.post(
        GNOMAD_API,
        json={"query": query, "variables": {"gene": gene}},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()

    # GraphQL returns errors inside a 200 response, so we must check explicitly
    # rather than trusting the HTTP status alone.
    if "errors" in payload and payload["errors"]:
        raise RuntimeError(f"gnomAD returned errors: {payload['errors']}")

    variants = payload["data"]["gene"]["variants"]
    freq = {}
    for v in variants:
        genome = v.get("genome") or {}
        freq[v["variant_id"]] = genome.get("af")
    print(f"[gnomAD] retrieved frequencies for {len(freq)} variants")
    return freq


# ---------------------------------------------------------------------------
# STEP 3: WRITE THE DATABASE
# ---------------------------------------------------------------------------
def write_csv(clinvar_records, gnomad_freq, path):
    """
    Combines the two sources into one CSV.

    NOTE ON JOINING: ClinVar titles and gnomAD variant_ids are not identical
    strings, so an automatic per-variant join is unreliable. Rather than fake a
    match, we write the ClinVar rows in full and attach gnomAD frequency ONLY
    where you later map them. The gnomad_af column is written empty by default,
    with the raw gnomAD data saved separately (see main) so you can join by hand
    or extend this function once you decide on a matching key. Pretending the
    join is clean would reintroduce exactly the kind of hidden error we are
    trying to avoid.

    The final columns include the HAND-CURATED block, written empty on purpose:
      old_class, new_class, evidence_that_moved_it
    These are your original reclassification data. The pipeline cannot fill them.
    """
    columns = [
        "variant_name",
        "clinvar_significance",
        "clinvar_review_status",
        "clinvar_conflicting",
        "gnomad_af",              # left blank; populated when you define the join
        # ---- hand-curated block below: fill from the literature ----
        "old_class",
        "new_class",
        "evidence_that_moved_it",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for rec in clinvar_records:
            row = {col: "" for col in columns}   # start every field empty
            row.update(rec)                       # fill in the ClinVar fields
            writer.writerow(row)

    print(f"[write] wrote {len(clinvar_records)} rows to {path}")
    print("[write] gnomad_af and the reclassification columns are intentionally "
          "empty. Fill the reclassification columns by hand; see the saved "
          "gnomad_frequencies.json for the frequency data to join in.")


# ---------------------------------------------------------------------------
# MAIN: run the three steps in order
# ---------------------------------------------------------------------------
def main():
    try:
        ids = clinvar_search_ids(GENE)
        if not ids:
            print("[stop] ClinVar returned no IDs. Check the gene symbol.")
            sys.exit(1)

        clinvar_records = clinvar_fetch_summaries(ids)

        gnomad_freq = gnomad_fetch_frequencies(GENE)
        # Save the raw gnomAD data alongside, so the frequency work is not lost
        # even though we do not auto-join it into the CSV.
        with open("gnomad_frequencies.json", "w", encoding="utf-8") as f:
            json.dump(gnomad_freq, f, indent=2)

        write_csv(clinvar_records, gnomad_freq, OUTPUT_CSV)
        print("[done] database reconstruction complete.")

    except requests.HTTPError as e:
        # A loud, specific failure beats a silent half-built database.
        print(f"[error] an HTTP request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[error] unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
