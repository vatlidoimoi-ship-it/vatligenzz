const urlInput = document.getElementById("siteUrl");
const copyBtn = document.getElementById("copyUrlBtn");
const copyState = document.getElementById("copyState");
const liveUrls = document.querySelectorAll(".live-url");
const tabButtons = document.querySelectorAll(".tab-btn");
const panels = document.querySelectorAll(".guide-panel");

function normalizedUrl() {
  const value = urlInput.value.trim();
  return value || "https://ten-mien-cua-ban.com";
}

function syncUrls() {
  const value = normalizedUrl();
  liveUrls.forEach((node) => {
    node.textContent = value;
  });
}

urlInput.addEventListener("input", syncUrls);
syncUrls();

copyBtn.addEventListener("click", async () => {
  const value = normalizedUrl();
  try {
    await navigator.clipboard.writeText(value);
    copyState.textContent = "Đã sao chép link.";
  } catch (error) {
    urlInput.select();
    copyState.textContent = "Hãy nhấn Ctrl + C để sao chép link.";
  }
});

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const device = button.dataset.device;
    tabButtons.forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", active ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.panel === device);
    });
  });
});
