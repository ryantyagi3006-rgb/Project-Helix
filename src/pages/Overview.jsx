import { Link } from "react-router-dom";

export default function Overview() {
  return (
    <>
      <header className="hero wrap">
        <h1 className="sr-only">Project Helix, a research extension of BreatheBetter</h1>
        <div className="hero-brandline">
          <img src="/dps-logo.png" alt="DPS International" />
          <span>Research Extension of BreatheBetter</span>
        </div>
        <h2 className="hero-title">Project Helix</h2>
        <p className="tagline">Spira. Scio. Vive.</p>
        <p className="sub">Mapping the genetic basis of alpha-1 antitrypsin deficiency, a well established genetic risk factor for COPD.</p>
        <div className="hero-cta">
          <Link className="btn btn-primary" to="/data">View Data</Link>
        </div>
      </header>

      <section className="reveal">
        <div className="wrap">
          <div className="two">
            <div>
              <h3>What this project is</h3>
              <p>A reconstructed, frequency-annotated map of the 566 SERPINA1 variants held in ClinVar, joined to gnomAD population data and read against two clinical guidelines and one variant-curation framework. It gathers the raw inputs behind a classification rather than only the final label.</p>
            </div>
            <div>
              <h3>Why it exists</h3>
              <p>Alpha-1 antitrypsin deficiency is common enough to matter and underdiagnosed enough to be missed. A variant of uncertain significance sits at the centre of that gap. This work assembles the evidence around each variant so the uncertainty is visible and honestly bounded.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="band reveal">
        <div className="wrap">
          <blockquote>Every pathway ends in an action a guideline recommends: test, refer, counsel, or monitor.</blockquote>
          <p className="support">A variant of uncertain significance must not drive clinical decisions. Where evidence is thin, the honest output is the boundary of what is known, not a classification dressed up as one.</p>
        </div>
      </section>

      <section className="reveal">
        <div className="wrap">
          <h2>Four concrete outputs</h2>
          <div className="grid2" style={{ marginTop: "36px" }}>
            <div className="card glass"><span className="k">566</span><h3>Frequency-annotated variant dataset</h3><p>Every SERPINA1 record in ClinVar with significance, review status, conflict flag, and a gnomAD allele frequency where one could be resolved.</p></div>
            <div className="card glass"><span className="k">83%</span><h3>Reproducible frequency join</h3><p>A Python pipeline that maps cDNA changes to genomic coordinates and attaches gnomAD frequency, joined for 468 of 566 variants and honest about the rest.</p></div>
            <Link className="card glass" to="/pathways"><span className="k">2</span><h3>Guideline decision-pathway map</h3><p>Genetic result-states routed to guideline-cited next steps, with the ICS and NCCP divergence surfaced rather than smoothed over.</p><span className="more">View the pathways</span></Link>
            <div className="card glass"><span className="k">2-axis</span><h3>Provisional lean engine</h3><p>gnomAD rarity and AlphaMissense predictions combined into a provisional VUS lean on the MGB spectrum, with judgment codes flagged as expert-only.</p></div>
          </div>
        </div>
      </section>
    </>
  );
}
