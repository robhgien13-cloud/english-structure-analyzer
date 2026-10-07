const button = document.getElementById("analyzeButton");
const textarea = document.getElementById("sentence");
const status = document.getElementById("status");
const result = document.getElementById("result");

button.addEventListener("click", async () => {
  const text = textarea.value.trim();

  if (!text) {
    status.textContent = "英文を入力してください。";
    result.innerHTML = "";
    return;
  }

  button.disabled = true;
  status.textContent = "解析中...";
  result.innerHTML = "";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "解析に失敗しました。");
    }

    status.textContent = "解析完了";

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(data, null, 2);
    result.appendChild(pre);

  } catch (error) {
    status.textContent = "エラー";
    result.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
