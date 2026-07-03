import { useEffect, useState, useCallback } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Nav from "./components/Nav.jsx";
import Footer from "./components/Footer.jsx";
import Overview from "./pages/Overview.jsx";
import Methods from "./pages/Methods.jsx";
import Pathways from "./pages/Pathways.jsx";
import Data from "./pages/Data.jsx";
import Privacy from "./pages/Privacy.jsx";

function currentTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export default function App() {
  const location = useLocation();
  const [theme, setTheme] = useState(currentTheme);

  const toggleTheme = useCallback(() => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("helix-theme", next); } catch (e) { /* ignore */ }
    setTheme(next);
  }, []);

  // scroll to top and run the scroll-reveal on every route change
  useEffect(() => {
    window.scrollTo(0, 0);
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion:reduce)").matches) {
      els.forEach((e) => e.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, [location.pathname]);

  return (
    <>
      <Nav theme={theme} onToggleTheme={toggleTheme} />
      <main>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/methods" element={<Methods />} />
          <Route path="/pathways" element={<Pathways />} />
          <Route path="/data" element={<Data />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="*" element={<Overview />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
