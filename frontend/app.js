const API = "https://smart-study-planner-2-oub2.onrender.com";
const sections = ["loginSection", "goalSection", "detailsSection", "planSection", "pyqSection"];
let user = null;
let selectedGoal = "";
let selectedSubjectId = null;
let selectedSubjectName = "";

function showSection(sectionId) {
  sections.forEach(id => document.getElementById(id).classList.toggle("hidden", id !== sectionId));
  const active = {
    loginSection: 1, goalSection: 2, detailsSection: 3, planSection: 4, pyqSection: 4
  }[sectionId];
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`step${i}`).classList.toggle("active", i === active);
  }
  showNotice("");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showNotice(message, isError = false) {
  const notice = document.getElementById("notice");
  notice.textContent = message;
  notice.classList.toggle("hidden", !message);
  notice.classList.toggle("error-notice", isError);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Something went wrong. Please try again.");
  return data;
}

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  try {
    user = await apiRequest("/api/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    showSection("goalSection");
    showNotice(`Welcome, ${user.email}.`);
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelectorAll("[data-goal]").forEach(button => {
  button.addEventListener("click", () => {
    selectedGoal = button.dataset.goal;
    document.querySelectorAll("[data-goal]").forEach(item => item.classList.toggle("selected", item === button));
    document.getElementById("goalError").textContent = "";
  });
});

document.getElementById("toDetails").addEventListener("click", () => {
  if (!selectedGoal) {
    document.getElementById("goalError").textContent = "Please select one goal to continue.";
    return;
  }
  showSection("detailsSection");
});

document.getElementById("detailsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!user) {
    showSection("loginSection");
    return;
  }
  const details = {
    user_id: user.user_id,
    goal: selectedGoal,
    academic_year: document.getElementById("academicYear").value,
    branch: document.getElementById("branch").value,
    semester: document.getElementById("semester").value
  };
  try {
    const result = await apiRequest("/api/plan", {
      method: "POST",
      body: JSON.stringify(details)
    });
    document.getElementById("planSummary").innerHTML = `
      <strong>Goal:</strong> ${escapeHtml(result.goal)}<br>
      <strong>Academic year:</strong> ${escapeHtml(result.academic_year)}<br>
      <strong>Branch:</strong> ${escapeHtml(result.branch)}<br>
      <strong>Semester:</strong> ${escapeHtml(result.semester)}
    `;
    document.getElementById("planList").innerHTML = result.plan_text.split("\n")
      .map(line => `<li>${escapeHtml(line.replace(/^\d+\.\s*/, ""))}</li>`).join("");
    await loadSubjects(details.branch, details.semester);
    showSection("planSection");
  } catch (error) {
    showNotice(error.message, true);
  }
});

async function loadSubjects(branch, semester) {
  const select = document.getElementById("subjectSelect");
  select.innerHTML = '<option value="">Loading subjects…</option>';
  try {
    const data = await apiRequest(`/api/subjects?branch=${encodeURIComponent(branch)}&semester=${encodeURIComponent(semester)}`);
    select.innerHTML = "";
    if (!data.subjects.length) {
      select.innerHTML = '<option value="">No sample subjects available</option>';
      return;
    }
    data.subjects.forEach(subject => {
      const option = document.createElement("option");
      option.value = subject.id;
      option.textContent = subject.name;
      select.appendChild(option);
    });
  } catch (error) {
    select.innerHTML = '<option value="">Could not load subjects</option>';
    showNotice(error.message, true);
  }
}

document.getElementById("openSubject").addEventListener("click", () => {
  const select = document.getElementById("subjectSelect");
  if (!select.value) {
    showNotice("Please select a subject first.", true);
    return;
  }
  selectedSubjectId = select.value;
  selectedSubjectName = select.options[select.selectedIndex].text;
  document.getElementById("subjectHeading").textContent = selectedSubjectName;
  document.getElementById("subjectContent").innerHTML = "";
  showSection("pyqSection");
});

document.getElementById("combinedBtn").addEventListener("click", () => loadContent("combined"));
document.getElementById("unitwiseBtn").addEventListener("click", () => loadContent("unitwise"));

async function loadContent(mode) {
  if (!selectedSubjectId) return;
  try {
    const data = await apiRequest(`/api/subjects/${selectedSubjectId}/pyq?mode=${mode}`);
    const container = document.getElementById("subjectContent");
    if (mode === "combined") {
      container.innerHTML = `<h3>Combined PYQ / Important Questions</h3>` +
        data.questions.map((item, index) =>
          `<div class="unit-card"><strong>Q${index + 1}.</strong> ${escapeHtml(item.question)}<p class="muted">From: ${escapeHtml(item.unit_name)}</p></div>`
        ).join("");
    } else {
      container.innerHTML = `<h3>Unit-wise weightage and important questions</h3>` +
        data.units.map(unit => `
          <article class="unit-card">
            <div class="unit-top"><h3>${escapeHtml(unit.unit_name)}</h3><span class="weight">${escapeHtml(unit.weightage)}</span></div>
            <ol>${unit.important_questions.split("\n").map(q => `<li>${escapeHtml(q.replace(/^\d+\.\s*/, ""))}</li>`).join("")}</ol>
          </article>
        `).join("");
    }
    showNotice(mode === "combined" ? "Showing combined sample questions." : "Showing unit-wise sample content.");
  } catch (error) {
    showNotice(error.message, true);
  }
}

document.querySelectorAll("[data-back]").forEach(button => {
  button.addEventListener("click", () => showSection(button.dataset.back));
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[character]));
}
