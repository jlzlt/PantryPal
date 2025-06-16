import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const recipeContainer = document.querySelector("#saved-recipe-results");
  let pendingRemoveForm = null;
  let currentPage = 1;
  let isLoading = false;
  let hasMore = true;

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
        currentFilters
          .filter((f) => f !== tag)
          .forEach((f) => params.append("filter", f));
      } else {
        // Add the tag if not active
        params.append("filter", tag);
      }
      window.location.href = url.toString();
    });
  }

  // Infinite scroll handler
  function handleScroll() {
    if (isLoading || !hasMore) return;

    // Get the loading spinner element
    const loadingSpinner = document.querySelector('.loading-spinner');
    if (!loadingSpinner) return;

    // Get the position of the loading spinner
    const spinnerRect = loadingSpinner.getBoundingClientRect();
    const spinnerBottom = spinnerRect.bottom;

    // Check if the spinner is visible in the viewport
    if (spinnerBottom <= window.innerHeight) {
      loadMoreRecipes();
    }
  }

  // Load more recipes function
  async function loadMoreRecipes() {
    if (isLoading) return;
    isLoading = true;

    const loadingSpinner = document.querySelector('.loading-spinner');
    if (loadingSpinner) {
      loadingSpinner.classList.remove('d-none');
    }

    try {
      const url = new URL(window.location.href);
      url.searchParams.set('page', currentPage + 1);

      const response = await fetch(url.toString(), {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const data = await response.json();

      if (data.html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = data.html;
        const newCards = tempDiv.querySelectorAll('.col-12');
        
        const recipeGrid = document.querySelector('.row.g-4');
        if (recipeGrid) {
          newCards.forEach(card => {
            recipeGrid.appendChild(card);
          });
        }

        currentPage++;
        hasMore = data.has_more;
      }
    } catch (error) {
      console.error('Error loading more recipes:', error);
    } finally {
      isLoading = false;
      if (loadingSpinner) {
        loadingSpinner.classList.add('d-none');
      }
    }
  }

  // Add scroll event listener
  window.addEventListener("scroll", handleScroll);

  // Handle recipe removal
  recipeContainer.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form.classList.contains("save-recipe-form")) return;
    e.preventDefault();

    // Show custom modal
    pendingRemoveForm = form;
    modal.classList.remove("d-none");
  });

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
          // Remove the recipe card from the DOM
          const recipeCard = form.closest(".col-12");
          recipeCard.remove();
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
