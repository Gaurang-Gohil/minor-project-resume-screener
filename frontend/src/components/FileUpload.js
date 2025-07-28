// src/components/FileUpload.js
import React from 'react';
import '../App.css';

const FileUpload = ({ files, setFiles }) => {
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const maxSize = 5 * 1024 * 1024;
    const validFiles = [];

    selectedFiles.forEach((file) => {
      if (file.size > maxSize) {
        alert(`${file.name} is larger than 5MB and was skipped.`);
      } else if (file.type !== 'application/pdf') {
        alert(`${file.name} is not a PDF and was skipped.`);
      } else {
        validFiles.push(file);
      }
    });

    setFiles((prev) => [...prev, ...validFiles]);
  };

  const handleRemoveFile = (indexToRemove) => {
    const updated = files.filter((_, index) => index !== indexToRemove);
    setFiles(updated);
  };

  const handleClearAll = () => {
    setFiles([]);
  };

  return (
    <div className="upload-container container">
      <label className="choose-file">
        Choose File
        <input type="file" multiple accept=".pdf" onChange={handleFileChange} />
      </label>

      <ul className="file-list">
        {files.map((file, index) => (
          <li className="file-item" key={index}>
            <span className="file-index">{index + 1}</span>
            <span className="file-name">{file.name}</span>
            <button className="remove-btn" onClick={() => handleRemoveFile(index)}>✖</button>
          </li>
        ))}
      </ul>

      {files.length > 0 && (
        <button className="clear-all-btn" onClick={handleClearAll}>
          Clear All
        </button>
      )}
    </div>
  );
};

export default FileUpload;
