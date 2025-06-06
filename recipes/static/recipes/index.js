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

  // Adding a new ingredient
  ingredientList.addEventListener("click", function (e) {
    e.preventDefault();

    // Handle Add button
    if (e.target.classList.contains("add-ingredient")) {
      const currentInput = e.target.previousElementSibling;
      if (currentInput && currentInput.classList.contains("ingredient-input")) {
        const value = currentInput.value.trim();
        if (value === "") {
          alert("Enter ingredient to add.");
          return;
        }

        // Disable current input and add remove button
        currentInput.disabled = true;
        e.target.disabled = true;

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "btn btn-outline-danger remove-ingredient";
        removeBtn.textContent = "Remove";
        e.target.parentElement.appendChild(removeBtn);

        // Add a new empty input group (without Remove button)
        const newField = document.createElement("div");
        newField.className = "input-group mb-2";
        newField.innerHTML = `
          <input type="text" class="form-control ingredient-input" placeholder="e.g. onion" />
          <button type="button" class="btn btn-outline-primary add-ingredient">Add</button>
        `;
        ingredientList.appendChild(newField);

        updateHiddenInput();
      }
    }

    // Handle Remove button
    if (e.target.classList.contains("remove-ingredient")) {
      const group = e.target.closest(".input-group");
      if (group) {
        group.remove();
        updateHiddenInput();
      }
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
