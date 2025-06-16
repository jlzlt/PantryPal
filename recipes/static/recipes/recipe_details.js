import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const recipeContainer = document.querySelector(".recipe-detail-container");
  let pendingRemoveForm = null;

  // Modal elements
  const modal = document.getElementById("remove-confirm-modal");
  const confirmBtn = document.getElementById("confirm-remove-btn");
  const cancelBtn = document.getElementById("cancel-remove-btn");

  // Handle recipe removal form submission
  if (recipeContainer) {
    recipeContainer.addEventListener("submit", (e) => {
      const form = e.target;
      if (!form.classList.contains("save-recipe-form")) return;
      e.preventDefault();

      // Show custom modal
      pendingRemoveForm = form;
      modal.classList.remove("d-none");
    });
  }

  // Handle modal confirmation
  if (confirmBtn) {
    confirmBtn.addEventListener("click", async () => {
      if (!pendingRemoveForm) return;

      const form = pendingRemoveForm;
      const button = form.querySelector("button[type='submit']");
      const buttonText = button.querySelector(".button-text");
      const spinner = button.querySelector(".spinner-border");

      // Show loading state
      buttonText.classList.add("d-none");
      spinner.classList.remove("d-none");
      button.disabled = true;

      try {
        const response = await fetch("/remove_saved_recipe/", {
          method: "POST",
          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `recipe_hash=${encodeURIComponent(form.querySelector('input[name="recipe_hash"]').value)}`,
        });

        const data = await response.json();

        if (data.status === "removed") {
          // Redirect to saved recipes page after successful removal
          window.location.href = "/saved/";
        } else {
          console.error("Error removing recipe:", data.message);
          alert(`Error: ${data.message}`);
        }
      } catch (error) {
        console.error("Error:", error);
        alert("Failed to remove recipe. Please try again.");
      } finally {
        // Hide modal
        modal.classList.add("d-none");
        pendingRemoveForm = null;
      }
    });
  }

  // Handle modal cancellation
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      modal.classList.add("d-none");
      pendingRemoveForm = null;
    });
  }
}); 