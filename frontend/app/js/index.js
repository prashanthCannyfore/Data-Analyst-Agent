// document.getElementById("themeToggleBtn").addEventListener("click", () => {
//   const root = document.documentElement;
//   const current = root.getAttribute("data-theme");
//   const next = current === "dark" ? "light" : "dark";
//   root.setAttribute("data-theme", next);
//   document.getElementById("themeToggleBtn").textContent = next === "dark" ? "Dark" : "Light";
// });

// async function submitToAPI() {
//   const questionsFile = document.getElementById("questionsFile").files[0];
//   const dataFile = document.getElementById("dataFile").files[0];
//   const imageFile = document.getElementById("imageFile").files[0];
//   const loader = document.getElementById("loader");
//   const jsonResponse = document.getElementById("jsonResponse");
//   const scatterPlot = document.getElementById("scatterPlot");

//   if (!questionsFile) {
//     alert("Please upload a .txt file with your question.");
//     return;
//   }

//   const formData = new FormData();
//   formData.append("questions", questionsFile);

//   if (dataFile) formData.append("data", dataFile);
//   if (imageFile) formData.append("image", imageFile);

//   loader.style.display = "block";
//   jsonResponse.textContent = "";
//   scatterPlot.style.display = "none";
//   scatterPlot.src = "";

//   try {
//     const response = await fetch("http://localhost:8000/api/", {
//       method: "POST",
//       body: formData,
//     });

//     const data = await response.json();
//     loader.style.display = "none";

//     if (data.plot_code && data.plot_code.startsWith("data:image/png;base64,")) {
//       scatterPlot.src = data.plot_code;
//       scatterPlot.style.display = "block";
//     }

//     jsonResponse.textContent = JSON.stringify(data, null, 2);
//   } catch (err) {
//     loader.style.display = "none";
//     jsonResponse.textContent = "Error: " + err.message;
//   }
// }
// Toggle between light and dark mode
document.getElementById("themeToggleBtn").addEventListener("click", () => {
  const root = document.documentElement;
  const current = root.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  document.getElementById("themeToggleBtn").textContent = next === "dark" ? "Dark" : "Light";
});

// Submit files and send request to FastAPI
async function submitToAPI() {
  const questionsFile = document.getElementById("questionsFile").files[0];
  const dataFile = document.getElementById("dataFile").files[0];
  const imageFile = document.getElementById("imageFile").files[0];
  const loader = document.getElementById("loader");
  const jsonResponse = document.getElementById("jsonResponse");
  const scatterPlot = document.getElementById("scatterPlot");

  // Validate input
  if (!questionsFile) {
    alert("Please upload a .txt file with your question.");
    return;
  }

  // Prepare form data
  const formData = new FormData();
  formData.append("questions", questionsFile);
  if (dataFile) formData.append("data", dataFile);
  if (imageFile) formData.append("image", imageFile);

  // Show loader and reset UI
  loader.style.display = "block";
  jsonResponse.textContent = "";
  scatterPlot.style.display = "none";
  scatterPlot.src = "";

  try {
    // Replace with your actual ngrok URL
    const apiURL = "https://blakely-estimative-nonarbitrarily.ngrok-free.dev/api/";

    const response = await fetch(apiURL, {
      method: "POST",
      body: formData,
    });

    // Check response status
    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data = await response.json();
    loader.style.display = "none";

    // Show plot if present
    if (data.plot_code && data.plot_code.startsWith("data:image/png;base64,")) {
      scatterPlot.src = data.plot_code;
      scatterPlot.style.display = "block";
    }

    // Show JSON response
    jsonResponse.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    loader.style.display = "none";
    jsonResponse.textContent = "Error: " + err.message;
    console.error("API error:", err);
  }
}
