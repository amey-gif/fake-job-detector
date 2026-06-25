window.onload = () =>{
  document.getElementById("status").textContent = "";
  document.getElementById("result").innerHTML = "";
}

const API_URL = "https://fake-job-detector-4sx2.onrender.com/predict";

document.getElementById("scanBtn").addEventListener("click", async () => {
  const status = document.getElementById("status");
  const result = document.getElementById("result");

  status.textContent = "Scanning...";
  result.innerHTML = "";

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, { action: "extractJob" }, async (jobData) => {
    if (!jobData) {
      status.textContent = "Could not extract job data from this page.";
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jobData)
      });

      const data = await response.json();
      status.textContent = "";

      const verdictClass = data.verdict === "FAKE" ? "fake" : "real";

      let html = `<p class="${verdictClass}">${data.verdict} — ${(data.fake_probability * 100).toFixed(1)}% fake probability</p>`;
      html += `<p style="font-size:12px;margin:8px 0 4px;">Top reasons:</p>`;

      data.top_reasons.forEach(r => {
        const direction = r.impact > 0 ? "fake signal" : "real signal";
        html += `<div class="reason">• ${r.feature} — ${direction}</div>`;
      });

      result.innerHTML = html;
    } catch (err) {
      status.textContent = "API error. Try again.";
    }
  });
});