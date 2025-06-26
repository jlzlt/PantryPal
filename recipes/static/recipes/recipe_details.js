import { getCSRFToken } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const recipeContainer = document.querySelector(".recipe-detail-container");

  // Save modal elements
  const saveModal = document.getElementById("save-confirm-modal");
  const confirmSaveBtn = document.getElementById("confirm-save-btn");
  const cancelSaveBtn = document.getElementById("cancel-save-btn");
  let pendingSaveForm = null;

  // Remove from Saved Modal elements
  const modal = document.getElementById("remove-confirm-modal");
  const confirmBtn = document.getElementById("confirm-remove-btn");
  const cancelBtn = document.getElementById("cancel-remove-btn");
  let pendingRemoveForm = null;

  // Share modal elements
  const shareBtn = document.getElementById("share-btn");
  const shareForm = document.getElementById("share-form");
  const shareModal = document.getElementById("share-confirm-modal");
  const confirmShareBtn = document.getElementById("confirm-share-btn");
  const cancelShareBtn = document.getElementById("cancel-share-btn");

  // Remove share modal elements
  const removeShareForm = document.getElementById("remove-share-form");
  const removeShareModal = document.getElementById(
    "remove-share-confirm-modal"
  );
  const confirmRemoveShareBtn = document.getElementById(
    "confirm-remove-share-btn"
  );
  const cancelRemoveShareBtn = document.getElementById(
    "cancel-remove-share-btn"
  );

  // Show modals for save, remove from saved and remove from shared
  if (recipeContainer) {
    recipeContainer.addEventListener("submit", (e) => {
      const form = e.target;
      if (form.classList.contains("remove-recipe-form")) {
        e.preventDefault();
        // Modal for remove from saved
        pendingRemoveForm = form;
        modal.classList.remove("d-none");
      } else if (form.classList.contains("save-recipe-form")) {
        e.preventDefault();
        // Modal for save
        pendingSaveForm = form;
        saveModal.classList.remove("d-none");
        // Modal for remove from shared
      } else if (form.id === "remove-share-form") {
        e.preventDefault();
        removeShareModal.classList.remove("d-none");
      }
    });
  }

  // Submit form to share recipe if user confirms in modal
  if (confirmRemoveShareBtn && removeShareForm && removeShareModal) {
    confirmRemoveShareBtn.addEventListener("click", () => {
      removeShareForm.submit();
      removeShareModal.classList.add("d-none");
    });
  }

  // If user cancels remove modal
  if (cancelRemoveShareBtn && removeShareModal) {
    cancelRemoveShareBtn.addEventListener("click", () => {
      removeShareModal.classList.add("d-none");
    });
  }

  // Handle modal confirmation for removing from saved
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

      // Remove from saved
      try {
        const response = await fetch("/remove_saved_recipe/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRFToken(),
          },
          body: new URLSearchParams(new FormData(form)),
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
            <input type="hidden" name="recipe_hash" value="${
              form.querySelector("input[name=recipe_hash]").value
            }">
            <button type="submit" class="btn add-btn" data-saved="false">
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

  // Handle share recipe functionality (submits form, refreshes page)
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
        const response = await fetch("/save_recipe/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRFToken(),
          },
          body: new URLSearchParams(new FormData(form)),
        });

        const data = await response.json();
        if (data.status === "saved") {
          // Swap Save for Remove button
          const buttonGroup = form.parentNode;
          form.remove();
          // Create Remove form
          const removeForm = document.createElement("form");
          removeForm.method = "POST";
          removeForm.action = "/remove_saved_recipe/";
          removeForm.className = "remove-recipe-form";
          removeForm.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
            <input type="hidden" name="recipe_hash" value="${
              form.querySelector("input[name=recipe_hash]").value
            }">
            <button type="submit" class="btn remove-btn" data-saved="true">
              <span class="button-text">Remove from Saved</span>
              <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
            </button>
          `;
          buttonGroup.appendChild(removeForm);
          // Add saved-timestamp footer
          const timestamp = document.createElement("div");
          timestamp.className = "saved-timestamp";
          timestamp.textContent = `Saved ${new Date().toLocaleDateString(
            "en-US",
            {
              month: "short",
              day: "numeric",
              year: "numeric",
            }
          )}`;
          document
            .querySelector(".button-group")
            .insertAdjacentElement("afterend", timestamp);
        } else {
          alert(data.message || "Failed to save recipe.");
        }
      } catch (error) {
        alert("Failed to save recipe. Please try again.");
        console.error("Error:", error);
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

  // Handle save modal cancellation
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
    let stars = Array.from(ratingContainer.querySelectorAll(".star-input"));
    let selectedValue = stars.filter((s) =>
      s.classList.contains("selected")
    ).length;

    function updateSelectedStars(value, store = false) {
      stars.forEach((star, idx) => {
        star.classList.toggle("selected", idx < value);
      });
      if (store) {
        selectedValue = value;
      }
    }

    stars.forEach((star, idx) => {
      const value = idx + 1;

      // Hover effect
      star.addEventListener("mouseover", () => {
        updateSelectedStars(value);
      });

      star.addEventListener("mouseleave", () => {
        updateSelectedStars(selectedValue);
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
            // Update selected state, keep interactive stars
            updateSelectedStars(value, true);
            // Hide feedback text entirely
            if (feedback) feedback.classList.add("hidden");

            // Update community stars (Rating: ...)
            const communityStars = document.querySelector(".community-stars");
            if (communityStars) {
              communityStars.innerHTML = "";
              let avg = parseFloat(data.average_rating);
              for (let i = 1; i <= 5; i++) {
                let fill = Math.max(0, Math.min(1, avg - (i - 1)));
                let starEl = document.createElement("span");
                if (fill === 1) {
                  starEl.className = "star";
                  starEl.innerHTML = "&#9733;";
                } else if (fill === 0) {
                  starEl.className = "star star-empty";
                  starEl.innerHTML = "&#9733;";
                } else {
                  starEl.className = "star partial-star";
                  starEl.innerHTML = "&#9733;";
                  starEl.style.setProperty(
                    "--star-fill",
                    `${(fill * 100).toFixed(0)}%`
                  );
                }
                communityStars.appendChild(starEl);
              }
            }
            // Update rating number and total votes in .rating-numbers
            let ratingNumbers = document.querySelector(".rating-numbers");
            if (ratingNumbers) {
              ratingNumbers.innerHTML = "";
              const ratingNumber = document.createElement("span");
              ratingNumber.className = "rating-number";
              ratingNumber.textContent = parseFloat(
                data.average_rating
              ).toFixed(1);
              const totalVotes = document.createElement("span");
              totalVotes.className = "total-votes";
              totalVotes.textContent = ` (${data.total_votes} vote${
                data.total_votes === 1 ? "" : "s"
              })`;
              ratingNumbers.appendChild(ratingNumber);
              ratingNumbers.appendChild(totalVotes);
            } else {
              // If .rating-numbers doesn't exist, create and insert it after .community-stars
              const starsAndNumbers = communityStars?.parentElement;
              if (starsAndNumbers) {
                ratingNumbers = document.createElement("div");
                ratingNumbers.className = "rating-numbers";
                const ratingNumber = document.createElement("span");
                ratingNumber.className = "rating-number";
                ratingNumber.textContent = parseFloat(
                  data.average_rating
                ).toFixed(1);
                const totalVotes = document.createElement("span");
                totalVotes.className = "total-votes";
                totalVotes.textContent = ` (${data.total_votes} vote${
                  data.total_votes === 1 ? "" : "s"
                })`;
                ratingNumbers.appendChild(ratingNumber);
                ratingNumbers.appendChild(totalVotes);
                starsAndNumbers.appendChild(ratingNumbers);
              }
            }
          } else {
            if (feedback) {
              feedback.textContent = data.error || "Failed to rate.";
              feedback.classList.remove("hidden");
            }
          }
        } catch (err) {
          if (feedback) {
            feedback.textContent = "Error submitting rating.";
            feedback.classList.remove("hidden");
          }
          console.error("Rating error:", err);
        }
      });
    });
  }
});
