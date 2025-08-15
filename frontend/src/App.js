import React, { useState } from "react";
import Header from "./components/Header";
import FileUpload from "./components/FileUpload";
import JobDescriptionInput from "./components/JobDescriptionInput";
import ExecuteButton from "./components/ExecuteButton";
import ShowStatus from "./components/DisplayStatus";
import ShowTable from "./components/ShowTable";
import "./App.css";

function App() {
  // State for the user inputs
  const [files, setFiles] = useState([]);
  const [jobDescription, setJobDescription] = useState("");

  // State to hold the process ID received from the backend
  const [processId, setProcessId] = useState(null);

  // State to hold current processing status
  const [status, setStatus] = useState(null);

  // This function is passed to ExecuteButton.
  // It receives the ID from the backend and updates our state.
  const handleProcessStart = (id) => {
    console.log("Process started in App.js with ID:", id);
    setProcessId(id);
    setStatus("processing"); // Initialize status when processing starts
  };

  // This function is passed to ShowStatus to get status updates
  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
  };

  return (
    <div className="App">
      <Header />
      <JobDescriptionInput
        value={jobDescription}
        onChange={setJobDescription}
      />
      <FileUpload files={files} setFiles={setFiles} />

      {/* ExecuteButton triggers the backend process and calls handleProcessStart */}
      <ExecuteButton
        files={files}
        jobDescription={jobDescription}
        onProcessStart={handleProcessStart}
      />

      {/* ShowStatus receives the processId and notifies App of status changes */}
      {processId && (
        <ShowStatus processId={processId} onStatusChange={handleStatusChange} />
      )}

      {/* ShowTable only renders when processing is complete */}
      {status === "completed" && <ShowTable taskId={processId} />}
    </div>
  );
}

export default App;
