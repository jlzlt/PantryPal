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
  if (confirmShareBtn && shareForm && shareModal) {
    confirmShareBtn.addEventListener("click", () => {
      shareModal.classList.add("d-none");
      const shareBtnOnPage = document.getElementById("share-btn");
      if (shareBtnOnPage) {
        shareBtnOnPage.disabled = true;
        let spinner = shareBtnOnPage.querySelector(".spinner-border");
        let buttonText = shareBtnOnPage.querySelector(".button-text");
        if (!spinner) {
          spinner = document.createElement("span");
          spinner.className = "spinner-border spinner-border-sm ms-2";
          spinner.setAttribute("role", "status");
          spinner.setAttribute("aria-hidden", "true");
          shareBtnOnPage.appendChild(spinner);
        }
        if (buttonText) buttonText.classList.remove("d-none");
        spinner.classList.remove("d-none");
      }
      shareForm.submit();
    });
  }

  // Submit form to remove shared recipe if user confirms in modal
  if (confirmRemoveShareBtn && removeShareForm && removeShareModal) {
    confirmRemoveShareBtn.addEventListener("click", () => {
      removeShareModal.classList.add("d-none");
      const removeShareBtn = document.getElementById("remove-share-btn");
      if (removeShareBtn) {
        removeShareBtn.disabled = true;
        let spinner = removeShareBtn.querySelector(".spinner-border");
        let buttonText = removeShareBtn.querySelector(".button-text");
        if (!spinner) {
          spinner = document.createElement("span");
          spinner.className = "spinner-border spinner-border-sm ms-2";
          spinner.setAttribute("role", "status");
          spinner.setAttribute("aria-hidden", "true");
          removeShareBtn.appendChild(spinner);
        }
        if (buttonText) buttonText.classList.remove("d-none");
        spinner.classList.remove("d-none");
      }
      removeShareForm.submit();
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
      modal.classList.add("d-none");
      const form = pendingRemoveForm;
      const button = form.querySelector("button[type='submit']");
      const buttonText = button.querySelector(".button-text");
      const spinner = button.querySelector(".spinner-border");
      buttonText.classList.remove("d-none");
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
            <input type="hidden" name="recipe_hash" value="${form.querySelector("input[name=recipe_hash]").value}">
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
        pendingRemoveForm = null;
        // No need to revert spinner/button state since form is removed or replaced
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

  // Handle save modal confirmation
  if (confirmSaveBtn) {
    confirmSaveBtn.addEventListener("click", async () => {
      if (!pendingSaveForm) return;
      saveModal.classList.add("d-none");
      const form = pendingSaveForm;
      const button = form.querySelector("button[type='submit']");
      const buttonText = button.querySelector(".button-text");
      const spinner = button.querySelector(".spinner-border");
      buttonText.classList.remove("d-none");
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
            <input type="hidden" name="recipe_hash" value="${form.querySelector("input[name=recipe_hash]").value}">
            <button type="submit" class="btn remove-btn" data-saved="true">
              <span class="button-text">Remove from Saved</span>
              <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
            </button>
          `;
          buttonGroup.appendChild(removeForm);
          // Add saved-timestamp footer if needed (optional)
        } else {
          alert(data.message || "Failed to save recipe.");
        }
      } catch (error) {
        alert("Failed to save recipe. Please try again.");
        console.error("Error:", error);
      } finally {
        pendingSaveForm = null;
        // No need to revert spinner/button state since form is removed or replaced
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

  // --- Live character counter for comment textarea ---
  const commentTextarea = document.querySelector('textarea[name="text"]');
  const charCount = document.getElementById('comment-char-count');
  if (commentTextarea && charCount) {
    const maxLen = 1000;
    function updateCharCount() {
      const len = commentTextarea.value.length;
      charCount.textContent = `${len} / ${maxLen}`;
      if (len >= maxLen) {
        charCount.classList.add('text-danger');
      } else {
        charCount.classList.remove('text-danger');
      }
    }
    commentTextarea.addEventListener('input', updateCharCount);
    // Initialize on page load
    updateCharCount();
  }

  // --- Image preview modal for comment images ---
  const previewImgs = document.querySelectorAll('.comment-preview-img');
  const imgPreviewModal = document.getElementById('img-preview-modal');
  const imgPreviewLarge = document.getElementById('img-preview-large');
  const closeImgPreview = document.getElementById('close-img-preview');

  if (previewImgs.length && imgPreviewModal && imgPreviewLarge && closeImgPreview) {
    previewImgs.forEach(img => {
      img.addEventListener('click', function () {
        imgPreviewLarge.src = this.dataset.imgUrl || this.src;
        imgPreviewModal.classList.remove('d-none');
      });
    });
    closeImgPreview.addEventListener('click', function () {
      imgPreviewModal.classList.add('d-none');
      imgPreviewLarge.src = '';
    });
    imgPreviewModal.addEventListener('click', function (e) {
      if (e.target === imgPreviewModal) {
        imgPreviewModal.classList.add('d-none');
        imgPreviewLarge.src = '';
      }
    });
  }

  // --- Frontend validation for comment image file size ---
  const imageInput = document.querySelector('.comment-section input[type="file"]');
  if (imageInput) {
    let warning = document.createElement('div');
    warning.className = 'text-danger small mt-1';
    warning.style.display = 'none';
    imageInput.parentNode.insertBefore(warning, imageInput.nextSibling);
    imageInput.addEventListener('change', function () {
      warning.style.display = 'none';
      if (imageInput.files && imageInput.files[0]) {
        const file = imageInput.files[0];
        if (file.size > 3 * 1024 * 1024) {
          warning.textContent = 'Image file size cannot exceed 3MB.';
          warning.style.display = 'block';
          imageInput.value = '';
        }
      }
    });
  }
});
