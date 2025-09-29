document.getElementById("themeToggleBtn").addEventListener("click", () => {
  const root = document.documentElement;
  const current = root.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  document.getElementById("themeToggleBtn").textContent = next === "dark" ? "Dark" : "Light";
});

document.getElementById("questionsFile").addEventListener("change", function () {
  if (this.files.length) {
    console.log("Question file selected:", this.files[0].name);
  }
});

document.getElementById("dataFile").addEventListener("change", function () {
  if (this.files.length) {
    console.log("Data file selected:", this.files[0].name);
  }
});

async function submitToAPI() {
  const questionsFile = document.getElementById("questionsFile").files[0];
  const dataFile = document.getElementById("dataFile").files[0];
  const loader = document.getElementById("loader");
  const jsonResponse = document.getElementById("jsonResponse");
  const scatterPlot = document.getElementById("scatterPlot");

  if (!questionsFile) {
    alert("Please upload a .txt file with your question(s).");
    return;
  }

  const formData = new FormData();
  formData.append("questions_txt", questionsFile);

  if (dataFile) {
    const ext = dataFile.name.split(".").pop().toLowerCase();
    if (ext === "csv") {
      formData.append("data_csv", dataFile);
    } else if (ext === "json") {
      formData.append("data_json", dataFile);
    } else {
      alert("Unsupported data file format. Use .csv or .json");
      return;
    }
  }

  loader.style.display = "block";
  jsonResponse.textContent = "";
  scatterPlot.src = "";
  scatterPlot.style.display = "none";

  try {
    const res = await fetch("http://localhost:8000/api/", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    loader.style.display = "none";

    if (data && typeof data === "object") {
      jsonResponse.textContent = JSON.stringify(data, null, 2);

      const base64Plot = Object.values(data).find(
        v => typeof v === "string" && v.startsWith("data:image/png;base64,")
      );

      if (base64Plot) {
        scatterPlot.src = base64Plot;
        scatterPlot.style.display = "block";
      }
    } else {
      jsonResponse.textContent = "Unexpected response format.";
    }

  } catch (err) {
    loader.style.display = "none";
    jsonResponse.textContent = "❌ Error: " + err.message;
    console.error("Error submitting to API:", err);
  }
}

