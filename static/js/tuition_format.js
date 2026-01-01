document.addEventListener("DOMContentLoaded", function () {
  const tuitionInput = document.getElementById("id_tuition");
  if (tuitionInput) {
    tuitionInput.addEventListener("input", function () {
      let val = this.value.replace(/,/g, "");
      if (!isNaN(val) && val !== "") {
        this.value = Number(val).toLocaleString("ko-KR");
      }
    });
  }
});
