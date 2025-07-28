import React, { useState, useEffect } from 'react';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const ShowStatus = ({ processId }) => {
  const [status, setStatus] = useState('Not started');
  const [resultData, setResultData] = useState(null);

  useEffect(() => {
    if (!processId) {
      setStatus('Not started');
      setResultData(null);
      return;
    }

    let isMounted = true; 

    const pollStatus = async () => {
      setStatus('Processing...');
      setResultData(null);

      while (isMounted) {
        try {
          // --- CORRECTED URL AND PARAMETER STYLE ---
          const baseUrl = 'http://127.0.0.1:8000';
          // The ID is now part of the URL path, not a query string like ?id=...
          const response = await fetch(`${baseUrl}/api/scoring/status/${processId}`);
          
          if (!response.ok) {
             await sleep(5000);
             continue;
          }

          const data = await response.json();

          setStatus(data.status);
          
          if (data.result) {
            setResultData(data.result);
          }

          if (data.status === 'complete' || data.status === 'failed') {
            break;
          }

        } catch (error) {
          console.error('Error fetching status:', error);
          setStatus('Error');
          break;
        }

        await sleep(3000);
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
    };
  }, [processId]);

  return (
    <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
      <h3>Process Status</h3>
      <p style={{ fontSize: '18px', fontWeight: 'bold' }}>
        Status: <span style={{ color: '#007bff' }}>{status}</span>
      </p>
      
      {resultData && (
        <div>
          <h4>Live Results:</h4>
          <pre style={{ 
            textAlign: 'left', 
            backgroundColor: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '5px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {JSON.stringify(resultData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ShowStatus;
