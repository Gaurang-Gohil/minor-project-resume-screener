// Calls backend to extract skills from job description
export const extractSkillsFromJD = async (jobDescription) => {
  const response = await fetch("http://localhost:5000/api/extract-skills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: jobDescription }),
  });

  const data = await response.json();
  return data.skills || [];
};
