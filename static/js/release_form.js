document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ release_form.js loaded (autocomplete ver)");

  const vendorTypeSelect = document.getElementById("vendor_type");
  const expectedDateInput = document.getElementById("expected_date");
  const orderYearInput = document.getElementById("order_year");
  const orderMonthInput = document.getElementById("order_month");
  const teacherInput = document.getElementById("teacherInput");
  const teacherList = document.getElementById("teacherAcList");
  const teacherHidden = document.getElementById("teacherHidden");
  const addRowBtn = document.getElementById("addRowBtn");
  const tableBody = document.querySelector("#releaseTable tbody");
  const rowCountInput = document.getElementById("row_count");

  // ==============================
  // 날짜 기본값
  // ==============================
  if (expectedDateInput && !expectedDateInput.value) {
    const now = new Date();
    now.setDate(now.getDate() + (now.getHours() < 12 ? 2 : 3));
    expectedDateInput.value = now.toISOString().split("T")[0];
  }
  if (orderYearInput && !orderYearInput.value)
    orderYearInput.value = new Date().getFullYear();
  if (orderMonthInput && !orderMonthInput.value)
    orderMonthInput.value = String(new Date().getMonth() + 1).padStart(2, "0");

  // ==============================
  // 🔧 범용 자동완성 셋업
  // ==============================
  function setupAutocomplete(input, list, hidden, onSelect) {
    if (!input || !list || !hidden) return;
    const items = list.querySelectorAll("li:not(.empty)");
    const emptyMsg = list.querySelector(".empty");

    // 초기값 표시
    if (hidden.value) {
      const match = list.querySelector(`li[data-id="${hidden.value}"]`);
      if (match) input.value = match.textContent.trim();
    }

    function filterAndShow() {
      const val = input.value.toLowerCase().trim();
      let hasMatch = false;
      items.forEach(li => {
        const matchesText = li.textContent.toLowerCase().includes(val);
        // f-out- 으로 시작하는 클래스가 하나라도 있으면 외부 필터에 의해 가려진 것
        const isExternallyFiltered = Array.from(li.classList).some(cls => cls.startsWith("f-out-"));
        
        const visible = matchesText && !isExternallyFiltered;
        li.style.display = visible ? "" : "none";
        if (visible) hasMatch = true;
      });
      if (emptyMsg) emptyMsg.style.display = hasMatch ? "none" : "block";
      list.classList.add("show");
    }

    input.addEventListener("input", function () {
      hidden.value = "";
      filterAndShow();
    });
    input.addEventListener("focus", filterAndShow);

    items.forEach(li => {
      li.addEventListener("click", function (e) {
        e.preventDefault();
        input.value = this.textContent.trim();
        hidden.value = this.getAttribute("data-id");
        list.classList.remove("show");
        if (onSelect) onSelect(this);
      });
    });

    document.addEventListener("click", function (e) {
      if (!input.contains(e.target) && !list.contains(e.target)) {
        list.classList.remove("show");
      }
    });
  }

  // ==============================
  // 출강장소 자동완성
  // ==============================
  const instInput = document.getElementById("institutionInput");
  const instList = document.getElementById("institutionAcList");
  const instHidden = document.getElementById("institutionHidden");

  setupAutocomplete(instInput, instList, instHidden, function (selectedLi) {
    const program = (selectedLi.getAttribute("data-program") || "").toLowerCase();
    const teacherId = selectedLi.getAttribute("data-teacher");

    // 강사 자동선택
    if (teacherHidden && teacherId) {
      teacherHidden.value = teacherId;
      // 강사 이름도 입력창에 표시
      if (teacherList) {
        const tLi = teacherList.querySelector(`li[data-id="${teacherId}"]`);
        if (tLi && teacherInput) teacherInput.value = tLi.textContent.trim();
      }
    }

    // 거래처 종류 자동선택
    if (vendorTypeSelect) {
      if (program.includes("로봇")) vendorTypeSelect.value = "로봇";
      else if (program.includes("과학")) vendorTypeSelect.value = "과학";
      else if (program.includes("3d펜")) vendorTypeSelect.value = "3D펜";
      else if (program.includes("드론")) vendorTypeSelect.value = "항공드론";
      else if (program.includes("코딩")) vendorTypeSelect.value = "코딩";
      else if (program.includes("수학")) vendorTypeSelect.value = "창의수학";
      else if (program.includes("it") || program.includes("교재"))
        vendorTypeSelect.value = "IT교재";
      else vendorTypeSelect.value = "";

      vendorTypeSelect.dispatchEvent(new Event("change"));
    }
  });

  // 초기 로드시 출강장소가 이미 선택되어 있으면 자동 처리
  if (instHidden && instHidden.value && instList) {
    const matchLi = instList.querySelector(`li[data-id="${instHidden.value}"]`);
    if (matchLi) {
      if (instInput) instInput.value = matchLi.textContent.trim();
      // 거래처종류 자동 매칭
      setTimeout(() => {
        const program = (matchLi.getAttribute("data-program") || "").toLowerCase();
        if (vendorTypeSelect) {
          if (program.includes("로봇")) vendorTypeSelect.value = "로봇";
          else if (program.includes("과학")) vendorTypeSelect.value = "과학";
          else if (program.includes("3d펜")) vendorTypeSelect.value = "3D펜";
          else if (program.includes("드론")) vendorTypeSelect.value = "항공드론";
          else if (program.includes("코딩")) vendorTypeSelect.value = "코딩";
          else if (program.includes("수학")) vendorTypeSelect.value = "창의수학";
          else if (program.includes("it") || program.includes("교재"))
            vendorTypeSelect.value = "IT교재";
          else vendorTypeSelect.value = "";
          vendorTypeSelect.dispatchEvent(new Event("change"));
        }
      }, 100);
    }
  }

  // ==============================
  // 거래처 종류 필터
  // ==============================
  function applyVendorTypeFilter() {
    const selectedType = vendorTypeSelect ? vendorTypeSelect.value : "";

    // 거래처 리스트 필터링
    document.querySelectorAll(".vendor-ac-list").forEach(list => {
      list.querySelectorAll("li:not(.empty)").forEach(li => {
        const kind = (li.getAttribute("data-kind") || "").trim();
        if (!selectedType || kind === selectedType) {
          li.classList.remove("f-out-type");
        } else {
          li.classList.add("f-out-type");
        }
      });
    });

    // 교구재 리스트 필터링
    document.querySelectorAll(".material-ac-list").forEach(list => {
      list.querySelectorAll("li:not(.empty)").forEach(li => {
        const kind = (li.getAttribute("data-kind") || "").trim();
        if (!selectedType || kind === selectedType) {
          li.classList.remove("f-out-type");
        } else {
          li.classList.add("f-out-type");
        }
      });
    });
  }

  if (vendorTypeSelect) {
    vendorTypeSelect.addEventListener("change", applyVendorTypeFilter);
    applyVendorTypeFilter();
  }

  // ==============================
  // 행별 자동완성 바인딩
  // ==============================
  function bindRowAutocomplete(rowIndex) {
    const vendorInput = document.querySelector(`.vendor-ac-input[data-row="${rowIndex}"]`);
    const vendorList = document.querySelector(`.vendor-ac-list[data-row="${rowIndex}"]`);
    const vendorHidden = document.querySelector(`.vendor-hidden[data-row="${rowIndex}"]`);

    const matInput = document.querySelector(`.material-ac-input[data-row="${rowIndex}"]`);
    const matList = document.querySelector(`.material-ac-list[data-row="${rowIndex}"]`);
    const matHidden = document.querySelector(`.material-hidden[data-row="${rowIndex}"]`);

    const priceInput = document.querySelector(`input[name="unit_price_${rowIndex}"]`);
    const stockSpan = document.querySelector(`.stock-display-${rowIndex}`);

    // 거래처 자동완성
    setupAutocomplete(vendorInput, vendorList, vendorHidden, function (li) {
      // 거래처 선택 시 교구재 리스트를 해당 거래처로 필터
      if (matList) {
        const vendorId = li.getAttribute("data-id");
        matList.querySelectorAll("li:not(.empty)").forEach(mli => {
          const mVendor = mli.getAttribute("data-vendor");
          if (!vendorId || mVendor === vendorId) {
            mli.classList.remove("f-out-vendor");
          } else {
            mli.classList.add("f-out-vendor");
          }
        });
      }
    });

    // 교구재 자동완성
    setupAutocomplete(matInput, matList, matHidden, function (li) {
      const vendorId = li.getAttribute("data-vendor");
      const vendorName = li.getAttribute("data-vendor-name");
      const kind = li.getAttribute("data-kind");
      const price = li.getAttribute("data-price") || 0;
      const stock = li.getAttribute("data-stock") || "-";

      // 거래처 자동선택
      if (vendorHidden && vendorId) {
        vendorHidden.value = vendorId;
        if (vendorInput && vendorName) vendorInput.value = vendorName;
      }

      // 거래처 종류 자동선택
      if (vendorTypeSelect && kind) {
        vendorTypeSelect.value = kind;
        applyVendorTypeFilter();
      }

      // 납품가 자동입력
      if (priceInput) priceInput.value = Number(price).toLocaleString();

      // 재고 표시
      if (stockSpan) stockSpan.textContent = stock;
    });
  }

  // 초기 행 바인딩
  const initialRows = tableBody ? tableBody.querySelectorAll("tr").length : 0;
  for (let i = 1; i <= initialRows; i++) {
    bindRowAutocomplete(i);
  }

  // ==============================
  // 행 추가
  // ==============================
  if (addRowBtn && tableBody && rowCountInput) {
    addRowBtn.addEventListener("click", function () {
      const rowCount = tableBody.querySelectorAll("tr").length;
      const newIndex = rowCount + 1;
      const firstRow = tableBody.querySelector("tr");
      const newRow = firstRow.cloneNode(true);

      newRow.querySelector(".row-number").textContent = newIndex;

      // data-row 업데이트
      newRow.querySelectorAll("[data-row]").forEach(el => {
        el.setAttribute("data-row", newIndex);
      });

      // name 업데이트
      newRow.querySelectorAll("[name]").forEach(el => {
        el.name = el.name.replace(/\d+$/, newIndex);
      });

      // class 업데이트 (stock-display)
      const stockSpan = newRow.querySelector("[class*='stock-display-']");
      if (stockSpan) {
        stockSpan.className = stockSpan.className.replace(/stock-display-\d+/, `stock-display-${newIndex}`);
        stockSpan.textContent = "-";
      }

      // 값 초기화
      newRow.querySelectorAll("input").forEach(el => {
        if (el.type === "hidden") el.value = "";
        else if (el.classList.contains("price-input")) { el.value = ""; el.placeholder = "가격"; }
        else if (el.name && el.name.startsWith("quantity_")) el.value = "0";
        else el.value = "";
      });
      newRow.querySelectorAll("select").forEach(el => el.selectedIndex = 0);

      tableBody.appendChild(newRow);
      rowCountInput.value = newIndex;

      bindRowAutocomplete(newIndex);
      applyVendorTypeFilter();
    });
  }

  // ==============================
  // 강사 자동완성
  // ==============================
  // 강사 선택 시 출강장소 필터링 함수
  function filterInstitutionsByTeacher() {
    const teacherId = teacherHidden ? teacherHidden.value : "";
    if (instList) {
      instList.querySelectorAll("li:not(.empty)").forEach(li => {
        const tid = li.getAttribute("data-teacher");
        if (!teacherId || tid === teacherId) {
          li.classList.remove("f-out-teacher");
        } else {
          li.classList.add("f-out-teacher");
        }
      });
    }
  }

  setupAutocomplete(teacherInput, teacherList, teacherHidden, function (selectedLi) {
    filterInstitutionsByTeacher();
    // 강사 변경 시 출강장소 선택 초기화
    if (instInput) instInput.value = "";
    if (instHidden) instHidden.value = "";
  });

  // 초기 로드시 강사가 있으면 필터 적용
  if (teacherHidden && teacherHidden.value) {
    filterInstitutionsByTeacher();
  }
});

// ==============================
// 납품가 천단위 콤마
// ==============================
document.addEventListener("input", function (e) {
  if (e.target.classList.contains("price-input")) {
    let value = e.target.value.replace(/,/g, "");
    if (!isNaN(value) && value !== "") {
      e.target.value = Number(value).toLocaleString();
    }
  }
});

// 폼 전송 전 콤마 제거
document.addEventListener("submit", function (e) {
  if (e.target.tagName.toLowerCase() === "form") {
    e.target.querySelectorAll(".price-input").forEach((input) => {
      input.value = input.value.replace(/,/g, "");
    });
  }
});

// 초기 로드시 납품가 값 천단위 변환
document.querySelectorAll(".price-input").forEach((input) => {
  if (input.value) {
    let value = input.value.replace(/,/g, "");
    if (!isNaN(value) && value !== "") {
      input.value = Number(value).toLocaleString();
    }
  }
});
