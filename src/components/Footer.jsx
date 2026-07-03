import { Link } from "react-router-dom";

const APP_URL = "https://breathebetter-dpsi.vercel.app";

export default function Footer() {
  return (
    <footer>
      <div className="wrap">
        <div className="foot-grid">
          <div>
            <div className="foot-brand">
              <img src="/favicon.svg" alt="BreatheBetter logo" />
              <span className="brand-text">
                <span className="brand-name">Breathe<span>Better</span></span>
                <span className="brand-sub">Project Helix</span>
              </span>
            </div>
            <p className="tag" style={{ margin: "0 0 6px" }}>Spira. Scio. Vive.</p>
            <p style={{ margin: 0, maxWidth: "34ch" }}>A research extension for spirometry access and innovation.</p>
            <div className="foot-dps"><img src="/dps-logo.png" alt="DPS International" /></div>
          </div>
          <div>
            <div className="foot-h">Explore</div>
            <ul>
              <li><Link to="/">Overview</Link></li>
              <li><Link to="/methods">Methods</Link></li>
              <li><Link to="/pathways">Pathways</Link></li>
              <li><Link to="/data">Data</Link></li>
              <li><Link to="/privacy">Privacy Policy</Link></li>
              <li><a href={APP_URL} target="_blank" rel="noopener">Open BreatheBetter App</a></li>
            </ul>
          </div>
          <div>
            <div className="foot-h">Sources</div>
            <ul>
              <li>Alpha-1 Foundation CPG</li>
              <li>Gupta et al., Lung India 2013;30(3):228-267</li>
              <li>MGB Variant Curation Task Force</li>
              <li>ACMG, PMID 25741868</li>
              <li>ClinVar and gnomAD r4</li>
            </ul>
          </div>
        </div>
        <p className="foot-note">A student research project for awareness and education. Not medical advice. Prepared by Ryan Tyagi, MYP Personal Project, DPS International.</p>
      </div>
    </footer>
  );
}
