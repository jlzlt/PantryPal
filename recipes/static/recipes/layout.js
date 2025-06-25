document.addEventListener("DOMContentLoaded", function () {
  const backToTopBtn = document.getElementById("backToTopBtn");

  document.body.addEventListener("scroll", function () {
    if (document.body.scrollTop > 1000) {
      backToTopBtn.classList.add("visible");
    } else {
      backToTopBtn.classList.remove("visible");
    }
  });

  backToTopBtn.addEventListener("click", () => {
    document.body.scrollTo({ top: 0, behavior: "smooth" });
  });
});