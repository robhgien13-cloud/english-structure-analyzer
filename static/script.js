const button = document.getElementById("analyzeButton");
const textarea = document.getElementById("sentence");
const status = document.getElementById("status");
const result = document.getElementById("result");

const REQUEST_TIMEOUT_MS = 90000;

button.addEventListener("click", async () => {
  const text = textarea.value.trim();

  if (!text) {
    status.textContent = "英文を入力してください。";
    result.replaceChildren();
    return;
  }

  button.disabled = true;
  status.textContent = "解析中...（初回起動時は時間がかかることがあります）";
  result.replaceChildren();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal
    });

    // The server can return an HTML error page on a gateway timeout.
    const raw = await response.text();
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      throw new Error(`サーバーから正常な解析結果が返りませんでした（HTTP ${response.status}）。時間をおいて再試行してください。`);
    }

    if (!response.ok) {
      throw new Error(data.error || `解析に失敗しました（HTTP ${response.status}）。`);
    }

    const count = Array.isArray(data.sentences) ? data.sentences.length : 0;
    status.textContent = `解析完了（${count}文）`;

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(data, null, 2);
    result.appendChild(pre);
  } catch (error) {
    status.textContent = "解析できませんでした";
    result.textContent = error.name === "AbortError"
      ? "解析が90秒以内に完了しませんでした。英文を短くして再試行してください。"
      : error.message;
  } finally {
    clearTimeout(timeoutId);
    button.disabled = false;
  }
});
