// Cart functionality and application logic
class CartManager {
    constructor() {
        this.cart = [];
        this.init();
    }

    init() {
        this.renderProducts();
        this.bindEvents();
        this.initLucideIcons();
    }

    // Initialize Lucide icons
    initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // Product data
    getProducts() {
        return [
            {
                id: 1,
                name: "Galão de Água 20L",
                price: 12.50,
                image: "src/assets/galao-20l.jpg"
            },
            {
                id: 2,
                name: "Galão de Água 10L",
                price: 8.00,
                image: "src/assets/galao-10l.jpg"
            },
            {
                id: 3,
                name: "Pack 6 Garrafas 500ml",
                price: 15.90,
                image: "src/assets/pack-500ml.jpg"
            },
            {
                id: 4,
                name: "Bebedouro de Água",
                price: 180.00,
                image: "src/assets/bebedouro.jpg"
            },
            {
                id: 5,
                name: "Galão de Água 20L - Promoção",
                price: 10.00,
                image: "src/assets/galao-20l.jpg"
            },
            {
                id: 6,
                name: "Pack 12 Garrafas 500ml",
                price: 28.90,
                image: "src/assets/pack-500ml.jpg"
            }
        ];
    }

    // Render products grid
    renderProducts() {
        const productsGrid = document.getElementById('productsGrid');
        const products = this.getProducts();

        productsGrid.innerHTML = products.map((product, index) => `
            <div class="product-card" style="animation-delay: ${index * 0.1}s">
                <div class="product-image">
                    <img src="${product.image}" alt="${product.name}" loading="lazy">
                </div>
                <div class="product-info">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-price">${this.formatPrice(product.price)}</p>
                    <button class="add-to-cart-btn" data-product-id="${product.id}">
                        Adicionar ao Carrinho
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Bind event listeners
    bindEvents() {
        // Add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.add-to-cart-btn')) {
                const productId = parseInt(e.target.getAttribute('data-product-id'));
                this.addToCart(productId);
            }
        });

        // Cart button
        document.getElementById('cartButton').addEventListener('click', () => {
            this.openCart();
        });

        // Cart close button
        document.getElementById('cartClose').addEventListener('click', () => {
            this.closeCart();
        });

        // Cart overlay
        document.getElementById('cartOverlay').addEventListener('click', () => {
            this.closeCart();
        });

        // Quantity and remove buttons (event delegation)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.quantity-btn.minus') || e.target.closest('.quantity-btn.minus')) {
                const productId = parseInt(e.target.closest('.cart-item').dataset.productId);
                this.updateQuantity(productId, -1);
            }
            
            if (e.target.matches('.quantity-btn.plus') || e.target.closest('.quantity-btn.plus')) {
                const productId = parseInt(e.target.closest('.cart-item').dataset.productId);
                this.updateQuantity(productId, 1);
            }
            
            if (e.target.matches('.remove-btn') || e.target.closest('.remove-btn')) {
                const productId = parseInt(e.target.closest('.cart-item').dataset.productId);
                this.removeFromCart(productId);
            }
        });

        // ESC key to close cart
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeCart();
            }
        });
    }

    // Add product to cart
    addToCart(productId) {
        const products = this.getProducts();
        const product = products.find(p => p.id === productId);
        
        if (!product) return;

        const existingItem = this.cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({ ...product, quantity: 1 });
        }

        this.updateCartUI();
        this.showToast(product.name);
    }

    // Update quantity
    updateQuantity(productId, delta) {
        const item = this.cart.find(item => item.id === productId);
        
        if (!item) return;

        item.quantity += delta;

        if (item.quantity <= 0) {
            this.removeFromCart(productId);
        } else {
            this.updateCartUI();
        }
    }

    // Remove from cart
    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        this.updateCartUI();
    }

    // Update cart UI
    updateCartUI() {
        this.updateCartBadge();
        this.renderCartItems();
        this.updateCartTotal();
    }

    // Update cart badge
    updateCartBadge() {
        const badge = document.getElementById('cartBadge');
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        badge.textContent = totalItems;
        badge.classList.toggle('hidden', totalItems === 0);
    }

    // Render cart items
    renderCartItems() {
        const cartItems = document.getElementById('cartItems');
        const cartEmpty = document.getElementById('cartEmpty');
        const cartFooter = document.getElementById('cartFooter');

        if (this.cart.length === 0) {
            cartEmpty.style.display = 'block';
            cartItems.style.display = 'none';
            cartFooter.style.display = 'none';
            return;
        }

        cartEmpty.style.display = 'none';
        cartItems.style.display = 'block';
        cartFooter.style.display = 'block';

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item" data-product-id="${item.id}">
                <div class="cart-item-image">
                    <img src="${item.image}" alt="${item.name}">
                </div>
                <div class="cart-item-info">
                    <h4 class="cart-item-name">${item.name}</h4>
                    <p class="cart-item-price">${this.formatPrice(item.price)}</p>
                    <div class="cart-item-controls">
                        <button class="quantity-btn minus">
                            <i data-lucide="minus"></i>
                        </button>
                        <span class="quantity-display">${item.quantity}</span>
                        <button class="quantity-btn plus">
                            <i data-lucide="plus"></i>
                        </button>
                        <button class="remove-btn">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Re-initialize icons for new content
        this.initLucideIcons();
    }

    // Update cart total
    updateCartTotal() {
        const totalPrice = document.getElementById('totalPrice');
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        totalPrice.textContent = this.formatPrice(total);
    }

    // Open cart sidebar
    openCart() {
        document.getElementById('cartOverlay').classList.add('active');
        document.getElementById('cartSidebar').classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Close cart sidebar
    closeCart() {
        document.getElementById('cartOverlay').classList.remove('active');
        document.getElementById('cartSidebar').classList.remove('active');
        document.body.style.overflow = '';
    }

    // Show toast notification
    showToast(productName) {
        const toast = document.getElementById('toast');
        const toastTitle = document.getElementById('toastTitle');
        const toastDescription = document.getElementById('toastDescription');

        toastTitle.textContent = 'Produto adicionado!';
        toastDescription.textContent = `${productName} foi adicionado ao seu carrinho.`;

        toast.classList.add('active');

        setTimeout(() => {
            toast.classList.remove('active');
        }, 3000);
    }

    // Format price to Brazilian currency
    formatPrice(price) {
        return price.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CartManager();
});