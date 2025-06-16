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

  // Load more recipes via AJAX
  async function loadMoreRecipes() {
    if (isLoading || !hasMore) return;
    
    isLoading = true;
    currentPage++;

    // Show loading spinner
    const loadingSpinner = document.querySelector('.loading-spinner');
    if (loadingSpinner) {
      loadingSpinner.classList.remove('d-none');
    }

    try {
      const url = new URL(window.location.href);
      url.searchParams.set('page', currentPage);
      
      const response = await fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      
      // Create a temporary container to parse the HTML
      const tempContainer = document.createElement('div');
      tempContainer.innerHTML = data.html;
      
      // Get all recipe cards from the temporary container
      const recipeCards = tempContainer.querySelectorAll('.col-12');
      
      // Get the row element
      const row = recipeContainer.querySelector('.row');
      
      // Append each recipe card to the row
      recipeCards.forEach(card => {
        row.appendChild(card);
      });
      
      // Update hasMore flag
      hasMore = data.has_more;
      
      // If no more recipes, remove scroll listener and hide spinner
      if (!hasMore) {
        window.removeEventListener('scroll', handleScroll);
        if (loadingSpinner) {
          loadingSpinner.remove();
        }
      }
    } catch (error) {
      console.error('Error loading more recipes:', error);
    } finally {
      isLoading = false;
    }
  }

  // Add scroll event listener
  window.addEventListener('scroll', handleScroll);

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
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await response.json();

        if (data.status === "removed") {
          // Remove the recipe card from the DOM
          const recipeCard = form.closest(".col-12");
          recipeCard.remove();
        } else {
          console.error("Error removing recipe:", data.message);
        }
      } catch (error) {
        console.error("Error:", error);
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
