const form = document.getElementById("analyze-form");
const sentenceInput = document.getElementById("sentence");
const statusBox = document.getElementById("status");
const resultBox = document.getElementById("result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const sentence = sentenceInput.value.trim();

  if (!sentence) {
    statusBox.textContent = "英文を入力してください。";
    return;
  }

  statusBox.textContent = "解析中...";
  resultBox.innerHTML = "";

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ sentence })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "解析に失敗しました。");
    }

    statusBox.textContent = "解析完了";

    resultBox.innerHTML = `
      <h3>解析結果</h3>
      <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
    `;

  } catch (error) {
    statusBox.textContent = "エラー";
    resultBox.innerHTML = `
      <p>${escapeHtml(error.message)}</p>
    `;
  }
});

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot
