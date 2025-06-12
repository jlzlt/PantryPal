function getCSRFToken() {
  const cookieName = "csrftoken";
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(cookieName + "=")) {
      return decodeURIComponent(cookie.substring(cookieName.length + 1));
    }
  }
  // Fallback to hidden form input
  const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return csrfInput ? csrfInput.value : null;
}

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

        // Remove existing error if any
        const existingError =
          currentInput.parentElement.querySelector(".invalid-feedback");
        if (existingError) existingError.remove();
        currentInput.classList.remove("is-invalid");

        // Validate input
        if (value === "") {
          // Add red border and error message below the input
          currentInput.classList.add("is-invalid");

          const errorMsg = document.createElement("div");
          errorMsg.className = "invalid-feedback";
          errorMsg.textContent = "Please enter an ingredient before adding.";

          currentInput.parentElement.appendChild(errorMsg);
          return;
        }

        // Disable current input and add remove button
        currentInput.disabled = true;

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
          <button type="button" class="btn btn-outline-primary add-ingredient rounded-end">Add</button>
          <div class="suggestions-list position-absolute bg-white border rounded shadow-sm" style="top: 100%; left: 0; right: 0; z-index: 1000;"></div>
        `;
        ingredientList.appendChild(newField);

        const newInput = newField.querySelector(".ingredient-input");
        if (newInput) {
          newInput.focus();
        }

        e.target.remove();

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

  // Track which suggestion is highlighted
  let selectedSuggestionIndex = -1;

  ingredientList.addEventListener("input", function (e) {
    if (e.target.classList.contains("ingredient-input")) {
      const input = e.target;
      const query = input.value.trim().toLowerCase();
      const suggestionsBox =
        input.parentElement.querySelector(".suggestions-list");

      if (input.classList.contains("is-invalid") && query.length > 0) {
        input.classList.remove("is-invalid");
        const errorMsg = input.parentElement.querySelector(".invalid-feedback");
        if (errorMsg) errorMsg.remove();
      }

      if (query.length < 2) {
        suggestionsBox.style.display = "none";
        suggestionsBox.innerHTML = "";
        selectedSuggestionIndex = -1;
        return;
      }

      // Fetch suggestions from your Django backend
      fetch(`/autocomplete_ingredients?query=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((suggestions) => {
          suggestionsBox.innerHTML = "";
          if (suggestions.length === 0) {
            suggestionsBox.style.display = "none";
            selectedSuggestionIndex = -1;
            return;
          }

          selectedSuggestionIndex = -1; // reset highlight

          suggestions.forEach((suggestion) => {
            const item = document.createElement("div");
            item.className = "suggestion-item";
            item.textContent = suggestion;
            item.addEventListener("click", () => {
              input.value = suggestion;
              suggestionsBox.style.display = "none";
              suggestionsBox.innerHTML = "";
              selectedSuggestionIndex = -1;
              updateHiddenInput();
            });
            suggestionsBox.appendChild(item);
          });

          suggestionsBox.style.display = "block";
        });
    }
  });

  ingredientList.addEventListener("keydown", function (e) {
    if (!e.target.classList.contains("ingredient-input")) return;

    const input = e.target;
    const suggestionsBox =
      input.parentElement.querySelector(".suggestions-list");
    const items = suggestionsBox?.querySelectorAll(".suggestion-item");

    // If suggestions not visible or no items, reset index and exit early for keys other than Enter
    if (!items || items.length === 0) {
      if (e.key === "Enter") {
        // No suggestions visible: this Enter triggers Add button
        e.preventDefault();
        const addBtn = input.parentElement.querySelector(".add-ingredient");
        if (addBtn && !addBtn.disabled) {
          addBtn.click();
        }
      }
      return;
    }

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
      if (
        selectedSuggestionIndex >= 0 &&
        selectedSuggestionIndex < items.length
      ) {
        e.preventDefault(); // prevent form submit or blur

        const selected = items[selectedSuggestionIndex];
        input.value = selected.textContent;
        updateHiddenInput();

        suggestionsBox.innerHTML = "";
        suggestionsBox.style.display = "none";
        selectedSuggestionIndex = -1;
      } else {
        // No highlighted suggestion, Enter should add ingredient
        e.preventDefault();
        const addBtn = input.parentElement.querySelector(".add-ingredient");
        if (addBtn && !addBtn.disabled) {
          addBtn.click();
        }
      }
    } else if (e.key === "Escape") {
      suggestionsBox.innerHTML = "";
      suggestionsBox.style.display = "none";
      selectedSuggestionIndex = -1;
    } else if (e.key == "Tab") {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex + 1) % items.length;
      updateSuggestionHighlight(items);
    }
  });

  document.addEventListener("click", function (e) {
    // Find all visible suggestions boxes
    const allSuggestionsBoxes = document.querySelectorAll(".suggestions-list");

    allSuggestionsBoxes.forEach((suggestionsBox) => {
      // Only process if the suggestions box is currently visible
      if (suggestionsBox.style.display === "block") {
        const container = suggestionsBox.closest(".input-group");

        // Check if clicked outside the container (input + suggestions)
        if (container && !container.contains(e.target)) {
          suggestionsBox.innerHTML = "";
          suggestionsBox.style.display = "none";
          selectedSuggestionIndex = -1;

          // Clear the input's invalid state if present
          const input = container.querySelector(".ingredient-input");
          if (input) {
            input.classList.remove("is-invalid");
            const errorMsg = container.querySelector(".invalid-feedback");
            if (errorMsg) errorMsg.remove();
          }
        }
      }
    });
  });

  function updateSuggestionHighlight(items) {
    items.forEach((item, idx) => {
      item.style.backgroundColor =
        idx === selectedSuggestionIndex ? "#e8f0fe" : "";
    });
  }

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

    updateHiddenInput();

    const inputs = ingredientList.querySelectorAll(".ingredient-input");
    let hasValid = false;

    // Clear any previous error styles/messages
    inputs.forEach((input) => {
      input.classList.remove("is-invalid");
      const existingError =
        input.parentElement.querySelector(".invalid-feedback");
      if (existingError) existingError.remove();

      if (input.value.trim() !== "") {
        hasValid = true;
      }
    });

    // Show validation error if no valid input
    if (!hasValid) {
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
      return;
    }

    // Show spinner and hide results while loading
    spinner.style.display = "block";
    recipeContainer.style.display = "none";

    const formData = new FormData(form);

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

  const reripeContainer = document.querySelector("#recipe-results");

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
