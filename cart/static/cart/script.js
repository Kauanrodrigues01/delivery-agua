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
  function updateQtyValue(btn, newQty) {
    const qtySpan = btn.parentElement.querySelector(".cart-item-qty-value");
    if (qtySpan) qtySpan.textContent = newQty;
  }

  function removeCartItemElement(btn) {
    const cartItem = btn.closest(".cart-item");
    if (cartItem) cartItem.remove();
  }

  function updateCartTotal(newTotal) {
    const totalSpan = document.querySelector(".cart-total-value");
    if (totalSpan) totalSpan.textContent = "R$ " + Number(newTotal).toFixed(2);
  }

  // Increase
  document.querySelectorAll(".cart-btn-increase").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const productId = btn.getAttribute("data-product-id");
      fetch("/cart/increase/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `product_id=${productId}`,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            updateQtyValue(btn, data.quantity);
            if (data.cart_total !== undefined) updateCartTotal(data.cart_total);
          }
        });
    });
  });

  // Decrease
  document.querySelectorAll(".cart-btn-decrease").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const productId = btn.getAttribute("data-product-id");
      fetch("/cart/decrease/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `product_id=${productId}`,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            if (data.quantity > 0) {
              updateQtyValue(btn, data.quantity);
              if (data.cart_total !== undefined)
                updateCartTotal(data.cart_total);
            } else {
              removeCartItemElement(btn);
              if (data.cart_total !== undefined)
                updateCartTotal(data.cart_total);
            }
          }
        });
    });
  });

  // Remove
  document.querySelectorAll(".cart-btn-remove").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const productId = btn.getAttribute("data-product-id");
      fetch("/cart/remove/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `product_id=${productId}`,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            removeCartItemElement(btn);
            if (data.cart_total !== undefined) updateCartTotal(data.cart_total);
          }
        });
    });
  });
});
