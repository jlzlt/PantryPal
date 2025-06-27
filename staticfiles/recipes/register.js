document.addEventListener("DOMContentLoaded", function () {
  const registerForm = document.querySelector("form[action*='register']");
  if (!registerForm) return;

  registerForm.addEventListener("submit", function (e) {
    let hasError = false;

    // Clear previous errors
    registerForm
      .querySelectorAll(".is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
    registerForm
      .querySelectorAll(".invalid-feedback")
      .forEach((el) => el.remove());

    const fields = ["username", "email", "password", "confirmation"];
    const values = {};
    fields.forEach((name) => {
      values[name] = registerForm[name].value.trim();
    });

    // Username and email required
    if (values.username === "") showError("username", "Username is required.");
    if (values.email === "") showError("email", "Email is required.");

    // Password matching check
    if (values.password === "" || values.confirmation === "") {
      showError("password", "Password is required.");
      showError("confirmation", "Please confirm your password.");
    } else if (values.password !== values.confirmation) {
      showError("confirmation", "Passwords must match.");
    }

    function showError(fieldName, message) {
      const input = registerForm[fieldName];
      input.classList.add("is-invalid");

      const error = document.createElement("div");
      error.className = "invalid-feedback mb-2";
      error.textContent = message;
      input.parentElement.appendChild(error);

      hasError = true;
    }

    if (hasError) {
      e.preventDefault();
    }
  });

  // Add input event listener to clear errors as user types
  registerForm.addEventListener("input", function (e) {
    if (
      ["username", "email", "password", "confirmation"].includes(e.target.name)
    ) {
      const input = e.target;

      if (input.classList.contains("is-invalid")) {
        input.classList.remove("is-invalid");
      }

      // Remove the error message div, if any
      const errorDiv = input.parentElement.querySelector(".invalid-feedback");
      if (errorDiv) {
        errorDiv.remove();
      }
    }
  });
});
