import React from 'react';

function ResultTable({ results }) {
  return (
    <div style={{ marginTop: "30px" }}>
   <h2 className="section-title">Screening Results</h2>

      <table className="result-table">

        <thead>
          <tr>
            <th>Candidate Name</th>
            <th>Match Score (%)</th>
            <th>Matched Skills</th>
          </tr>
        </thead>
        <tbody>
          {results.map((res, index) => (
  <tr key={index}>
    <td>{res.name}</td>
    <td>{res.score}</td>
    <td>
      {Array.isArray(res.matchedSkills)
        ? res.matchedSkills.join(", ")
        : res.matchedSkills}
    </td>
  </tr>
))}

        
        </tbody>
      </table>
    </div>
  );
}

export default ResultTable;
