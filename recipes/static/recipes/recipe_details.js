import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const recipeContainer = document.querySelector(".recipe-detail-container");
  let pendingRemoveForm = null;

  // Modal elements
  const modal = document.getElementById("remove-confirm-modal");
  const confirmBtn = document.getElementById("confirm-remove-btn");
  const cancelBtn = document.getElementById("cancel-remove-btn");

  // Save modal elements
  const saveModal = document.getElementById("save-confirm-modal");
  const confirmSaveBtn = document.getElementById("confirm-save-btn");
  const cancelSaveBtn = document.getElementById("cancel-save-btn");
  let pendingSaveForm = null;

  // Share modal elements
  const shareModal = document.getElementById("share-confirm-modal");
  const shareBtn = document.getElementById("share-btn");
  const confirmShareBtn = document.getElementById("confirm-share-btn");
  const cancelShareBtn = document.getElementById("cancel-share-btn");
  const shareForm = document.getElementById("share-form");

  // Handle recipe removal form submission
  if (recipeContainer) {
    recipeContainer.addEventListener("submit", (e) => {
      const form = e.target;
      if (form.classList.contains("remove-recipe-form")) {
        e.preventDefault();
        // Show custom modal for remove
        pendingRemoveForm = form;
        modal.classList.remove("d-none");
      } else if (form.classList.contains("save-recipe-form")) {
        e.preventDefault();
        // Show custom modal for save
        pendingSaveForm = form;
        saveModal.classList.remove("d-none");
      }
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
          body: `recipe_hash=${encodeURIComponent(
            form.querySelector('input[name="recipe_hash"]').value
          )}`,
        });
        const data = await response.json();
        if (data.status === "removed") {
          // Swap Remove for Save button
          const buttonGroup = form.parentNode;
          form.remove();
          // Create Save form
          const saveForm = document.createElement("form");
          saveForm.method = "POST";
          saveForm.action = "/save_recipe/";
          saveForm.className = "save-recipe-form";
          saveForm.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
            <input type="hidden" name="recipe_hash" value="${form.querySelector('input[name=recipe_hash]').value}">
            <button type="submit" class="btn view-btn" data-saved="false">
              <span class="button-text">Save</span>
              <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
            </button>
          `;
          buttonGroup.appendChild(saveForm);
          // Remove saved-timestamp footer if it exists
          let timestamp = document.querySelector(".saved-timestamp");
          if (timestamp) timestamp.remove();
        } else {
          alert(data.message || "Failed to remove recipe.");
        }
      } catch (error) {
        alert("Failed to remove recipe. Please try again.");
        console.error("Error:", error);
      } finally {
        modal.classList.add("d-none");
        pendingRemoveForm = null;
        if (buttonText && spinner && button) {
          buttonText.classList.remove("d-none");
          spinner.classList.add("d-none");
          button.disabled = false;
        }
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

  if (shareBtn && shareModal) {
    shareBtn.addEventListener("click", () => {
      shareModal.classList.remove("d-none");
    });
  }
  if (cancelShareBtn && shareModal) {
    cancelShareBtn.addEventListener("click", () => {
      shareModal.classList.add("d-none");
    });
  }
  if (confirmShareBtn && shareForm && shareModal) {
    confirmShareBtn.addEventListener("click", () => {
      shareForm.submit();
      shareModal.classList.add("d-none");
    });
  }

  // Handle save modal confirmation
  if (confirmSaveBtn) {
    confirmSaveBtn.addEventListener("click", async () => {
      if (!pendingSaveForm) return;
      const form = pendingSaveForm;
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
          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `recipe_hash=${encodeURIComponent(
            form.querySelector('input[name="recipe_hash"]').value
          )}`,
        });
        const data = await response.json();
        if (data.status === "saved" || data.status === "exists") {
          // Swap Save for Remove button
          const buttonGroup = form.parentNode;
          // Remove the Save form
          form.remove();
          // Create Remove form
          const removeForm = document.createElement("form");
          removeForm.method = "POST";
          removeForm.action = "/remove_saved_recipe/";
          removeForm.className = "remove-recipe-form";
          removeForm.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
            <input type="hidden" name="recipe_hash" value="${form.querySelector('input[name=recipe_hash]').value}">
            <button type="submit" class="btn remove-btn" data-saved="true">
              <span class="button-text">Remove</span>
              <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
            </button>
          `;
          buttonGroup.appendChild(removeForm);
          // Add or update saved-timestamp footer
          let timestamp = document.querySelector(".saved-timestamp");
          if (!timestamp) {
            timestamp = document.createElement("div");
            timestamp.className = "saved-timestamp";
            // Append to .recipe-content
            const recipeContent = document.querySelector(".recipe-content");
            if (recipeContent) recipeContent.appendChild(timestamp);
          }
          // Format today's date as 'M d, Y'
          const now = new Date();
          const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
          const formatted = `${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`;
          timestamp.textContent = `Saved ${formatted}`;
        } else {
          alert(data.message || "Failed to save recipe.");
        }
      } catch (err) {
        alert("Error saving recipe. Please try again.");
        console.error("Save error:", err);
      } finally {
        saveModal.classList.add("d-none");
        pendingSaveForm = null;
        if (buttonText && spinner && button) {
          buttonText.classList.remove("d-none");
          spinner.classList.add("d-none");
          button.disabled = false;
        }
      }
    });
  }
  if (cancelSaveBtn) {
    cancelSaveBtn.addEventListener("click", () => {
      saveModal.classList.add("d-none");
      pendingSaveForm = null;
    });
  }

  // Handle star rating submission
  const ratingContainer = document.querySelector(".star-rating-input");
  const feedback = document.getElementById("user-rating-feedback");

  if (ratingContainer) {
    const sharedId = ratingContainer.dataset.sharedId;
    const stars = Array.from(ratingContainer.querySelectorAll(".star-input")); // left-to-right

    stars.forEach((star, idx) => {
      const value = idx + 1;

      // Hover effect
      star.addEventListener("mouseover", () => {
        stars.forEach((s, i) => {
          s.classList.toggle("hover", i <= idx);
        });
      });

      star.addEventListener("mouseleave", () => {
        stars.forEach((s) => s.classList.remove("hover"));
      });

      // Click to rate
      star.addEventListener("click", async () => {
        try {
          const response = await fetch(`/rate/${sharedId}/`, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken(),
              "X-Requested-With": "XMLHttpRequest",
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `rating=${value}`,
          });

          const data = await response.json();

          if (data.success) {
            // Replace the star-rating-input with static stars
            const staticStars = document.createElement("div");
            staticStars.className = "star-rating-input";
            for (let i = 1; i <= 5; i++) {
              const star = document.createElement("span");
              star.className = i <= value ? "star" : "star star-empty";
              star.innerHTML = "&#9733;";
              staticStars.appendChild(star);
            }
            ratingContainer.parentNode.replaceChild(staticStars, ratingContainer);

            // Hide feedback text entirely
            feedback.classList.add("hidden");

            // Update community stars (Rating: ...)
            const communityStars = document.querySelector(".community-stars");
            if (communityStars) {
              // Remove all children
              communityStars.innerHTML = "";
              // Add new stars based on new average rating
              let avg = parseFloat(data.average_rating);
              for (let i = 1; i <= 5; i++) {
                let starEl = document.createElement("span");
                if (avg >= i) {
                  starEl.className = "star";
                  starEl.innerHTML = "&#9733;";
                } else if (avg >= i - 0.5) {
                  starEl.className = "half-star";
                  starEl.innerHTML = "&#9733;";
                } else {
                  starEl.className = "star star-empty";
                  starEl.innerHTML = "&#9733;";
                }
                communityStars.appendChild(starEl);
              }
              // Create or update rating number and total votes
              let ratingNumber = document.createElement("span");
              ratingNumber.className = "rating-number";
              ratingNumber.textContent = data.average_rating;
              let totalVotes = document.createElement("span");
              totalVotes.className = "total-votes";
              totalVotes.textContent = `(${data.total_votes} vote${data.total_votes === 1 ? '' : 's'})`;
              communityStars.appendChild(ratingNumber);
              communityStars.appendChild(totalVotes);
            }
          } else {
            feedback.textContent = data.error || "Failed to rate.";
            feedback.classList.remove("hidden");
          }
        } catch (err) {
          feedback.textContent = "Error submitting rating.";
          feedback.classList.remove("hidden");
          console.error("Rating error:", err);
        }
      });
    });
  }
});
