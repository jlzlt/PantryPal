document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.querySelector("form[action*='login']");
  if (!loginForm) return;

  loginForm.addEventListener("submit", function (e) {
    let hasError = false;

    // Clear previous errors
    loginForm
      .querySelectorAll(".is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
    loginForm
      .querySelectorAll(".invalid-feedback")
      .forEach((el) => el.remove());

    const username = loginForm["username"].value.trim();
    const password = loginForm["password"].value.trim();

    if (!username) showError("username", "Username is required.");
    if (!password) showError("password", "Password is required.");

    function showError(fieldName, message) {
      const input = loginForm[fieldName];
      input.classList.add("is-invalid");

      const error = document.createElement("div");
      error.className = "invalid-feedback mb-2";
      error.textContent = message;
      input.parentElement.appendChild(error);

      hasError = true;
    }

    if (hasError) {
      e.preventDefault();
      return; // Don't proceed with submission if frontend errors exist
    } else {
      // Disable button and show spinner
      const submitBtn = loginForm.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = true;
        const spinner = submitBtn.querySelector(".spinner-border");
        if (spinner) spinner.classList.remove("d-none");
      }
    }
  });

  // Clear error on input as user types
  loginForm.addEventListener("input", function (e) {
    if (["username", "password"].includes(e.target.name)) {
      const input = e.target;
      if (input.classList.contains("is-invalid")) {
        input.classList.remove("is-invalid");
      }
      const errorDiv = input.parentElement.querySelector(".invalid-feedback");
      if (errorDiv) errorDiv.remove();
    }
  });
});
