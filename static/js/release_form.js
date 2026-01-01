document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ release_form.js loaded");

  const vendorTypeSelect = document.getElementById("vendor_type");
  const expectedDateInput = document.getElementById("expected_date");
  const orderYearInput = document.getElementById("order_year");
  const orderMonthInput = document.getElementById("order_month");
  const teacherSelect = document.querySelector('select[name="teacher"]');
  const institutionSelect = document.querySelector(
    'select[name="institution"]'
  );
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
  // 거래처 종류 필터 함수
  // ==============================
  function applyVendorTypeFilter() {
    const selectedType = vendorTypeSelect ? vendorTypeSelect.value : "";

    // 거래처 필터링
    document.querySelectorAll(".vendor-select").forEach((vendorSelect) => {
      Array.from(vendorSelect.options).forEach((option) => {
        const type = (option.getAttribute("data-kind") || "").trim();
        const isPlaceholder = option.value === "";
        const visible = !selectedType || type === selectedType || isPlaceholder;
        option.style.display = visible ? "" : "none";

        // 선택된 값이 필터 결과에 없으면 초기화
        if (!visible && option.selected) {
          vendorSelect.value = "";
        }
      });
    });

    // 교구재 필터링
    document.querySelectorAll(".material-select").forEach((materialSelect) => {
      Array.from(materialSelect.options).forEach((opt) => {
        const kind = (opt.getAttribute("data-kind") || "").trim();
        const isPlaceholder = opt.value === "";
        const visible = !selectedType || kind === selectedType || isPlaceholder;
        opt.style.display = visible ? "" : "none";

        if (!visible && opt.selected) {
          materialSelect.value = "";
          const row = materialSelect.dataset.row;
          const priceInput = document.querySelector(
            `input[name="unit_price_${row}"]`
          );
          if (priceInput) priceInput.value = "";
        }
      });
    });
  }

  // ==============================
  // 행 이벤트 바인딩 함수
  // ==============================
  function bindRowEvents(rowIndex) {
    const vendorSelect = document.querySelector(
      `select[name="vendor_${rowIndex}"]`
    );
    const materialSelect = document.querySelector(
      `select[name="material_${rowIndex}"]`
    );
    const priceInput = document.querySelector(
      `input[name="unit_price_${rowIndex}"]`
    );

    if (!vendorSelect || !materialSelect) return;

    // 거래처 선택 → 교구재 필터링
    vendorSelect.addEventListener("change", function () {
      const selectedVendorId = String(this.value);
      let keepSelected = false;

      Array.from(materialSelect.options).forEach((option) => {
        const vendorId = option.getAttribute("data-vendor");
        const isPlaceholder = option.value === "";
        const visible =
          !vendorId || vendorId === selectedVendorId || isPlaceholder;
        option.style.display = visible ? "" : "none";

        if (visible && option.value === materialSelect.value) {
          keepSelected = true;
        }
      });

      if (!keepSelected) {
        materialSelect.value = "";
        if (priceInput) priceInput.value = "";
      }
    });

    // 교구재 선택 → 거래처 자동선택 + 납품가 입력 + 재고 표시
    materialSelect.addEventListener("change", function () {
        const selectedOption = this.options[this.selectedIndex];
        if (!selectedOption) return;

        const vendorId = selectedOption.getAttribute("data-vendor");
        const price = selectedOption.getAttribute("data-price") || 0;
        const stock = selectedOption.getAttribute("data-stock") || "-";   // ⭐ 재고

        // 거래처 자동 선택
        if (vendorSelect && vendorId) {
          vendorSelect.value = vendorId;
        }

        // 납품가 입력
        if (priceInput) priceInput.value = Number(price).toLocaleString();

        // ⭐ 재고 표시
        const stockSpan = document.querySelector(`.stock-display-${rowIndex}`);
        if (stockSpan) stockSpan.textContent = stock;
    });


    // ✅ 초기 선택값 반영
    if (materialSelect.value) materialSelect.dispatchEvent(new Event("change"));

    // ⭐ 초기 로딩 시 재고 표시
    const initOption = materialSelect.options[materialSelect.selectedIndex];
    if (initOption) {
        const initStock = initOption.getAttribute("data-stock") || "-";
        const stockSpan = document.querySelector(`.stock-display-${rowIndex}`);
        if (stockSpan) stockSpan.textContent = initStock;
}
  }

  // ==============================
  // 초기 1행 바인딩
  // ==============================
  bindRowEvents(1);

  // ==============================
  // 거래처 종류 이벤트 연결
  // ==============================
  if (vendorTypeSelect) {
    vendorTypeSelect.addEventListener("change", applyVendorTypeFilter);

    // ✅ 초기 로드시 실행
    applyVendorTypeFilter();
  }

  // ==============================
  // 행 추가 버튼
  // ==============================
  if (addRowBtn && tableBody && rowCountInput) {
    addRowBtn.addEventListener("click", function () {
      const rowCount = tableBody.querySelectorAll("tr").length;
      const newIndex = rowCount + 1;
      const firstRow = tableBody.querySelector("tr");
      const newRow = firstRow.cloneNode(true);

      newRow.querySelector(".row-number").textContent = newIndex;

      newRow.querySelectorAll("select, input").forEach((el) => {
        if (el.name) el.name = el.name.replace(/\d+$/, newIndex);
        if (el.dataset.row) el.dataset.row = newIndex;

        if (el.tagName === "INPUT") {
          if (el.classList.contains("price-input")) {
            el.value = "";
            el.placeholder = "가격";
          } else if (el.name.startsWith("quantity_")) {
            el.value = "0";
          } else {
            el.value = "";
          }
        } else if (el.tagName === "SELECT") {
          el.selectedIndex = 0;
        }
      });

      tableBody.appendChild(newRow);
      rowCountInput.value = newIndex;

      // ✅ 새 행에도 이벤트 바인딩 + 필터 적용
      bindRowEvents(newIndex);
      applyVendorTypeFilter();
    });
  }

  // ==============================
  // 출강장소 선택 → 프로그램명에 따라 거래처 종류 자동 선택
  // ==============================
  if (institutionSelect && vendorTypeSelect) {
    institutionSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      if (!selectedOption) return;

      const program = (selectedOption.dataset.program || "").toLowerCase();

      if (program.includes("로봇")) vendorTypeSelect.value = "로봇";
      else if (program.includes("과학")) vendorTypeSelect.value = "과학";
      else if (program.includes("3d펜")) vendorTypeSelect.value = "3D펜";
      else if (program.includes("드론")) vendorTypeSelect.value = "항공드론";
      else if (program.includes("코딩")) vendorTypeSelect.value = "코딩";
      else if (program.includes("수학")) vendorTypeSelect.value = "창의수학";
      else if (program.includes("it") || program.includes("교재"))
        vendorTypeSelect.value = "IT교재";
      else vendorTypeSelect.value = "";

      // ✅ 자동 선택 후 필터 적용
      vendorTypeSelect.dispatchEvent(new Event("change"));
    });
  }

   // ==============================
  // 출강장소 선택 → 해당 강사 자동 선택
  // ==============================
  if (institutionSelect && teacherSelect) {
    institutionSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      if (!selectedOption) return;

      const teacherId = selectedOption.getAttribute("data-teacher");
      if (teacherId) {
        // 강사 select 값만 변경
        teacherSelect.value = teacherId;

        // ⚠️ 여기서는 굳이 teacherSelect.change()를 실행하지 말고,
        // institutionSelect의 선택은 그대로 두게 둡니다.
        // teacherSelect.dispatchEvent(new Event("change")); ← 이거 제거!
      }
    });
  }

  // ==============================
  // 강사 선택 → 출강장소 필터링
  // ==============================
  if (teacherSelect && institutionSelect) {
    teacherSelect.addEventListener("change", function () {
      const selectedTeacherId = this.value;
      Array.from(institutionSelect.options).forEach((option) => {
        const optionTeacherId = option.getAttribute("data-teacher");
        const isPlaceholder = option.value === "";
        option.style.display =
          !selectedTeacherId ||
          optionTeacherId === selectedTeacherId ||
          isPlaceholder
            ? ""
            : "none";
      });
      institutionSelect.value = "";
    });
  }

    // ==============================
  // ✅ 페이지 로드시 출강장소가 이미 선택되어 있으면
  // 프로그램명 기준으로 거래처 종류 자동 선택 실행 (지연 실행)
  // ==============================
  if (institutionSelect && vendorTypeSelect) {
    console.log("실행 ✅ release_form auto detect start");
    setTimeout(() => {
      const selectedOption = institutionSelect.options[institutionSelect.selectedIndex];
      if (selectedOption && institutionSelect.value) {
        const program = (selectedOption.dataset.program || "")
          .toLowerCase()
          .replace(/\s+/g, ""); // 공백 제거
        
        console.log("📚 program:", program);


        if (program.includes("로봇")) vendorTypeSelect.value = "로봇";
        else if (program.includes("과학")) vendorTypeSelect.value = "과학";
        else if (program.includes("3d펜")) vendorTypeSelect.value = "3D펜";
        else if (program.includes("드론")) vendorTypeSelect.value = "항공드론";
        else if (program.includes("코딩")) vendorTypeSelect.value = "코딩";
        else if (program.includes("수학")) vendorTypeSelect.value = "창의수학";
        else if (program.includes("it") || program.includes("교재"))
          vendorTypeSelect.value = "IT교재";
        else vendorTypeSelect.value = "";

        console.log("📦 자동 거래처 종류 설정:", vendorTypeSelect.value);

        // ✅ 거래처 종류 자동 반영 후 필터 적용
        vendorTypeSelect.dispatchEvent(new Event("change"));
      }
    }, 100); // DOM 렌더 후 약간의 지연으로 실행
  }

});

// ==============================
// 납품가 입력시 천단위 콤마 적용
// ==============================
document.addEventListener("input", function (e) {
  if (e.target.classList.contains("price-input")) {
    let value = e.target.value.replace(/,/g, "");
    if (!isNaN(value) && value !== "") {
      e.target.value = Number(value).toLocaleString();
    }
  }
});

// ==============================
// 폼 전송 전에 콤마 제거
// ==============================
document.addEventListener("submit", function (e) {
  if (e.target.tagName.toLowerCase() === "form") {
    e.target.querySelectorAll(".price-input").forEach((input) => {
      input.value = input.value.replace(/,/g, "");
    });
  }
});

// ==============================
// 초기 로드시 납품가 값 천단위 변환
// ==============================
document.querySelectorAll(".price-input").forEach((input) => {
  if (input.value) {
    let value = input.value.replace(/,/g, "");
    if (!isNaN(value) && value !== "") {
      input.value = Number(value).toLocaleString();
    }
  }
});
