function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
  const addToCartButtons = document.querySelectorAll(".add-btn");
  addToCartButtons.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const productId = btn.getAttribute("data-product-id");
      fetch("/cart/add/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `product_id=${productId}`,
      })
        .then((response) => response.json())
        .then((data) => {
          showToast(
            "Produto adicionado!",
            "Item foi adicionado ao seu carrinho."
          );
          updateCartBadge(data.cart_count);
        });
    });
  });

  function showToast(title, description) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    document.getElementById("toastTitle").textContent = title;
    document.getElementById("toastDescription").textContent = description;
    toast.classList.add("active");
    setTimeout(() => toast.classList.remove("active"), 2000);
  }

  function updateCartBadge(count) {
    const badge = document.querySelector(".cart-badge-header");
    if (badge) {
      badge.textContent = count;
    }
  }
});
