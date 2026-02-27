(function () {
  const content = document.getElementById("content");
  const archivePicker = document.getElementById("archivePicker");
  const dateSelect = document.getElementById("dateSelect");

  let currentTab = "daily";
  let currentLang = "all";
  let currentData = null;
  let archiveData = null;

  function showLoading() {
    content.innerHTML = '<p class="loading">加载中...</p>';
  }

  function renderCards(items) {
    if (!items || !items.length) {
      content.innerHTML = '<p class="loading">暂无数据</p>';
      return;
    }
    content.innerHTML = items
      .map(
        (item) => `
      <article class="card">
        <h3><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.author + "/" + item.name)}</a></h3>
        <div class="meta">⭐ ${item.stars || 0} · 本周期 +${item.currentPeriodStars || 0}</div>
        <div class="summary">${escapeHtml(item.summary_zh || item.description || "")}</div>
        ${item.tech_stack ? `<div class="tech"><strong>技术栈：</strong>${escapeHtml(item.tech_stack)}</div>` : ""}
        ${item.why_hot ? `<div class="why"><strong>为什么火：</strong>${escapeHtml(item.why_hot)}</div>` : ""}
      </article>
    `
      )
      .join("");
  }

  function escapeHtml(s) {
    if (!s) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function getItems() {
    if (!currentData) return [];
    const period = currentTab === "archive" ? "daily" : currentTab;
    const byLang = currentData[period] || {};
    let items = byLang[currentLang] || byLang.all || [];
    return items;
  }

  function refresh() {
    const items = getItems();
    renderCards(items);
  }

  function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelector(`.tab[data-tab="${tab}"]`)?.classList.add("active");

    if (tab === "archive") {
      archivePicker.style.display = "block";
      loadArchiveDates();
    } else {
      archivePicker.style.display = "none";
      currentData = null;
      fetchData();
    }
  }

  function switchLang(lang) {
    currentLang = lang;
    document.querySelectorAll(".lang-tab").forEach((b) => b.classList.remove("active"));
    const btn = document.querySelector(`.lang-tab[data-lang="${lang}"]`);
    if (btn) btn.classList.add("active");
    refresh();
  }

  async function fetchData() {
    showLoading();
    try {
      const res = await fetch("data/today.json");
      currentData = await res.json();
      refresh();
    } catch (e) {
      content.innerHTML = '<p class="loading">加载失败，请稍后重试</p>';
    }
  }

  async function loadArchiveDates() {
    try {
      const res = await fetch("data/archive-index.json");
      const index = await res.json();
      const dates = index.dates || [];
      dateSelect.innerHTML = dates.map((d) => `<option value="${d}">${d}</option>`).join("");
      if (dates.length) {
        await loadArchive(dates[0]);
      } else {
        content.innerHTML = '<p class="loading">暂无历史数据</p>';
      }
    } catch (e) {
      content.innerHTML = '<p class="loading">加载历史索引失败</p>';
    }
  }

  async function loadArchive(date) {
    showLoading();
    try {
      const res = await fetch(`data/archive/${date}.json`);
      currentData = await res.json();
      refresh();
    } catch (e) {
      content.innerHTML = '<p class="loading">加载该日期数据失败</p>';
    }
  }

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  document.querySelectorAll(".lang-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchLang(btn.dataset.lang));
  });

  dateSelect.addEventListener("change", () => loadArchive(dateSelect.value));

  if (currentTab !== "archive") {
    fetchData();
  }
})();
