import React, { useState } from "react";
import Header from "./components/Header";
import FileUpload from "./components/FileUpload";
import JobDescriptionInput from "./components/JobDescriptionInput";
import ExecuteButton from "./components/ExecuteButton";
// Correcting the import path to match the component we've been working on
import ShowStatus from "./components/DisplayResult"; 
import "./App.css"; 

function App() {
  // State for the user inputs
  const [files, setFiles] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  
  // State to hold the process ID received from the backend
  const [processId, setProcessId] = useState(null);

  // This function is passed to ExecuteButton.
  // It receives the ID from the backend and updates our state.
  const handleProcessStart = (id) => {
    console.log("Process started in App.js with ID:", id);
    setProcessId(id);
  };

  // The old frontend processing logic (handleProcess) has been removed,
  // as this is now handled by your backend.

  return (
    <div className="App">
      <Header />
      <JobDescriptionInput
        value={jobDescription}
        onChange={setJobDescription}
      />
      <FileUpload files={files} setFiles={setFiles} />
      
      {/* ExecuteButton now triggers the backend process and calls handleProcessStart */}
      <ExecuteButton
        files={files}
        jobDescription={jobDescription}
        onProcessStart={handleProcessStart}
      />
      
      {/* ShowStatus receives the processId and will start polling for results */}
      <ShowStatus processId={processId} />
      
      {/* The old ResultTable is removed because ShowStatus now handles displaying results.
          You can move table-like formatting into the ShowStatus component if desired. */}
    </div>
  );
}

export default App;
