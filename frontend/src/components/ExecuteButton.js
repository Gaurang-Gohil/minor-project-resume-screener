import React, { useState } from 'react';

const ExecuteButton = ({ files, jobDescription, onProcessStart }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleClick = async () => {
    // Frontend validation checks
    if (!files || files.length === 0) {
      alert("Please upload at least one resume.");
      return;
    }
    if (!jobDescription || jobDescription.trim() === "") {
      alert("Please enter a job description.");
      return;
    }

    setIsProcessing(true); // Indicate that processing has started (for UI feedback)

    try {
      // Create FormData object to send files and text data
      const formData = new FormData();
      
      // Append job description with the key expected by the backend
      formData.append('job_description', jobDescription); 
      
      // Append each file with the key expected by the backend
      // (Corrected from 'resumes' to 'files')
      files.forEach(file => {
        formData.append('files', file); 
      });

      // Define the base URL for your backend API
      const baseUrl = 'http://127.0.0.1:8000'; // Ensure this matches your backend's host and port

      // Make the POST request to the backend
      const response = await fetch(`${baseUrl}/api/scoring/process-batch`, {
        method: 'POST',
        body: formData, // FormData automatically sets 'Content-Type: multipart/form-data'
      });

      // Check if the HTTP response was successful (status code 2xx)
      if (!response.ok) {
        // Attempt to parse error details from the backend response
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        
        console.error('Backend HTTP Error Response:', errorData); 
        
        // Throw an error with a message derived from backend details or status text
        throw new Error(errorData.detail?.[0]?.msg || errorData.message || `API call failed with status: ${response.status}`);
      }

      // Parse the JSON response from the backend
      const result = await response.json();
      
      // Log the full JSON response received from the backend for debugging
      console.log("Backend JSON response received:", result); 

      // ************ CRITICAL CORRECTION: Access the correct key for the process ID ************
      // Assuming your backend returns a key named 'task_id' (based on previous logs)
      const receivedProcessId = result.task_id; 

      // Validate if a process ID was received and if onProcessStart is a function
      if (receivedProcessId && typeof onProcessStart === 'function') {
        onProcessStart(receivedProcessId); // Pass the received ID to the parent component
      } else {
        // Provide a more informative error message if ID is missing or callback is invalid
        throw new Error(`Invalid or no 'task_id' received from the server. Response: ${JSON.stringify(result)}`);
      }

    } catch (error) {
      console.error('Error starting the process:', error);
      alert(`Error: ${error.message}`); // Display user-friendly alert
    } finally {
      setIsProcessing(false); // Reset processing state regardless of success or failure
    }
  };

  // Determine if the button should be disabled
  const isDisabled = isProcessing || files.length === 0 || !jobDescription.trim();

  return (
    <div style={{ marginTop: '20px', textAlign: 'center' }}>
      <button
        onClick={handleClick}
        disabled={isDisabled}
        style={{
          padding: '10px 30px',
          backgroundColor: isDisabled ? '#ccc' : '#007bff',
          color: '#fff',
          fontSize: '16px',
          border: 'none',
          borderRadius: '8px',
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.3s ease'
        }}
      >
        {isProcessing ? 'Starting...' : 'Process'}
      </button>
    </div>
  );
};

export default ExecuteButton;