// 👉 무한 루프 감지 결과를 받아 반복 제한을 입력받는 팝업
async function askLoopLimit() {
    return new Promise((resolve) => {
        let limit = prompt(
            "⚠️ 이 코드는 무한 반복을 일으킬 수 있습니다.\n\n" +
            "몇 번까지 반복을 허용할까요?\n(기본값: 100)"
        );

        if (limit === null) return resolve(null);  // 취소
        limit = parseInt(limit);

        if (isNaN(limit) || limit <= 0) {
            alert("올바른 숫자를 입력하세요!");
            return resolve(null);
        }

        resolve(limit);
    });
}

/* ===============================
   🔥 무한 반복 감지
=============================== */
function detectInfiniteLoop(code) {

    // 기본 패턴 감지
    const infinitePatterns = [
        /while\s*True\s*:/,
        /while\s*1\s*:/,
        /while\s*\(\s*1\s*\)\s*:/,
        /while\s*\(\s*True\s*\)\s*:/,
    ];

    for (let pattern of infinitePatterns) {
        if (pattern.test(code)) {
            if (!/break/.test(code)) return true;
        }
    }

    // 'while something:' 이지만 break 없는 경우도 위험
    const whileRegex = /while\s*\(?.*?\)?:/g;
    if (whileRegex.test(code) && !/break/.test(code)) {
        return true;
    }

    return false;
}


// Ace Editor 설정
var editor = ace.edit("editor");
editor.session.setMode("ace/mode/python");
editor.setTheme("ace/theme/github");
editor.setFontSize(14);

const inputBox = document.getElementById("inputBox");

// CSRF 가져오기
function getCSRF() {
    return document.getElementById("csrf").value;
}

/* ===============================
   🔥 1) 코드에서 input() 감지 + 개수 분석
=============================== */
function detectInput() {
    const code = editor.getValue();

    // input() 존재 여부
    const hasInput = code.includes("input(");

    if (!hasInput) {
        inputBox.style.display = "none";
        inputBox.value = "";
        return;
    }

    // input() 개수 세기
    let count = 0;

    const directInputs = (code.match(/input\s*\(/g) || []).length;
    count += directInputs;

    // for문 안의 반복 input() 카운트
    const forRegex = /for\s+(\w+)\s+in\s+range\s*\(\s*(\d+)\s*\)\s*:\s*\n([\s\S]*?)(?=\n\S|$)/g;
    let match;

    while ((match = forRegex.exec(code)) !== null) {
        const block = match[3];
        const repeatCount = parseInt(match[2]);
        const innerInputs = (block.match(/input\s*\(/g) || []).length;

        count += innerInputs * repeatCount;
    }

    if (count < 1) count = 1;

    inputBox.style.display = "block";
    inputBox.rows = count;
}

editor.session.on("change", detectInput);
detectInput();


/* ===============================
   🔥 실행 버튼
=============================== */
document.getElementById("btnRun").onclick = async function () {

    let code = editor.getValue();
    let csrf = getCSRF();
    let inputValue = document.getElementById("inputBox").value;

    // 1) 서버에서 input 개수 + 무한루프 검사
    let precheck = await fetch("/courses/api/precheck/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf
        },
        body: "code=" + encodeURIComponent(code)
    }).then(res=>res.json());

    // ⭐⭐⭐ 매우 중요: 서버에 보낼 필요 입력 개수 저장 ⭐⭐⭐
    let required_inputs = precheck.input_count;

    // 2) 무한 루프 의심되면 팝업
    let loop_limit = "";
    if (precheck.possible_infinite === true) {
        loop_limit = await askLoopLimit();
        if (loop_limit === null) return;
    }

    // 3) 실행 요청 (required_inputs 추가됨)
    fetch("/courses/api/run/", {
        method: "POST",
        headers: { 
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf
        },
        body:
            "code=" + encodeURIComponent(code) +
            "&loop_limit=" + loop_limit +
            "&input_value=" + encodeURIComponent(inputValue) +
            "&required_inputs=" + required_inputs  // ⭐ 핵심 추가 ⭐
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("outputBox").textContent = data.output;
    });
};


/* ===============================
   🔥 채점 버튼
=============================== */
document.getElementById("btnGrade").onclick = function () {
    let code = editor.getValue();
    let itemId = this.dataset.item;
    let csrf = getCSRF();

    fetch("/courses/api/grade/", {
        method: "POST",
        headers: { 
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf
        },
        body: "item_id=" + itemId + "&code=" + encodeURIComponent(code)
    })
    .then(res => res.json())
    .then(data => {

        let msg =
            "점수: " + data.score + "\n\n" +
            "출력:\n" + data.output + "\n\n" +
            "예상 출력:\n" + data.expected;

        if (data.completed) msg += "\n\n✔ 수업 완료!";

        document.getElementById("gradeBox").textContent = msg;
    });
};


// 힌트
document.getElementById("btnHint").onclick = function () {
    let itemId = document.getElementById("btnGrade").dataset.item;
    fetch("/courses/api/hint/" + itemId + "/")
    .then(res => res.json())
    .then(data => {
        let box = document.getElementById("hintBox");
        box.style.display = "block";
        box.textContent = data.hint;
    });
};

// 정답
document.getElementById("btnAnswer").onclick = function () {
    let itemId = document.getElementById("btnGrade").dataset.item;
    fetch("/courses/api/answer/" + itemId + "/")
    .then(res => res.json())
    .then(data => {
        let box = document.getElementById("answerBox");
        box.style.display = "block";
        box.textContent = data.answer;
    });
};


/* ===============================
   input() 개수 서버에서 정확히 분석
=============================== */
function checkInputCount(callback) {
    let code = editor.getValue();
    let csrf = getCSRF();

    fetch("/courses/api/input-count/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrf
        },
        body: "code=" + encodeURIComponent(code)
    })
    .then(res => res.json())
    .then(data => {
        callback(data.count);
    });
}

/* ===============================
   🔥 화면의 \n 문자 등 정리 (가독성 향상)
=============================== */
document.addEventListener("DOMContentLoaded", function () {
    const explainBox = document.querySelector(".explain-box");
    if (explainBox) {
        // DB에서 가져온 문자열 중 리터럴 백슬래시 n(\n) 을 HTML 개행으로 변환
        explainBox.innerHTML = explainBox.innerHTML.replace(/\\n/g, '<br>');
        
        // 추가로 연속된 스페이스(예: 파이썬 들여쓰기)를 렌더링하기 위해 스타일 추가
        explainBox.style.whiteSpace = 'pre-wrap';
    }
});
