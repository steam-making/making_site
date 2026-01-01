
document.addEventListener("DOMContentLoaded", function () {
  const startDateInput = document.getElementById("id_start_date");
  const programEndDateInput = document.getElementById("id_end_date");
  const recruitStartInput = document.getElementById("id_recruit_start_date");
  const recruitEndInput = document.getElementById("id_recruit_end_date");
  const tuitionInput = document.getElementById("id_tuition");
  const durationInput = document.getElementById("id_class_duration");
  const startSelect = document.getElementById("id_target_start");
  const endSelect = document.getElementById("id_target_end");
  const imageInput = document.getElementById("id_image");
  const previewImg = document.getElementById("program-image-preview");
  const originalSrc = previewImg ? previewImg.src : "";

  // ------------------------------
  // 📌 월수업료 자동 계산
  // ------------------------------
  const baseFeeInput = document.getElementById("id_base_fee");         // 수강료
  const materialFeeInput = document.getElementById("id_material_fee"); // 교구비
  const includeMaterialsInput = document.getElementById("id_include_materials"); // 체크박스
  const tuitionField = document.getElementById("id_tuition");          // 월수업료

  function updateTuition() {
    let base = parseInt(baseFeeInput?.value || 0);
    let material = parseInt(materialFeeInput?.value || 0);
    let includeMat = includeMaterialsInput?.checked;

    if (!isNaN(base)) {
      let total = includeMat ? base + (isNaN(material) ? 0 : material) : base;
      tuitionField.value = total;
    }
  }

  if (baseFeeInput) baseFeeInput.addEventListener("input", updateTuition);
  if (materialFeeInput) materialFeeInput.addEventListener("input", updateTuition);
  if (includeMaterialsInput) includeMaterialsInput.addEventListener("change", updateTuition);

  // 초기 실행
  updateTuition();

  const weeklySelect = document.getElementById("id_weekly_sessions");   // ✅ Django id
  const monthlyInput = document.getElementById("id_monthly_sessions");  // ✅ Django id
  const monthsInput = document.getElementById("id_months");             // ✅ Django id
  const sessionCountInput = document.getElementById("id_session_count"); // ✅ Django id

  function updateSessionCount() {
    const weekly = Number(weeklySelect?.value || 0);
    const months = Number(monthsInput?.value || 0);

    const monthly = weekly * 4;
    if (monthlyInput) {
      monthlyInput.value = monthly;
    }

    if (sessionCountInput) {
      sessionCountInput.value = months > 0 ? monthly * months : 0;
    }

    // ✅ 반별 종료일 갱신 이벤트
    if (sessionCountInput) {
      sessionCountInput.dispatchEvent(new Event("input"));
    }
  }

  if (weeklySelect) weeklySelect.addEventListener("change", updateSessionCount);
  if (monthsInput) monthsInput.addEventListener("input", updateSessionCount);

  // ✅ 페이지 로드 시 초기값 계산
  updateSessionCount();

  const HOLIDAYS = [
    "2025-01-01","2025-03-01","2025-05-05","2025-05-06",
    "2025-06-06","2025-08-15","2025-09-07","2025-09-08","2025-09-09",
    "2025-10-03","2025-10-09","2025-12-25"
  ];

  // 📌 프로그램 종료일 = 반별 종료일 중 가장 늦은 날짜
  function updateProgramEndDate() {
    if (!programEndDateInput) return;
    let latest = null;
    document.querySelectorAll("#class-table-body input[name$='end_date']").forEach(input => {
      if (input.value) {
        let date = new Date(input.value);
        if (!isNaN(date)) {
          if (!latest || date > latest) latest = date;
        }
      }
    });
    if (latest) {
      programEndDateInput.value = latest.toLocaleDateString("en-CA");
    }
  }

  // 📌 첫 수업일 계산
  function getFirstClassDate(programStartDate, selectedDays) {
    if (!programStartDate || selectedDays.length === 0) return "";
    let cur = new Date(programStartDate);
    let safetyCounter = 0;
    while (true) {
      safetyCounter++;
      if (safetyCounter > 1000) break;
      let weekday = ["sun","mon","tue","wed","thu","fri","sat"][cur.getDay()];
      let dateStr = cur.toLocaleDateString("en-CA");
      if (selectedDays.includes(weekday) && !HOLIDAYS.includes(dateStr)) {
        return cur.toLocaleDateString("en-CA");
      }
      cur.setDate(cur.getDate() + 1);
    }
    return "";
  }

  // 📌 종료일 계산
  function calculateClassEndDate(startDate, selectedDays, countNeeded) {
    if (!startDate || !countNeeded || !Array.isArray(selectedDays) || selectedDays.length === 0) return "";
    let cur = new Date(startDate);
    let found = 0;
    let safetyCounter = 0;
    while (found < countNeeded) {
      safetyCounter++;
      if (safetyCounter > 10000) break;
      let weekday = ["sun","mon","tue","wed","thu","fri","sat"][cur.getDay()];
      let dateStr = cur.toLocaleDateString("en-CA");
      if (selectedDays.includes(weekday) && !HOLIDAYS.includes(dateStr)) found++;
      if (found < countNeeded) cur.setDate(cur.getDate() + 1);
    }
    return cur.toLocaleDateString("en-CA");
  }

  function bindClassRow(row, isFirstRow=false) {
    const checkboxes = row.querySelectorAll(".day-checkbox");
    const hiddenInput = row.querySelector("input[type=hidden][name$='days']");
    const selectedText = row.querySelector(".selected-days");
    const startInput = row.querySelector("input[name$='start_time']");
    const endInput = row.querySelector("input[name$='end_time']");
    const startDateField = row.querySelector("input[name$='start_date']");
    const endDateField = row.querySelector("input[name$='end_date']");
    const deleteBtn = row.querySelector(".delete-row");

    if (!startDateField || !endDateField) return;

    function updateSelected() {
      let values = [], labels = [];
      checkboxes.forEach(cb => {
        if (cb.checked) {
          values.push(cb.value);
          labels.push(cb.parentElement.textContent.trim());
        }
      });

      // ✅ 항상 새 값으로 덮어쓰기 (중복 hidden input을 생성하지 않음)
      if (hiddenInput) {
        // 기존 hidden input 제거
        hiddenInput.parentNode.querySelectorAll("input[type=hidden][name$='days']").forEach(el => el.remove());

        // 선택된 값마다 hidden input 추가
        values.forEach(val => {
          const newInput = document.createElement("input");
          newInput.type = "hidden";
          newInput.name = hiddenInput.name;  // 예: classes-0-days
          newInput.value = val;              // 각각 mon, wed ...
          hiddenInput.parentNode.appendChild(newInput);
        });
      }


      // ✅ 드롭다운 텍스트 갱신
      if (selectedText) {
        selectedText.textContent = labels.length > 0 ? labels.join(",") : "선택하세요";
      }

      // ✅ 종료일 자동 계산
      if (startDateInput && startDateInput.value && sessionCountInput && sessionCountInput.value) {
        let countVal = parseInt(sessionCountInput.value, 10);

      // ✅ 첫 수업일은 항상 계산
      let firstClassDate = getFirstClassDate(
        new Date(startDateInput.value + "T00:00:00"),
        values
      );
      if (startDateField && firstClassDate) {
        startDateField.value = firstClassDate;
      }

      if (countVal === 0) {
        // ✅ 무제한 모드: 종료일은 비우고 그대로 두기
        if (endDateField) {
          endDateField.value = "";
          endDateField.placeholder = "무제한";
          endDateField.readOnly = true;
        }
      } else {
        // ✅ 정상 모드: 종료일 자동 계산
        let endDateVal = calculateClassEndDate(
          new Date(startDateField.value + "T00:00:00"),
          values,
          countVal
        );
        if (endDateField && endDateVal) {
          endDateField.value = endDateVal;
          endDateField.placeholder = "";
          endDateField.readOnly = false;
          updateProgramEndDate();
        }
      }
      }
    }


    function calculateRowEndTime() {
      if (!startInput || !endInput || !durationInput) return;
      if (!startInput.value || !durationInput.value) return;
      let [h, m] = startInput.value.split(":").map(Number);
      let duration = parseInt(durationInput.value, 10);
      if (isNaN(duration)) return;
      let d = new Date();
      d.setHours(h);
      d.setMinutes(m + duration);
      endInput.value = `${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
    }

    // ✅ 이벤트 바인딩
    checkboxes.forEach(cb => cb.addEventListener("change", updateSelected));
    if (startInput) startInput.addEventListener("change", calculateRowEndTime);
    if (durationInput) durationInput.addEventListener("input", calculateRowEndTime);
    if (endDateField) endDateField.addEventListener("change", updateProgramEndDate);

    if (deleteBtn) {
      deleteBtn.addEventListener("click", function () {
        const deleteField = row.querySelector("input[name$='-DELETE']");
        if (deleteField) deleteField.checked = true; // ✅ 실제 삭제 체크
        row.style.display = "none";                  // ✅ 행 숨김
        updateProgramEndDate();
      });
    }

    // ✅ 초기값 강제 반영
    updateSelected();
  }

  // 초기 행 바인딩 (첫 번째 행만 삭제 버튼 숨김)
  document.querySelectorAll("#class-table-body .class-row").forEach((row, idx) => {
    bindClassRow(row, idx === 0);
  });
  updateProgramEndDate();

  // ✅ 반 추가
  const addBtn = document.getElementById("add-class-btn");
  const totalForms = document.querySelector("input[name$='-TOTAL_FORMS']");
  if (addBtn && totalForms) {
    addBtn.addEventListener("click", function () {
      const formIdx = parseInt(totalForms.value);
      let emptyFormHtml = document.querySelector("#empty-form").innerHTML.replace(/__prefix__/g, formIdx);

      const tempRow = document.createElement("tr");
      tempRow.classList.add("class-row");
      tempRow.innerHTML = emptyFormHtml;

      document.getElementById("class-table-body").appendChild(tempRow);
      totalForms.value = formIdx + 1;
      bindClassRow(tempRow, false); // 새로 추가된 반은 삭제 버튼 활성화
      updateProgramEndDate();
    });
  }

  // 총 횟수 변경 시 모든 반 갱신
  if (sessionCountInput) {
    sessionCountInput.addEventListener("input", function () {
      document.querySelectorAll("#class-table-body .class-row").forEach(row => {
        row.querySelectorAll(".day-checkbox").forEach(cb => {
          if (cb.checked) cb.dispatchEvent(new Event("change"));
        });
      });
      updateProgramEndDate();
    });
  }

  // 프로그램 시작일 변경 시 모든 반 갱신
  if (startDateInput) {
    startDateInput.addEventListener("change", function () {
      document.querySelectorAll("#class-table-body .class-row").forEach(row => {
        row.querySelectorAll(".day-checkbox").forEach(cb => {
          if (cb.checked) cb.dispatchEvent(new Event("change"));
        });
      });
      updateProgramEndDate();
    });
  }

  // 모집 시작일 선택 시 같은 달의 마지막 날짜로 모집 마감일 자동 설정
  if (recruitStartInput && recruitEndInput) {
    recruitStartInput.addEventListener("change", function () {
      if (recruitStartInput.value) {
        let startDate = new Date(recruitStartInput.value + "T00:00:00");

        // 👉 해당 달의 마지막 날 구하기
        let endDate = new Date(startDate.getFullYear(), startDate.getMonth() + 1, 0);

        recruitEndInput.value = endDate.toLocaleDateString("en-CA");
      }
    });
  }

  // ------------------------------ 
  // 📌 대상 끝 제한 
  // ------------------------------ 
  function updateEndOptions() { 
    if (!startSelect || !endSelect) return; 
      let startIndex = startSelect.selectedIndex; 
      for (let i = 0; i < endSelect.options.length; i++) { 
        endSelect.options[i].disabled = i < startIndex; 
      } 
      if (endSelect.selectedIndex < startIndex) {
        endSelect.selectedIndex = startIndex;
      } 
  } 
  if (startSelect) { 
    startSelect.addEventListener("change", updateEndOptions); 
    updateEndOptions(); 
  }
    
  
  
});

document.addEventListener("DOMContentLoaded", function () {
    const recruitWrapper = document.getElementById("recruit-period-wrapper");
    const classWrapper = document.getElementById("class-period-wrapper");

    const recruitRadios = document.querySelectorAll("input[name='recruit_type']");

    function togglePeriods() {
        const selected = document.querySelector("input[name='recruit_type']:checked")?.value;

        if (selected === "always") {
            recruitWrapper.style.display = "none";
            classWrapper.style.display = "none";
        } else {
            recruitWrapper.style.display = "";
            classWrapper.style.display = "";
        }
    }

    togglePeriods();

    recruitRadios.forEach(radio => {
        radio.addEventListener("change", togglePeriods);
    });
});

