export default function Privacy() {
  return (
    <>
      <header className="page-header wrap">
        <p className="eyebrow">Policies and disclaimers</p>
        <h1>Privacy Policy</h1>
        <p className="lede">What Project Helix is, what it does and does not do, the honest limits of the research, and how information is handled. Written in plain language for a student project. This is not medical or legal advice.</p>
      </header>

      <section>
        <div className="wrap policy">
          <div className="policy-block reveal">
            <h2>About Project Helix</h2>
            <p>Project Helix is a research and synthesis extension of <strong>BreatheBetter</strong>, a student awareness initiative on spirometry access and lung health by Ryan Tyagi. Helix focuses on the genetics behind alpha-1 antitrypsin deficiency, a well established genetic risk factor for COPD. It reconstructs the public SERPINA1 variant record, joins it to population frequency data, and reads it against published clinical guidelines and a variant-curation framework.</p>
            <p>The initiative exists to make the uncertainty around a variant of uncertain significance visible and honestly bounded, as a study aid and a record of the underlying research. It is built entirely on public, de-identified reference data.</p>
          </div>

          <div className="policy-block reveal">
            <h2>What it does, and what it does not do</h2>
            <h3>What it does</h3>
            <ul>
              <li>Presents 566 public SERPINA1 variant records from ClinVar with their classification and review status.</li>
              <li>Joins population allele frequency from gnomAD wherever a variant can be mapped to a genomic coordinate.</li>
              <li>Illustrates the mechanical, frequency-derived ACMG codes and the guideline-cited decision pathways.</li>
            </ul>
            <h3>What it does not do</h3>
            <ul>
              <li>It does not diagnose, classify a patient, or return a conclusion about any individual.</li>
              <li>It does not provide medical advice or treatment guidance.</li>
              <li>It does not collect accounts, contact details, or health measurements from visitors to this research site.</li>
            </ul>
            <div className="callout glass"><p>A variant of uncertain significance must not drive clinical decisions. Where evidence is thin, the honest output is the boundary of what is known.</p></div>
          </div>

          <div className="policy-block reveal">
            <h2>Research limitations</h2>
            <h3>Source bias</h3>
            <p>ClinVar and gnomAD are European-weighted. Nothing here supports a claim about SERPINA1 in the Indian population, and none is made.</p>
            <h3>A snapshot, not a live feed</h3>
            <p>The dataset carries a retrieval date. It is a fixed picture of ClinVar, not a substitute for querying ClinVar today.</p>
            <h3>Partial frequency join</h3>
            <p>468 of 566 variants carry a real frequency signal. The 98 unmapped ones are mostly intronic or splice-region changes, large structural events, and non-canonical transcripts, which resist a simple cDNA-to-genomic mapping. They are marked unmapped, never guessed as absent.</p>
            <h3>Guideline jurisdiction</h3>
            <p>The pathway spine is a United States recommendation. The Indian ICS and NCCP divergence is surfaced, not resolved. Neither guideline is presented as universal.</p>
            <h3>A retired component</h3>
            <p>A frequency-only lean estimator was built, found too weak on its own (almost every variant in this gene is rare), and rebuilt around two axes: gnomAD rarity plus the AlphaMissense in-silico prediction. Even combined it stays provisional, because the judgment codes that truly resolve a variant need a human. It is a triage aid, never a classification, and it surfaces its disagreements with ClinVar rather than hiding them.</p>
          </div>

          <div className="policy-block reveal">
            <h2>Privacy and your data</h2>
            <p>This Project Helix research site is static. It does not require an account and does not collect personal or health information from visitors. The policies below govern the wider BreatheBetter measurement platform, where breathing data is collected, and are included here so the full picture is in one place.</p>
            <h3>Information the platform collects</h3>
            <ul>
              <li><strong>Account information:</strong> the email address used to sign in.</li>
              <li><strong>Measurement data:</strong> FEV1, FVC and FEV1/FVC results, raw timestamped sensor readings, the calibration factor, and the time of each test.</li>
              <li><strong>Local preferences:</strong> theme, language and calibration settings stored in your browser.</li>
            </ul>
            <h3>How it is used</h3>
            <p>Data is used only to display your results, build your personal history and flow-volume curves, and let you track changes over time. It is not sold, used for advertising, or shared with third parties for marketing.</p>
            <h3>Storage and security</h3>
            <p>Account and measurement data are stored in a secured cloud database with access rules, so each user can read and write only their own records. Sign-in is handled by an established authentication provider, and raw passwords are never seen or stored.</p>
            <h3>Your rights</h3>
            <ul>
              <li>Access and export your full result history at any time.</li>
              <li>Delete individual results or request removal of your data.</li>
              <li>Withdraw consent by discontinuing use and deleting your records.</li>
            </ul>
            <h3>Cookies and local storage</h3>
            <p>No advertising or third-party tracking cookies are used. Essential items (sign-in session, theme, language, calibration factor) are kept in your browser's local storage. There is no cross-site profiling. Clearing your browser's site data resets these preferences but does not delete results already saved to an account.</p>
            <h3>Health data consent</h3>
            <p>Breathing measurements are health-related information and are treated with particular care. Running a test and saving the result provides explicit, informed consent to collect those measurements for awareness, not clinical diagnosis. Participation is voluntary and can be withdrawn at any time by deleting your data. Fresh consent is sought before any new or different use.</p>
            <h3>Children and students</h3>
            <p>The project operates in a school context. Students should use it with the awareness of a parent, guardian or teacher where their school requires it.</p>
          </div>

          <div className="policy-block reveal">
            <h2>Medical disclaimer</h2>
            <div className="callout glass"><p><strong>BreatheBetter and Project Helix are not medical devices and do not provide medical advice, diagnosis or treatment.</strong> They are educational awareness tools only.</p></div>
            <ul>
              <li>Platform results are estimates from low-cost hardware and may differ significantly from clinical spirometry performed by a healthcare professional.</li>
              <li>A "Normal" result does not rule out illness; a "Low" or "Borderline" result does not confirm any condition.</li>
              <li>Never start, stop or change any treatment based on a result from this project.</li>
              <li>Always seek the advice of a physician or qualified health provider with any questions about a medical condition.</li>
            </ul>
            <p>Reliance on any information provided here is solely at your own risk.</p>
          </div>

          <div className="policy-block reveal">
            <h2>Emergency notice</h2>
            <div className="callout warn glass"><p><strong>This project must never be used in a medical emergency.</strong> It is not monitored, is not a diagnostic device, and cannot summon help.</p></div>
            <p>If you or someone near you has severe difficulty breathing, chest pain, bluish lips or face, confusion, fainting, or any other sign of a serious medical emergency, stop and contact emergency services immediately.</p>
            <ul className="pill-list">
              <li>India, all emergencies: 112</li>
              <li>India, ambulance: 102 or 108</li>
              <li>Outside India: your local emergency number</li>
            </ul>
            <p style={{ marginTop: "16px" }}>Contact a doctor, hospital, or a trusted adult without delay. Do not wait for or rely on any reading before seeking help in an emergency.</p>
          </div>

          <div className="policy-block reveal">
            <h2>Terms and updates</h2>
            <p>By using this project you agree it is provided for educational and awareness purposes only, in a supervised, non-clinical setting. It is provided as is, without warranty of any kind, and accuracy is not guaranteed. To the maximum extent permitted by law, the author is not liable for any decision made, or harm arising, from use of or reliance on it. These policies may be updated as the project evolves, and continued use after changes constitutes acceptance of the revised policies.</p>
            <p className="policy-meta">Effective 18 June 2026. Prepared by Ryan Tyagi, MYP Personal Project, DPS International.</p>
          </div>
        </div>
      </section>
    </>
  );
}
