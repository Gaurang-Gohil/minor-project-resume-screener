// ShowTable.js
import React, { useState, useEffect } from "react";

const tableStyles = {
  width: "90%",
  borderCollapse: "separate",
  borderSpacing: 0,
  background: "#282A36",
  borderRadius: "8px",
  overflow: "hidden",
  boxShadow: "0 2px 8px rgba(0,0,0,0.09)",
  margin: "auto",
  border: "5px solid rgba(0, 51, 255, 0.45)",
};

const thStyles = {
  background: "#44475a",
  color: "#fff",
  padding: "12px 10px",
  fontWeight: "600",
  borderBottom: "2px solid #6272a4",
};

const tdStyles = {
  padding: "10px",
  borderBottom: "1px solid #44475a",
  color: "#F8F8F2",
  fontWeight: "400",
};

const trHover = {
  background: "#343746",
};

function ShowTable({ taskId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    setError(null);

    fetch(`http://127.0.0.1:8000/api/scoring/results/${taskId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch results");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [taskId]);

  if (!taskId) return <div>No task selected.</div>;
  if (loading) return <div>Loading results...</div>;
  if (error) return <div style={{ color: "red" }}>Error: {error}</div>;

  const candidates = data?.candidates || [];
  if (candidates.length === 0) return <div>No candidates found.</div>;

  return (
    <div style={{ marginTop: "2em" }}>
      {/* <h3 style={{ color: "#f8f8f2", marginBottom: "0.5em" }}>
        Results for Task: <span style={{ color: "#50fa7b" }}>{taskId}</span>
      </h3> */}
      <table style={tableStyles}>
        <thead>
          <tr style={{}}>
            <th style={thStyles}>Filename</th>
            <th style={thStyles}>Match Score</th>
            <th style={thStyles}>Skill Match</th>
            <th style={thStyles}>Experience Match</th>
            <th style={thStyles}>Education Match</th>
            <th style={thStyles}>Skillset</th>
            <th style={thStyles}>Overall Fit</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((cand, idx) => (
            
            <tr
              key={cand.filename || idx}
              style={{
                transition: "background 0.2s",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "#343746"}
              onMouseLeave={e => e.currentTarget.style.background = ""}
            >
              <td style={tdStyles}>{cand.filename}</td>
              <td style={tdStyles}>{cand.detailed_scores?.match_score}</td>
              <td style={tdStyles}>{cand.detailed_scores?.skill_match_score}</td>
              <td style={tdStyles}>{cand.detailed_scores?.experience_match_score}</td>
              <td style={tdStyles}>{cand.detailed_scores?.education_match_score}</td>
              <td style={tdStyles}>
                {Array.isArray(cand.detailed_scores?.skillset_for_role)
                  ? cand.detailed_scores.skillset_for_role.join(", ")
                  : ""}
              </td>
              <td style={tdStyles}>{cand.detailed_scores?.overall_fit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ShowTable;
