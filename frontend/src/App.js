import React, { useState } from "react";
import Header from "./components/Header";
import FileUpload from "./components/FileUpload";
import JobDescriptionInput from "./components/JobDescriptionInput";
import ResultTable from "./components/ResultTable";
import ExecuteButton from "./components/ExecuteButton";
import { extractTextFromPDF } from "./utils/pdfParser"; // ✅ PDF-only text extractor
import "./App.css"; // Ensure you import the CSS  
function App() {
  const [files, setFiles] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  const [results, setResults] = useState([]);

  const extractSkillsFromJD = (jd) => {
    return jd
      .toLowerCase()
      .split(/[\s,]+/)
      .filter((word) => word.length > 2);
  };

  const handleProcess = async () => {
    if (!files || files.length === 0) {
      alert("Please upload at least one resume.");
      return;
    }

    if (!jobDescription || jobDescription.trim() === "") {
      alert("Please enter a job description.");
      return;
    }

    const jdSkills = extractSkillsFromJD(jobDescription);

    const fileResults = await Promise.all(
      files.map(async (file) => {
        try {
          const lowerText = await extractTextFromPDF(file); // ✅ PDF-only
          const matched = jdSkills.filter((skill) =>
            lowerText.includes(skill)
          );
          const score = Math.round((matched.length / jdSkills.length) * 100);

          return {
            name: file.name.replace(".pdf", ""),
            score: score || 0,
            matchedSkills: matched,
          };
        } catch (error) {
          console.error(`Failed to process ${file.name}`, error);
          return {
            name: file.name.replace(".pdf", ""),
            score: 0,
            matchedSkills: "Error parsing PDF",
          };
        }
      })
    );

    const sorted = fileResults.sort((a, b) => b.score - a.score);
    setResults(sorted);
  };

  return (
    <div className="App">
      <Header />
      <JobDescriptionInput
        value={jobDescription}
        onChange={setJobDescription}
      />
      <FileUpload files={files} setFiles={setFiles} />
      <ExecuteButton
        files={files}
        jobDescription={jobDescription}
        onProcess={handleProcess}
      />
      <ResultTable results={results} />
    </div>
  );
}

export default App;
