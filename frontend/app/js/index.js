document.getElementById("themeToggleBtn").addEventListener("click", () => {
  const root = document.documentElement;
  const current = root.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  document.getElementById("themeToggleBtn").textContent = next === "dark" ? "Dark" : "Light";
});

async function submitToAPI() {
  const questionsFile = document.getElementById("questionsFile").files[0];
  const dataFile = document.getElementById("dataFile").files[0];
  const imageFile = document.getElementById("imageFile").files[0];
  const loader = document.getElementById("loader");
  const jsonResponse = document.getElementById("jsonResponse");
  const scatterPlot = document.getElementById("scatterPlot");

  if (!questionsFile) {
    alert("Please upload a .txt file with your question.");
    return;
  }

  const formData = new FormData();
  formData.append("questions", questionsFile);

  if (dataFile) formData.append("data", dataFile);
  if (imageFile) formData.append("image", imageFile);

  loader.style.display = "block";
  jsonResponse.textContent = "";
  scatterPlot.style.display = "none";
  scatterPlot.src = "";

  try {
    const response = await fetch("http://localhost:8000/api/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    loader.style.display = "none";

    if (data.plot_code && data.plot_code.startsWith("data:image/png;base64,")) {
      scatterPlot.src = data.plot_code;
      scatterPlot.style.display = "block";
    }

    jsonResponse.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    loader.style.display = "none";
    jsonResponse.textContent = "Error: " + err.message;
  }
}
