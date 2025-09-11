// Search with pagination support
document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.querySelector(".products-filters form");
  const searchInput = document.getElementById("searchInput");

  // Handle form submission
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // Submit the form to trigger server-side search with pagination
      window.location.href = `?search=${encodeURIComponent(searchInput.value)}`;
    });
  }

  // Handle real-time search with debounce
  if (searchInput) {
    let searchTimeout;

    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimeout);

      // Debounce search for 300ms
      searchTimeout = setTimeout(() => {
        const searchValue = searchInput.value.trim();

        // Only search if value changed and is different from current URL param
        const urlParams = new URLSearchParams(window.location.search);
        const currentSearch = urlParams.get("search") || "";

        if (searchValue !== currentSearch) {
          if (searchValue === "") {
            // Clear search - go to base URL
            window.location.href = window.location.pathname;
          } else {
            // Perform search
            window.location.href = `?search=${encodeURIComponent(searchValue)}`;
          }
        }
      }, 500); // 500ms delay for better UX
    });
  }

  // Smooth scroll to pagination if user clicks pagination links
  const paginationLinks = document.querySelectorAll(".pagination .page-link");
  paginationLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      // Add smooth scroll behavior
      setTimeout(() => {
        const productsSection = document.querySelector(".products-grid");
        if (productsSection) {
          productsSection.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 100);
    });
  });
});

// Enhanced loading states
function showLoadingState() {
  const productsGrid = document.getElementById("productsGrid");
  if (productsGrid) {
    productsGrid.style.opacity = "0.6";
    productsGrid.style.pointerEvents = "none";
  }
}

function hideLoadingState() {
  const productsGrid = document.getElementById("productsGrid");
  if (productsGrid) {
    productsGrid.style.opacity = "1";
    productsGrid.style.pointerEvents = "auto";
  }
}

// Add loading state when navigating
window.addEventListener("beforeunload", showLoadingState);
