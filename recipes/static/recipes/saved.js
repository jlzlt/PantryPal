import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const recipeContainer = document.querySelector("#saved-recipe-results");
  let pendingRemoveForm = null;

  // Modal elements
  const modal = document.getElementById("remove-confirm-modal");
  const confirmBtn = document.getElementById("confirm-remove-btn");
  const cancelBtn = document.getElementById("cancel-remove-btn");

  // Filter button handling for multi-select
  const filterGroup = document.querySelector(".filter-group");
  if (filterGroup) {
    filterGroup.addEventListener("click", (e) => {
      const button = e.target.closest(".btn-filter");
      if (!button) return;

      e.preventDefault();
      const tag = button.dataset.tag;
      if (!tag) return;

      const url = new URL(window.location.href);
      const params = url.searchParams;
      const currentFilters = params.getAll("filter");

      if (currentFilters.includes(tag)) {
        // Remove the tag if already active
        params.delete("filter"); // Remove all existing 'filter' params
        currentFilters.filter(f => f !== tag).forEach(f => params.append("filter", f));
      } else {
        // Add the tag if not active
        params.append("filter", tag);
      }
      window.location.href = url.toString();
    });
  }

  recipeContainer.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form.classList.contains("save-recipe-form")) return;
    e.preventDefault();

    // Show custom modal
    pendingRemoveForm = form;
    modal.classList.remove("d-none");
  });

  confirmBtn.addEventListener("click", function () {
    if (!pendingRemoveForm) return;
    // Proceed with AJAX removal (same as your previous logic)
    const submitBtn = pendingRemoveForm.querySelector("button[type='submit']");
    const buttonText = submitBtn.querySelector(".button-text");
    const spinner = submitBtn.querySelector(".spinner-border");

    submitBtn.disabled = true;
    spinner.classList.remove("d-none");
    buttonText.classList.add("d-none");

    const recipeHash = pendingRemoveForm.querySelector('input[name="recipe_hash"]').value;

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
        submitBtn.disabled = false;

        if (data.status === "removed") {
          const cardCol = pendingRemoveForm.closest(".col-12.col-sm-6.col-md-4.col-lg-3");
          if (cardCol) cardCol.remove();
          if (recipeContainer.querySelectorAll(".col-12.col-sm-6.col-md-4.col-lg-3").length === 0) {
            recipeContainer.innerHTML = `
              <div class="text-center py-5">
                <h4 class="mb-3">You have not saved recipes yet.</h4>
              </div>`;
          }
        } else {
          submitBtn.disabled = false;
          alert(`Error: ${data.message}`);
        }
        modal.classList.add("d-none");
        pendingRemoveForm = null;
      })
      .catch((err) => {
        submitBtn.disabled = false;
        spinner.classList.add("d-none");
        buttonText.classList.remove("d-none");
        console.error("Error removing recipe:", err);
        alert("Failed to remove saved recipe.");
        modal.classList.add("d-none");
        pendingRemoveForm = null;
      });
  });

  cancelBtn.addEventListener("click", function () {
    modal.classList.add("d-none");
    pendingRemoveForm = null;
  });
});
