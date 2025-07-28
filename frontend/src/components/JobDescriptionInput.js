import React from 'react';
import '../App.css'; // optional if not already globally imported in App.js

const JobDescriptionInput = ({ value, onChange }) => {
  const handleChange = (e) => {
    onChange(e.target.value);
  };

  return (
   <div className="jd-section">
  <h2 className="section-title">Job Title</h2>
  <textarea
    className="jd-textarea"
    value={value}
    onChange={handleChange}
    placeholder="Enter job description here..."
    rows={1}
  />
</div>

  );
};

export default JobDescriptionInput;
