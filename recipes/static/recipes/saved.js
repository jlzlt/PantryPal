import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const reripeContainer = document.querySelector("#saved-recipe-results");

  reripeContainer.addEventListener("submit", (e) => {
    if (e.target.classList.contains("save-recipe-form")) {
      e.preventDefault();

      const saveForm = e.target;
      const saveButton = saveForm.querySelector("button[type='submit']");
      if (!saveButton) return;

      const buttonText = saveButton.querySelector(".button-text");
      const spinner = saveButton.querySelector(".spinner-border");
      const isSaved = saveButton.dataset.saved === "true";

      saveButton.disabled = true;
      spinner.classList.remove("d-none");
      buttonText.classList.add("d-none");

      if (isSaved) {
        // Remove saved recipe
        const recipeHash = saveForm.querySelector(
          'input[name="recipe_hash"]'
        ).value;

        fetch("/remove_saved_recipe/", {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken(),
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `recipe_hash=${encodeURIComponent(recipeHash)}`,
        })
          .then((res) => res.json())
          .then((data) => {
            spinner.classList.add("d-none");
            buttonText.classList.remove("d-none");
            saveButton.disabled = false;

            if (data.status === "removed") {
              saveButton.textContent = "💾 Save Recipe";
              saveButton.dataset.saved = "false";
            } else {
              alert(`Error: ${data.message}`);
            }
          })
          .catch((err) => {
            spinner.classList.add("d-none");
            buttonText.classList.remove("d-none");
            saveButton.disabled = false;
            console.error("Error removing recipe:", err);
            alert("Failed to remove saved recipe.");
          });
      } else {
        // Save recipe
        const recipeHash = saveForm.querySelector(
          'input[name="recipe_hash"]'
        ).value;

        fetch(saveForm.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken(),
          },
          body: `recipe_hash=${encodeURIComponent(recipeHash)}`,
        })
          .then((res) => res.json())
          .then((data) => {
            spinner.classList.add("d-none");
            buttonText.classList.remove("d-none");
            saveButton.disabled = false;

            if (data.status === "saved" || data.status === "exists") {
              buttonText.textContent = "Remove from Saved";
              saveButton.dataset.saved = "true";

              if (data.status === "exists") {
                alert(data.message);
              }
            } else if (data.status === "error") {
              alert(`Error: ${data.message}`);
            } else {
              alert("Unexpected response");
            }
          })
          .catch((err) => {
            spinner.classList.add("d-none");
            buttonText.classList.remove("d-none");
            saveButton.disabled = false;
            console.error("Error saving recipe:", err);
            alert("Failed to save recipe.");
          });
      }
    }
  });
});
