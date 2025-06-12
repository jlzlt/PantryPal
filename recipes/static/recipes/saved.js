import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const reripeContainer = document.querySelector("#saved-recipe-results");

  reripeContainer.addEventListener("submit", (e) => {
    if (e.target.classList.contains("save-recipe-form")) {
      e.preventDefault();

      const saveForm = e.target;
      const saveButton = saveForm.querySelector("button[type='submit']");
      if (!saveButton) return;

      const isSaved = saveButton.dataset.saved === "true";

      if (isSaved) {
        // Call remove API
        fetch("/remove_saved_recipe/", {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken(),
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `hash=${encodeURIComponent(
            saveForm.querySelector('input[name="hash"]').value
          )}`,
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status === "removed") {
              saveButton.textContent = "Save Recipe";
              saveButton.dataset.saved = "false";
            } else {
              alert(`Error: ${data.message}`);
            }
          })
          .catch((err) => {
            console.error("Error removing recipe:", err);
            alert("Failed to remove saved recipe.");
          });
      } else {
        const formData = new FormData(saveForm);

        fetch(saveForm.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken(),
          },
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status === "saved") {
              const saveButton = saveForm.querySelector(
                "button[type='submit']"
              );
              if (saveButton) {
                saveButton.textContent = "Remove from Saved";
                saveButton.dataset.saved = "true";
              }
            } else if (data.status === "exists") {
              const saveButton = saveForm.querySelector(
                "button[type='submit']"
              );
              if (saveButton) {
                saveButton.textContent = "Remove from Saved";
                saveButton.dataset.saved = "true";
              }
              alert(data.message);
            } else if (data.status === "error") {
              alert(`Error: ${data.message}`);
            } else {
              alert("Unexpected response");
            }
          })
          .catch((err) => {
            console.error("Error saving recipe:", err);
            alert("Failed to save recipe.");
          });
      }
    }
  });
});
