const toggleButtons = document.querySelectorAll("[data-form-target]");
const forms = document.querySelectorAll(".auth-form");
const confirmButtons = document.querySelectorAll("[data-confirm]");

toggleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const targetId = button.dataset.formTarget;
    toggleButtons.forEach((item) => item.classList.remove("active"));
    forms.forEach((form) => form.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(targetId)?.classList.add("active");
  });
});

confirmButtons.forEach((button) => {
  button.addEventListener("click", (event) => {
    const message = button.dataset.confirm || "Are you sure?";
    if (!window.confirm(message)) {
      event.preventDefault();
    }
  });
});
