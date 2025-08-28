let questions = [];
let currentQuestion = 0;
let selectedAnswers = {};
let lockedQuestions = new Set();
let questionStates = [];

const timerDuration = 60 * 10;
let timeLeft = timerDuration;

async function loadExcelFromServer() {
  try {
    const res = await fetch("/static/questions.xlsx");
    if (!res.ok) throw new Error("Failed to load Excel file");

    const buffer = await res.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: "array" });
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    questions = XLSX.utils.sheet_to_json(sheet, { header: 1 });

    questions = questions.filter(row => row.length >= 6);
    questionStates = Array(questions.length).fill("gray");
    renderSidebar();
    loadQuestion(0);
  } catch (err) {
    console.error("Error loading questions.xlsx:", err);
    alert("Failed to load questions.");
  }
}

function renderSidebar() {
  const list = document.getElementById("question-list");
  list.innerHTML = "";

  questions.forEach((_, i) => {
    const btn = document.createElement("button");
    btn.textContent = `${i + 1}`;
    btn.className = `sidebar-btn ${questionStates[i]}`;
    btn.onclick = () => {
      if (!lockedQuestions.has(i)) loadQuestion(i);
    };
    list.appendChild(btn);
  });
}

function loadQuestion(index) {
  currentQuestion = index;
  const examBox = document.querySelector(".exam-box");

if (lockedQuestions.has(index)) {
  examBox.classList.add("locked");
} else {
  examBox.classList.remove("locked");
}

  const q = questions[index];
  if (!q || q.length < 6) return;

  document.getElementById("question-number").textContent = `Question ${index + 1} of ${questions.length}`;

  const qText = document.getElementById("question-text");
  qText.style.animation = "none";
  qText.offsetHeight;
  qText.textContent = q[0];
  qText.style.animation = "scrollLeftToRight 15s linear infinite";

  document.getElementById("optA").textContent = q[1];
  document.getElementById("optB").textContent = q[2];
  document.getElementById("optC").textContent = q[3];
  document.getElementById("optD").textContent = q[4];

  document.querySelectorAll("input[name='option']").forEach((input) => {
    input.disabled = lockedQuestions.has(index);
    input.checked = selectedAnswers[index] === input.value;
    input.onclick = () => {
      selectedAnswers[index] = input.value;
      questionStates[index] = "green";
      renderSidebar();
    };
  });

  if (questionStates[index] === "gray") {
    questionStates[index] = "red";
  }

  renderSidebar();
}

document.getElementById("nextBtn").onclick = () => {
  if (currentQuestion < questions.length - 1) loadQuestion(currentQuestion + 1);
};

document.getElementById("prevBtn").onclick = () => {
  if (currentQuestion > 0) loadQuestion(currentQuestion - 1);
};

document.getElementById("submitBtn").onclick = () => {
  submitExam();
};

window.addEventListener("blur", () => {
  lockedQuestions.add(currentQuestion);
  questionStates[currentQuestion] = "black";
  loadQuestion(currentQuestion);
});

function updateTimer() {
  timeLeft--;
  const min = String(Math.floor(timeLeft / 60)).padStart(2, '0');
  const sec = String(timeLeft % 60).padStart(2, '0');
  document.getElementById("time").textContent = `${min}:${sec}`;
  if (timeLeft <= 0) {
    clearInterval(timerInterval);
    alert("Time is up! Submitting your exam.");
    submitExam();
  }
}

function submitExam() {
  let correct = 0;
  questions.forEach((q, i) => {
    if (selectedAnswers[i] === q[5]) correct++;
  });

  alert(`You scored ${correct} out of ${questions.length}`);

  // ✅ Send score to Flask backend
  fetch(`/submit_result/${studentId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ score: `${correct}/${questions.length}` })
  });
}

const timerInterval = setInterval(updateTimer, 1000);
loadExcelFromServer();
// 🚫 Disable right-click
document.addEventListener("contextmenu", (e) => {
  e.preventDefault();
});

// 🚫 Disable Ctrl+C, Ctrl+U, F12, etc.
document.addEventListener("keydown", function (e) {
  if (
    (e.ctrlKey && (e.key === "c" || e.key === "u" || e.key === "s")) ||
    e.key === "F12" ||
    (e.ctrlKey && e.shiftKey && e.key === "I")
  ) {
    e.preventDefault();
  }
});
// 🚨 Lock question if mouse leaves exam area
document.getElementById("exam-area").addEventListener("mouseleave", () => {
  if (!lockedQuestions.has(currentQuestion)) {
    alert("Mouse left exam area! This question is now locked.");
    lockedQuestions.add(currentQuestion);
    questionStates[currentQuestion] = "black";
    loadQuestion(currentQuestion);
  }
});

