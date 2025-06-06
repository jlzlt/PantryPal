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
          // Add red border and error message below the input
          currentInput.classList.add("is-invalid");

          const errorMsg = document.createElement("div");
          errorMsg.className = "invalid-feedback";
          errorMsg.textContent = "Please enter an ingredient before adding.";

          currentInput.parentElement.appendChild(errorMsg);
          return;
        }

        // Remove error if it's there
        currentInput.classList.remove("is-invalid");
        const leftoverError =
          currentInput.parentElement.querySelector(".invalid-feedback");
        if (leftoverError) leftoverError.remove();

        // Disable current input and add remove button
        currentInput.disabled = true;
        e.target.disabled = true;

        const suggestionsBox =
          e.target.parentElement.querySelector(".suggestions-list");
        if (suggestionsBox) {
          suggestionsBox.innerHTML = "";
          suggestionsBox.style.display = "none";
        }

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className =
          "btn btn-outline-danger remove-ingredient animate-in";
        removeBtn.textContent = "Remove";
        e.target.parentElement.appendChild(removeBtn);

        // Add a new empty input group (without Remove button)
        const newField = document.createElement("div");
        newField.className = "input-group mb-2 animate-in position-relative";
        newField.innerHTML = `
          <input type="text" class="form-control ingredient-input" placeholder="e.g. onion" autocomplete="off" />
          <button type="button" class="btn btn-outline-primary add-ingredient">Add</button>
          <div class="suggestions-list position-absolute bg-white border rounded shadow-sm" style="top: 100%; left: 0; right: 0; z-index: 1000;"></div>
        `;
        ingredientList.appendChild(newField);

        const newInput = newField.querySelector(".ingredient-input");
        if (newInput) {
          newInput.focus();
        }

        updateHiddenInput();
      }
    }

    // Handle Remove button
    if (e.target.classList.contains("remove-ingredient")) {
      const group = e.target.closest(".input-group");
      if (group) {
        group.classList.add("animate-out");
        group.addEventListener(
          "animationend",
          () => {
            group.remove();
            updateHiddenInput();
          },
          { once: true }
        );
      }
    }
  });

  ingredientList.addEventListener("keydown", function (e) {
    // Check if Enter key is pressed inside an ingredient input
    if (e.target.classList.contains("ingredient-input") && e.key === "Enter") {
      e.preventDefault(); // prevent form submit

      // Find the corresponding Add button next to this input
      const addBtn = e.target.parentElement.querySelector(".add-ingredient");
      if (addBtn && !addBtn.disabled) {
        addBtn.click(); // trigger the Add button click handler
      }
    }
  });

  ingredientList.addEventListener("input", function (e) {
    if (e.target.classList.contains("ingredient-input")) {
      const input = e.target;
      const query = input.value.trim().toLowerCase();
      const suggestionsBox =
        input.parentElement.querySelector(".suggestions-list");

      if (query.length < 2) {
        suggestionsBox.style.display = "none";
        suggestionsBox.innerHTML = "";
        return;
      }

      // Fetch suggestions from your Django backend
      fetch(`/autocomplete_ingredients?query=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((suggestions) => {
          suggestionsBox.innerHTML = "";
          if (suggestions.length === 0) {
            suggestionsBox.style.display = "none";
            return;
          }

          selectedSuggestionIndex = -1;
          suggestions.forEach((suggestion) => {
            const item = document.createElement("div");
            item.className = "suggestion-item";
            item.textContent = suggestion;
            item.addEventListener("click", () => {
              input.value = suggestion;
              suggestionsBox.style.display = "none";
            });
            suggestionsBox.appendChild(item);
          });

          suggestionsBox.style.display = "block";
        });
    }
  });

  let selectedSuggestionIndex = -1;

  ingredientList.addEventListener("keydown", function (e) {
    if (!e.target.classList.contains("ingredient-input")) return;

    const input = e.target;
    const suggestionsBox =
      input.parentElement.querySelector(".suggestions-list");
    const items = suggestionsBox?.querySelectorAll(".suggestion-item");

    if (!items || items.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex + 1) % items.length;
      updateSuggestionHighlight(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedSuggestionIndex =
        (selectedSuggestionIndex - 1 + items.length) % items.length;
      updateSuggestionHighlight(items);
    } else if (e.key === "Enter") {
      const input = e.target;
      e.preventDefault();

      if (
        selectedSuggestionIndex >= 0 &&
        selectedSuggestionIndex < items.length
      ) {
        input.value = items[selectedSuggestionIndex].textContent;
      }

      // Always close the suggestion box
      suggestionsBox.innerHTML = "";
      suggestionsBox.style.display = "none";
      selectedSuggestionIndex = -1;

      // Optionally, trigger the Add button programmatically
      const addButton = input.parentElement.querySelector(".add-ingredient");
      if (addButton && !input.disabled) {
        addButton.click();
      }
    } else if (e.key === "Escape") {
      suggestionsBox.innerHTML = "";
      suggestionsBox.style.display = "none";
      selectedSuggestionIndex = -1;
    }
  });

  function updateSuggestionHighlight(items) {
    items.forEach((item, idx) => {
      item.style.backgroundColor =
        idx === selectedSuggestionIndex ? "#e8f0fe" : "";
    });
  }

  // Update hidden input on submit
  document
    .getElementById("ingredient-filter-form")
    .addEventListener("submit", function (e) {
      updateHiddenInput();

      const inputs = ingredientList.querySelectorAll(".ingredient-input");
      let hasValid = false;

      // Clear any previous error styles/messages
      inputs.forEach((input) => {
        input.classList.remove("is-invalid");
        const existingError =
          input.parentElement.querySelector(".invalid-feedback");
        if (existingError) existingError.remove();
      });

      // Check if there's at least one non-empty input
      inputs.forEach((input) => {
        if (input.value.trim() !== "") {
          hasValid = true;
        }
      });

      if (!hasValid) {
        e.preventDefault();

        // Add red border and inline message to the latest active input field
        const lastInputGroup = ingredientList.querySelector(
          ".input-group:last-child"
        );
        const input = lastInputGroup.querySelector(".ingredient-input");

        input.classList.add("is-invalid");

        const errorMsg = document.createElement("div");
        errorMsg.className = "invalid-feedback";
        errorMsg.textContent =
          "Please enter at least one ingredient before submitting.";

        input.parentElement.appendChild(errorMsg);
      }
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

  const form = document.getElementById("ingredient-filter-form");
  const spinner = document.getElementById("loading-spinner");
  const recipeContainer = document.getElementById("recipe-results");

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Show spinner and hide results while loading
    spinner.style.display = "block";
    recipeContainer.style.display = "none";

    console.log(form);
    const formData = new FormData(form);
    console.log(formData);

    fetch("/", {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        recipeContainer.innerHTML = data.html;

        // Hide spinner, show updated results
        spinner.style.display = "none";
        recipeContainer.style.display = "block";
      })
      .catch((err) => {
        console.error("Error submitting form:", err);
        spinner.style.display = "none";
        recipeContainer.style.display = "block";
        recipeContainer.innerHTML =
          '<div class="alert alert-danger">Failed to load recipes. Please try again.</div>';
      });
  });
});
