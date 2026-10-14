import "./styles/Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <a className="brand" href="/">
        <span className="brand-icon">
          <span className="brand-letter">F</span>
          <span className="brand-glow" />
        </span>

        <span className="brand-name">
          DataClean<span className="brand-muted"> Studio</span>
        </span>
      </a>

      <div className="navbar-right">
        <div className="api-status">
          <span className="status-dot" />
          <span>CSV Workspace</span>
        </div>
      </div>
    </nav>
  );
}