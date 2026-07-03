export default function Methods() {
  return (
    <>
      <header className="page-header wrap">
        <p className="eyebrow">How it was built</p>
        <h1>Methods</h1>
        <p className="lede">Three methods joined into one reproducible chain, from raw records to a guideline-aware reading of each variant.</p>
      </header>

      <section className="reveal">
        <div className="wrap">
          <div className="method">
            <div className="num">01</div>
            <div>
              <h3>Database reconstruction</h3>
              <p>566 SERPINA1 variants pulled from ClinVar through a reproducible Python pipeline, each carrying its clinical significance, review status, and conflict flag. Population frequency was joined from gnomAD by resolving every cDNA change to a GRCh38 coordinate, then reading the allele frequency back.</p>
              <p className="cite">ClinVar + gnomAD r4 · coordinate mapping via NCBI Variation Services</p>
            </div>
          </div>
          <div className="method">
            <div className="num">02</div>
            <div>
              <h3>Clinical-pathway mapping</h3>
              <p>Each genetic result-state is routed to the next step its guideline recommends. The Alpha-1 Foundation pathway forms the spine. The Indian ICS and NCCP guideline is surfaced where it diverges: it grades alpha-1 antitrypsin testing as a usual-practice point, limited to young patients with lower-lobe emphysema, rather than a broad recommendation.</p>
              <p className="cite">Alpha-1 Foundation CPG · Gupta et al., Lung India 2013;30(3):228-267</p>
            </div>
          </div>
          <div className="method">
            <div className="num">03</div>
            <div>
              <h3>VUS interpretation framework</h3>
              <p>The MGB Variant Curation framework places a variant on a benign-to-pathogenic spectrum from its ACMG codes. Project Helix automates the two mechanical axes it can defend, population rarity from gnomAD and the AlphaMissense in-silico prediction, and combines them into a provisional lean. Every judgment code it cannot assess is flagged, so the lean is never a classification.</p>
              <p className="cite">MGB Variant Curation Task Force · AlphaMissense · ACMG, PMID 25741868</p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
