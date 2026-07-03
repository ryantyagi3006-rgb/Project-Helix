import { useState } from "react";
import { NavLink, Link } from "react-router-dom";

const APP_URL = "https://breathebetter-dpsi.vercel.app";

export default function Nav({ onToggleTheme }) {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  return (
    <nav>
      <div className="nav-inner">
        <Link className="brand" to="/" aria-label="Project Helix, BreatheBetter, DPS International home" onClick={close}>
          <img className="nav-logo nav-logo-light" src="/helix-logo-light.png" alt="Project Helix, BreatheBetter" />
          <img className="nav-logo nav-logo-dark" src="/helix-logo-dark.png" alt="" aria-hidden="true" />
          <span className="brand-divider" />
          <img className="nav-dps" src="/dps-logo.png" alt="DPS International" />
        </Link>
        <div className="nav-right">
          <div className={"nav-links" + (open ? " open" : "")} id="navlinks">
            <NavLink to="/" end onClick={close}>Overview</NavLink>
            <NavLink to="/methods" onClick={close}>Methods</NavLink>
            <NavLink to="/pathways" onClick={close}>Pathways</NavLink>
            <NavLink to="/data" onClick={close}>Data</NavLink>
            <NavLink to="/privacy" onClick={close}>Privacy Policy</NavLink>
            <a className="btn btn-glass nav-app" href={APP_URL} target="_blank" rel="noopener">Open BreatheBetter App</a>
          </div>
          <button
            className="theme-toggle"
            aria-label="Toggle dark mode"
            title="Toggle light and dark"
            onClick={onToggleTheme}
          >
            <svg className="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" /></svg>
            <svg className="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
          </button>
          <button className="nav-toggle" aria-label="Menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>Menu</button>
        </div>
      </div>
    </nav>
  );
}
