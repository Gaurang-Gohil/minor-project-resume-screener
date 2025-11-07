import React, { useState, useEffect } from "react";
import "./StatusDisplay.css"; // import your new CSS
import Loader from "./animation/loader";

const sleep = ms => new Promise(res => setTimeout(res, ms));

const statusLabelClass = status => {
  if (status === "completed") return "status-label completed";
  if (status === "failed" || status === "error") return "status-label failed";
  return "status-label";
};

const DisplayStatus = ({ processId, onStatusChange }) => {
  const [status, setStatus] = useState("Not started");
  const [resultData, setResultData] = useState(null);

  useEffect(() => {
    if (!processId) {
      setStatus("Not started");
      setResultData(null);
      if (onStatusChange) onStatusChange("not_started");
      return;
    }

    let isMounted = true;

    const pollStatus = async () => {
      setStatus("Processing...");
      setResultData(null);
      if (onStatusChange) onStatusChange("processing");

      while (isMounted) {
        try {
          const baseUrl = "http://127.0.0.1:8000";
          const response = await fetch(`${baseUrl}/api/scoring/status/${processId}`);

          if (!response.ok) {
            await sleep(5000);
            continue;
          }

          const data = await response.json();
          setStatus(data.status);
          if (onStatusChange) onStatusChange(data.status);

          if (data.result) setResultData(data.result);
          if (data.status === "completed" || data.status === "failed") break;
        } catch (error) {
          console.error("Error fetching status:", error);
          setStatus("Error");
          if (onStatusChange) onStatusChange("error");
          break;
        }
        await sleep(3000);
      }
    };

    pollStatus();
    return () => { isMounted = false; };
  }, [processId, onStatusChange]);

  return (
    <div className="status-container">
      <span className={statusLabelClass(status)}>
        {status === "completed"
          ? "✔️ Completed"
          : status === "processing"
          ? `${Loader}`
          : status === "failed"
          ? "❌ Failed"
          : status === "error"
          ? "⚠️ Error"
          : "⏳ " + status}
      </span>
    </div>
  );
};

export default DisplayStatus;
