import React from 'react';

const ExecuteButton = ({ files, jobDescription, onProcess }) => {
  const handleClick = () => {
    if (!files || files.length === 0) {
      alert("Please upload at least one resume.");
      return;
    }

    if (!jobDescription || jobDescription.trim() === "") {
      alert("Please enter a job description.");
      return;
    }

    // Trigger the process function from App.js
    if (typeof onProcess === 'function') {
      onProcess();
    } else {
      console.warn("onProcess is not a function.");
    }
  };

  return (
    <div style={{ marginTop: '20px', textAlign: 'center' }}>
      <button
        onClick={handleClick}
        disabled={files.length === 0 || jobDescription.trim() === ""}

        style={{
          padding: '10px 30px',
          backgroundColor: files.length === 0 ? '#ccc' : '#007bff',
          color: '#fff',
          fontSize: '16px',
          border: 'none',
          borderRadius: '8px',
          cursor: files.length === 0 ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.3s ease'
        }}
      >
        Process
      </button>
    </div>
  );
};

export default ExecuteButton;
