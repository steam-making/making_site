(function () {
  const app = document.getElementById("typingApp");
  const stageId = parseInt(app.dataset.stageId, 10);
  const lang = app.dataset.lang; // KO / EN
  const durationLimit = parseInt(app.dataset.duration, 10);

  const minSpeed = parseInt(app.dataset.minSpeed, 10);
  const minAcc = parseInt(app.dataset.minAcc, 10);
  const maxTypo = parseInt(app.dataset.maxTypo, 10);

  const chars = JSON.parse(
    document.getElementById("typing-chars-data").textContent
    );


  if (!chars.length) {
    alert("연습 문자가 설정되지 않았습니다.\n관리자에게 문의하세요.");
    console.error("❌ chars is empty");
    return;
  }    


  const $remain = document.getElementById("remainTime");
  const $targetNow = document.getElementById("targetNow");
  const $targetNext = document.getElementById("targetNext");
  const $input = document.getElementById("typingInput");
  const $progress = document.getElementById("progressBar");

  const $statDuration = document.getElementById("statDuration");
  const $statAcc = document.getElementById("statAcc");
  const $statTypo = document.getElementById("statTypo");
  const $statSpeed = document.getElementById("statSpeed");

  const $btnReset = document.getElementById("btnReset");
  const $btnSave = document.getElementById("btnSave");
  const $passBadge = document.getElementById("passBadge");
  const $soundToggle = document.getElementById("soundToggle");

  const $keyboardArea = document.getElementById("keyboardArea");

  // -------------------------
  // 음성(정답 시만)
  // -------------------------
  const KO_JAMO_SPEAK = {
    "ㄱ": "기역", "ㄴ": "니은", "ㄷ": "디귿", "ㄹ": "리을",
    "ㅁ": "미음", "ㅂ": "비읍", "ㅅ": "시옷", "ㅇ": "이응",
    "ㅈ": "지읒", "ㅊ": "치읓", "ㅋ": "키읔", "ㅌ": "티읕",
    "ㅍ": "피읖", "ㅎ": "히읗",
    "ㅏ": "아", "ㅓ": "어", "ㅗ": "오", "ㅜ": "우",
    "ㅡ": "으", "ㅣ": "이",
  };

  function speak(text) {
    if (!$soundToggle.checked) return;
    if (!("speechSynthesis" in window)) return;

    const u = new SpeechSynthesisUtterance(text);
    u.lang = (lang === "KO") ? "ko-KR" : "en-US";
    window.speechSynthesis.cancel(); // 겹침 방지
    window.speechSynthesis.speak(u);
  }

  function speakCorrectChar(ch) {
    if (lang === "KO") {
      speak(KO_JAMO_SPEAK[ch] || ch);
    } else {
      // 영어는 문자 자체를 읽게
      speak(ch);
    }
  }

  // -------------------------
  // 키보드 UI(간단 버전)
  // -------------------------
  // 자리연습에서는 "연습 문자" 기준으로만 키를 만들어도 충분합니다.
  function renderKeyboard() {
    // 연습 chars를 2~3줄로 나눠서 보여주기
    const uniq = Array.from(new Set(chars));
    const rows = [];
    const perRow = Math.ceil(uniq.length / 3) || 1;

    for (let i = 0; i < uniq.length; i += perRow) {
      rows.push(uniq.slice(i, i + perRow));
    }

    let html = `<div class="kbd-grid">`;
    rows.forEach((r, idx) => {
      html += `<div class="kbd-row" data-row="${idx}">`;
      r.forEach((k) => {
        html += `<div class="kbd-key" data-key="${k}">${escapeHtml(k)}</div>`;
      });
      html += `</div>`;
    });
    html += `</div>`;

    $keyboardArea.innerHTML = html;
  }

  function highlightKey(ch) {
    const keys = $keyboardArea.querySelectorAll(".kbd-key");
    keys.forEach((el) => el.classList.remove("active"));

    const target = $keyboardArea.querySelector(
        `.kbd-key[data-key="${ch}"]`
    );
    if (target) target.classList.add("active");
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  // -------------------------
  // 연습 로직
  // -------------------------
  let started = false;
  let startTime = 0;
  let timerId = null;

  let targetQueue = [];
  let currentTarget = null;

  let correct = 0;
  let typo = 0;
  let totalTyped = 0;
  let finished = false;

  function pickRandomChar() {
    const i = Math.floor(Math.random() * chars.length);
    return chars[i];
  }

  function buildQueue(n = 30) {
    const q = [];
    for (let i = 0; i < n; i++) q.push(pickRandomChar());
    return q;
  }

  function setNextTarget() {
    if (targetQueue.length < 10) {
      targetQueue = targetQueue.concat(buildQueue(20));
    }
    currentTarget = targetQueue.shift();
    const next = targetQueue[0] || "-";
    $targetNow.textContent = currentTarget;
    $targetNext.textContent = `다음: ${next}`;
    highlightKey(currentTarget);

    console.log("target:", currentTarget,
    $keyboardArea.querySelector(`.kbd-key[data-key="${currentTarget}"]`)
);
  }

  function elapsedSeconds() {
    if (!started) return 0;
    return Math.floor((Date.now() - startTime) / 1000);
  }

  function calcAccuracy() {
    if (totalTyped <= 0) return 0;
    return Math.floor((correct / totalTyped) * 100);
  }

  function calcSpeed() {
    const sec = elapsedSeconds();
    if (sec <= 0) return 0;
    return Math.floor((correct / sec) * 60);
  }

  function updateStats() {
    const sec = elapsedSeconds();
    const remain = Math.max(0, durationLimit - sec);

    $remain.textContent = remain;
    $statDuration.textContent = `${sec}s`;
    $statTypo.textContent = `${typo}`;

    const acc = calcAccuracy();
    const spd = calcSpeed();

    $statAcc.textContent = `${acc}%`;
    $statSpeed.textContent = `${spd}`;

    const progress = Math.min(100, (sec / durationLimit) * 100);
    $progress.style.width = `${progress}%`;

    // pass badge(진행중 표시)
    if (!finished) {
      $passBadge.className = "badge bg-secondary";
      $passBadge.textContent = "진행중";
    }
  }

  function stop() {
    finished = true;
    if (timerId) clearInterval(timerId);

    $input.disabled = true;
    $btnSave.disabled = false;

    const acc = calcAccuracy();
    const spd = calcSpeed();
    const pass = (acc >= minAcc && spd >= minSpeed && typo <= maxTypo);

    $passBadge.className = pass ? "badge bg-success" : "badge bg-danger";
    $passBadge.textContent = pass ? "통과" : "재도전";
  }

  function startIfNeeded() {
    if (started) return;
    started = true;
    startTime = Date.now();

    timerId = setInterval(() => {
      updateStats();
      if (elapsedSeconds() >= durationLimit) stop();
    }, 200);

    updateStats();
  }

  // 핵심: 입력 1글자씩 판단 (자리연습이라 1글자 비교)
  function onInputChange() {
    if (finished) return;

    const val = $input.value;
    if (!val) return;

    startIfNeeded();

    // 사용자가 넣은 마지막 글자만 확인
    const typed = val[val.length - 1];

    // 다음 입력을 위해 input은 항상 비움(한 글자씩)
    $input.value = "";

    totalTyped += 1;

    if (typed === currentTarget) {
      correct += 1;
      speakCorrectChar(currentTarget);
    } else {
      typo += 1;
      // 오답은 소리 X (원하면 여기에 삐 소리 등 추가 가능)
    }

    setNextTarget();
    updateStats();
  }

  async function saveResult() {
    const acc = calcAccuracy();
    const spd = calcSpeed();
    const sec = elapsedSeconds();

    const payload = {
      speed: spd,
      accuracy: acc,
      typo_count: typo,
      duration: sec,
    };

    const res = await fetch(`/typing/practice/${stageId}/save/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (data.ok) {
      // 저장 후 안내
      alert(data.passed ? "✅ 결과 저장 완료! (통과)" : "✅ 결과 저장 완료! (재도전)");
    } else {
      alert("저장 실패");
    }
  }

  function getCsrfToken() {
    // 기본: 쿠키에서 csrftoken 찾기
    const name = "csrftoken=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(";");
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i].trim();
      if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return "";
  }

  function resetAll() {
    if (timerId) clearInterval(timerId);

    started = false;
        finished = false;
        startTime = 0;

        correct = 0;
        typo = 0;
        totalTyped = 0;

        $input.disabled = false;
        $input.value = "";
        $btnSave.disabled = true;

        targetQueue = buildQueue(30);
        setNextTarget();        // ← currentTarget 설정
        updateStats();

        // ✅ 여기 추가
        if (currentTarget) {
            highlightKey(currentTarget);
        }
    }


  // -------------------------
  // 이벤트 바인딩
  // -------------------------
  renderKeyboard();
  resetAll();

  $input.addEventListener("input", onInputChange);
  $btnReset.addEventListener("click", resetAll);
  $btnSave.addEventListener("click", saveResult);

})();
