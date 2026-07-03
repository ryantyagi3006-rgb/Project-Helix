export default function Pathways() {
  return (
    <>
      <header className="page-header wrap">
        <p className="eyebrow">Guideline synthesis</p>
        <h1>Pathways</h1>
        <p className="lede">How a genetic result routes to a guideline action, never a verdict. Every state below ends in one of four steps: test, refer, counsel, or monitor. And two guidelines diverge on the first question of all, which is who should be tested at all.</p>
      </header>

      <section className="reveal">
        <div className="wrap">
          <h2>The first divergence: who to test</h2>
          <p className="lede narrow" style={{ marginBottom: "6px" }}>Before any result exists, the guidelines disagree on the entry gate. Project Helix surfaces the split rather than picking a side.</p>
          <div className="gate">
            <div className="card glass">
              <h3>Alpha-1 Foundation, ATS and ERS</h3>
              <p className="pos">Test every adult with persistent airflow obstruction once, along with those who have unexplained liver disease and the first-degree relatives of known cases. Broad, one-time detection.</p>
              <span className="grade">Standard recommendation</span>
              <p className="cite">Alpha-1 Foundation CPG</p>
            </div>
            <div className="card glass">
              <h3>Indian ICS and NCCP</h3>
              <p className="pos">Restrict testing to young patients with lower-lobe emphysema, or atypical high-probability COPD. Indian prevalence data is sparse and augmentation therapy is not routinely available, so broad testing is not advised.</p>
              <span className="grade">Usual practice point</span>
              <p className="cite">Gupta et al., Lung India 2013;30(3):228-267</p>
            </div>
          </div>
        </div>
      </section>

      <section className="reveal">
        <div className="wrap">
          <h2>From result to action</h2>
          <p className="lede narrow" style={{ marginBottom: "20px" }}>Six genetic result-states, each routed to the next step its guideline recommends. The action describes what to do next, never a conclusion about the person.</p>
          <div className="routes glass">
            <div className="route r-none">
              <div className="state">Pi MM<small>Normal AAT</small></div>
              <div className="risk">Two normal M alleles. No alpha-1 antitrypsin deficiency.</div>
              <div className="acts"><span className="act none">No AATD action</span></div>
            </div>
            <div className="route r-low">
              <div className="state">Pi MS<small>Near-normal AAT</small></div>
              <div className="risk">One S allele. A carrier, with risk not meaningfully raised on its own.</div>
              <div className="acts"><span className="act">Counsel</span></div>
            </div>
            <div className="route r-low">
              <div className="state">Pi MZ<small>Mildly reduced AAT</small></div>
              <div className="risk">One Z allele. A carrier, with modest risk that is amplified by smoking.</div>
              <div className="acts"><span className="act">Counsel</span><span className="act">Monitor</span></div>
            </div>
            <div className="route r-mod">
              <div className="state">Pi SZ<small>Moderately reduced AAT</small></div>
              <div className="risk">One S and one Z allele. Intermediate risk, higher in smokers.</div>
              <div className="acts"><span className="act">Refer</span><span className="act">Counsel</span><span className="act">Monitor</span></div>
            </div>
            <div className="route r-high">
              <div className="state">Pi ZZ<small>Severely reduced AAT</small></div>
              <div className="risk">Two Z alleles. The highest risk of early emphysema and of liver disease.</div>
              <div className="acts"><span className="act">Refer</span><span className="act">Counsel</span><span className="act">Monitor</span></div>
            </div>
            <div className="route r-vus">
              <div className="state">Rare or VUS<small>Uncertain effect</small></div>
              <div className="risk">A variant of uncertain significance. Its effect is not established.</div>
              <div className="acts"><span className="act">Monitor</span><span className="act">Reassess</span><span className="act">Test family</span></div>
            </div>
          </div>
          <p style={{ color: "var(--muted)", fontSize: "0.95rem", marginTop: "24px", maxWidth: "64ch" }}>A variant of uncertain significance stays on the monitor-and-reassess path. It must not drive management. That is the principle the whole of Project Helix holds to: where evidence is thin, the honest output is the next guideline step, not a verdict about a patient.</p>
          <p className="cite" style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: "0.72rem", color: "var(--muted)", marginTop: "18px" }}>Synthesis of published guideline pathways. Alpha-1 Foundation CPG. Gupta et al., Lung India 2013;30(3):228-267. Not individualised medical advice.</p>
        </div>
      </section>
    </>
  );
}
