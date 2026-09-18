import { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  Loader2,
  MapPin,
  RefreshCw,
  Route,
  ShieldCheck,
  Clock3,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const ISSUE_TYPES = [
  { value: "garbage", label: "Garbage Dumping" },
  {
    value: "construction_waste",
    label: "Construction / Demolition Waste",
  },
  { value: "illegal_dumping", label: "Illegal Dumping" },
  { value: "road_waste", label: "Roadside Waste" },
];

function App() {
  const [page, setPage] = useState("report");

  const [form, setForm] = useState({
    title: "",
    description: "",
    issue_type: "garbage",
    latitude: "12.2958",
    longitude: "76.6394",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateField = (field, value) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const submitComplaint = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/complaints/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...form,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to submit complaint."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the CivicRoute backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setResult(null);
    setError("");
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">
            <Route size={22} />
          </div>

          <div>
            <h1>CivicRoute</h1>
            <span>Mysuru Civic Governance</span>
          </div>
        </div>

        <nav className="nav-links">
          <button
            className={page === "report" ? "active" : ""}
            onClick={() => {
              setPage("report");
              resetForm();
            }}
          >
            <MapPin size={17} />
            Report Issue
          </button>

          <button
            className={page === "dashboard" ? "active" : ""}
            onClick={() => setPage("dashboard")}
          >
            <ClipboardList size={17} />
            Authority Dashboard
          </button>
        </nav>

        <div className="nav-status">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      {page === "report" ? (
        <main className="main-content">
          {!result ? (
            <ReportForm
              form={form}
              updateField={updateField}
              submitComplaint={submitComplaint}
              loading={loading}
              error={error}
            />
          ) : (
            <RoutingResult
              result={result}
              onBack={resetForm}
            />
          )}
        </main>
      ) : (
        <Dashboard />
      )}

      <footer>
        CivicRoute · HackMysuru 1.0 · Civic Governance &
        Clean Mysuru
      </footer>
    </div>
  );
}

function ReportForm({
  form,
  updateField,
  submitComplaint,
  loading,
  error,
}) {
  return (
    <section className="report-layout">
      <div className="intro">
        <div className="eyebrow">
          <MapPin size={16} />
          CIVIC ISSUE REPORTING
        </div>

        <h2>
          Route your complaint to the
          <span> right authority.</span>
        </h2>

        <p>
          Report a civic issue with its location. CivicRoute
          determines the responsible local authority using the
          active jurisdiction boundary.
        </p>

        <div className="feature-list">
          <div>
            <CheckCircle2 size={20} />
            <span>Location-based routing</span>
          </div>

          <div>
            <CheckCircle2 size={20} />
            <span>Boundary version awareness</span>
          </div>

          <div>
            <CheckCircle2 size={20} />
            <span>Duplicate complaint detection</span>
          </div>
        </div>
      </div>

      <form
        className="complaint-card"
        onSubmit={submitComplaint}
      >
        <div className="card-header">
          <div>
            <h3>Report a Civic Issue</h3>
            <p>Provide the issue and its location.</p>
          </div>

          <div className="form-icon">
            <MapPin size={22} />
          </div>
        </div>

        <div className="form-group">
          <label>Issue Type</label>

          <select
            value={form.issue_type}
            onChange={(event) =>
              updateField(
                "issue_type",
                event.target.value
              )
            }
          >
            {ISSUE_TYPES.map((issue) => (
              <option
                key={issue.value}
                value={issue.value}
              >
                {issue.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Complaint Title</label>

          <input
            type="text"
            placeholder="Example: Illegal garbage dumping"
            value={form.title}
            onChange={(event) =>
              updateField("title", event.target.value)
            }
            required
            minLength={3}
          />
        </div>

        <div className="form-group">
          <label>Description</label>

          <textarea
            placeholder="Describe the civic issue..."
            value={form.description}
            onChange={(event) =>
              updateField(
                "description",
                event.target.value
              )
            }
            required
            minLength={5}
            rows={4}
          />
        </div>

        <div className="location-header">
          <label>Complaint Location</label>

          <span>
            <MapPin size={14} />
            GPS Coordinates
          </span>
        </div>

        <div className="coordinates">
          <div className="form-group">
            <label>Latitude</label>

            <input
              type="number"
              step="any"
              value={form.latitude}
              onChange={(event) =>
                updateField(
                  "latitude",
                  event.target.value
                )
              }
              required
            />
          </div>

          <div className="form-group">
            <label>Longitude</label>

            <input
              type="number"
              step="any"
              value={form.longitude}
              onChange={(event) =>
                updateField(
                  "longitude",
                  event.target.value
                )
              }
              required
            />
          </div>
        </div>

        {error && (
          <div className="error-box">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          className="submit-button"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2
                size={19}
                className="spinner"
              />
              Routing Complaint...
            </>
          ) : (
            <>
              <Route size={19} />
              Route Complaint
            </>
          )}
        </button>
      </form>
    </section>
  );
}

function RoutingResult({ result, onBack }) {
  const complaint = result.complaint;
  const routing = result.routing;
  const duplicate = result.duplicate_check;

  if (duplicate?.duplicate) {
    return (
      <section className="result-wrapper">
        <button className="back-button" onClick={onBack}>
          <ArrowLeft size={18} />
          Report another issue
        </button>

        <div className="result-card">
          <div className="result-icon warning">
            <AlertCircle size={30} />
          </div>

          <span className="result-label">
            POSSIBLE DUPLICATE
          </span>

          <h2>Similar complaint already exists</h2>

          <p className="result-description">
            Complaint #{duplicate.existing_complaint_id}
            was found within{" "}
            {duplicate.distance_meters} meters with the
            same issue type.
          </p>

          <div className="info-grid">
            <InfoItem
              label="New Complaint"
              value={`#${complaint.id}`}
            />

            <InfoItem
              label="Existing Complaint"
              value={`#${duplicate.existing_complaint_id}`}
            />

            <InfoItem
              label="Distance"
              value={`${duplicate.distance_meters} m`}
            />

            <InfoItem
              label="Status"
              value="Possible Duplicate"
            />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="result-wrapper">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} />
        Report another issue
      </button>

      <div className="result-card">
        <div className="success-icon">
          <CheckCircle2 size={34} />
        </div>

        <span className="result-label">
          COMPLAINT ROUTED SUCCESSFULLY
        </span>

        <h2>Your complaint has been routed.</h2>

        <p className="result-description">
          CivicRoute analyzed the complaint location and
          identified the responsible authority.
        </p>

        {routing ? (
          <>
            <div className="authority-box">
              <span>RESPONSIBLE AUTHORITY</span>
              <strong>{routing.authority}</strong>
              <small>{routing.authority_type}</small>
            </div>

            <div className="info-grid">
              <InfoItem
                label="Complaint ID"
                value={`#${complaint.id}`}
              />

              <InfoItem
                label="Jurisdiction"
                value={routing.jurisdiction}
              />

              <InfoItem
                label="Boundary Version"
                value={routing.boundary_version}
              />

              <InfoItem
                label="Confidence"
                value={`${Math.round(
                  routing.confidence * 100
                )}%`}
              />
            </div>

            <div className="reason-box">
              <div className="reason-title">
                <Route size={18} />
                Why was this routed here?
              </div>

              <p>{routing.reason}</p>
            </div>
          </>
        ) : (
          <div className="error-box">
            <AlertCircle size={18} />
            <span>
              Complaint saved, but no jurisdiction could
              be determined.
            </span>
          </div>
        )}
      </div>
    </section>
  );
}

function Dashboard() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchComplaints = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/complaints/`
      );

      if (!response.ok) {
        throw new Error("Failed to load complaints.");
      }

      const data = await response.json();

      setComplaints(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const updateStatus = async (id, status) => {
    try {
      const response = await fetch(
        `${API_URL}/api/complaints/${id}/status?status=${status}`,
        {
          method: "PATCH",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update status.");
      }

      await fetchComplaints();
    } catch (err) {
      setError(err.message);
    }
  };

  const total = complaints.length;

  const routed = complaints.filter(
    (item) => item.status === "routed"
  ).length;

  const inProgress = complaints.filter(
    (item) => item.status === "in_progress"
  ).length;

  const resolved = complaints.filter(
    (item) => item.status === "resolved"
  ).length;

  return (
    <main className="dashboard">
      <div className="dashboard-header">
        <div>
          <div className="eyebrow">
            <ShieldCheck size={16} />
            AUTHORITY WORKSPACE
          </div>

          <h2>Complaint Dashboard</h2>

          <p>
            Monitor and act on civic complaints routed to
            local authorities.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={fetchComplaints}
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      <div className="stats-grid">
        <StatCard
          icon={<ClipboardList size={21} />}
          label="Total Complaints"
          value={total}
        />

        <StatCard
          icon={<Route size={21} />}
          label="Routed"
          value={routed}
        />

        <StatCard
          icon={<Clock3 size={21} />}
          label="In Progress"
          value={inProgress}
        />

        <StatCard
          icon={<CheckCircle2 size={21} />}
          label="Resolved"
          value={resolved}
        />
      </div>

      {error && (
        <div className="error-box dashboard-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="complaints-section">
        <div className="section-header">
          <div>
            <h3>Incoming Complaints</h3>
            <p>Latest reports received by the system.</p>
          </div>

          <span className="complaint-count">
            {total} reports
          </span>
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader2 className="spinner" size={28} />
            Loading complaints...
          </div>
        ) : complaints.length === 0 ? (
          <div className="empty-state">
            <ClipboardList size={35} />
            <h3>No complaints yet</h3>
            <p>
              New citizen complaints will appear here.
            </p>
          </div>
        ) : (
          <div className="complaint-list">
            {complaints.map((complaint) => (
              <ComplaintRow
                key={complaint.id}
                complaint={complaint}
                updateStatus={updateStatus}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function ComplaintRow({ complaint, updateStatus }) {
  const routing = complaint.routing;

  return (
    <article className="complaint-row">
      <div className="complaint-main">
        <div className="complaint-number">
          #{complaint.id}
        </div>

        <div className="complaint-content">
          <div className="complaint-title-row">
            <h4>{complaint.title}</h4>
            <StatusBadge status={complaint.status} />
          </div>

          <p>{complaint.description}</p>

          <div className="complaint-meta">
            <span>
              <MapPin size={14} />
              {complaint.latitude.toFixed(4)},{" "}
              {complaint.longitude.toFixed(4)}
            </span>

            <span>
              Issue: {complaint.issue_type}
            </span>
          </div>
        </div>
      </div>

      <div className="routing-summary">
        {routing ? (
          <>
            <span>ROUTED TO</span>
            <strong>{routing.authority}</strong>
            <small>{routing.jurisdiction}</small>
          </>
        ) : (
          <>
            <span>ROUTING</span>
            <strong>Not determined</strong>
          </>
        )}
      </div>

      <div className="action-area">
        {complaint.status === "routed" && (
          <button
            className="action-button"
            onClick={() =>
              updateStatus(
                complaint.id,
                "in_progress"
              )
            }
          >
            Start Work
          </button>
        )}

        {complaint.status === "in_progress" && (
          <button
            className="action-button resolve"
            onClick={() =>
              updateStatus(
                complaint.id,
                "resolved"
              )
            }
          >
            Mark Resolved
          </button>
        )}

        {complaint.status === "resolved" && (
          <span className="resolved-label">
            <CheckCircle2 size={16} />
            Resolved
          </span>
        )}
      </div>
    </article>
  );
}

function StatusBadge({ status }) {
  const labels = {
    submitted: "Submitted",
    routed: "Routed",
    possible_duplicate: "Possible Duplicate",
    in_progress: "In Progress",
    resolved: "Resolved",
  };

  return (
    <span className={`status-badge ${status}`}>
      {labels[status] || status}
    </span>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div className="info-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;