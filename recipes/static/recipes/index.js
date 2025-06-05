document.addEventListener("DOMContentLoaded", function () {
  const ingredientList = document.getElementById("ingredient-list");
  const hiddenInput = document.getElementById("ingredients-hidden");

  function updateHiddenInput() {
    const inputs = ingredientList.querySelectorAll(".ingredient-input");
    const values = Array.from(inputs)
      .map((input) => input.value.trim())
      .filter((val) => val !== "");
    hiddenInput.value = values.join(", ");
  }

  // Add new ingredient input
  ingredientList.addEventListener("click", function (e) {
    if (e.target.classList.contains("add-ingredient")) {
      e.preventDefault();

      // Disable the current input field
      const currentInput = e.target.previousElementSibling;
      if (currentInput && currentInput.classList.contains("ingredient-input")) {
        currentInput.disabled = true;
        e.target.disabled = true;
      }

      const newField = document.createElement("div");
      newField.className = "input-group mb-2";
      newField.innerHTML = `
          <input type="text" class="form-control ingredient-input" placeholder="e.g. onion" />
          <button type="button" class="btn btn-outline-primary add-ingredient">Add</button>
        `;
      ingredientList.appendChild(newField);
      updateHiddenInput();
    }
  });

  // Update hidden input on submit
  document
    .getElementById("ingredient-filter-form")
    .addEventListener("submit", function (e) {
      updateHiddenInput();
    });

  // Toggle "show more" filters
  const toggleLink = document.getElementById("toggle-filters");
  const moreFilters = document.getElementById("more-filters");

  toggleLink.addEventListener("click", function (e) {
    e.preventDefault();
    if (moreFilters.style.display === "none") {
      moreFilters.style.display = "block";
      toggleLink.textContent = "Show fewer filters ▲";
    } else {
      moreFilters.style.display = "none";
      toggleLink.textContent = "Show more filters ▼";
    }
  });
});
