const productsList = document.getElementById('productsGrid');
    const searchInput = document.getElementById('searchInput');

    function normalizeText(text) {
        return text
            .normalize("NFD") // separa acentos das letras
            .replace(/[\u0300-\u036f]/g, "") // remove os acentos
            .replace(/[^a-zA-Z0-9 ]/g, "") // remove outros caracteres especiais, exceto espaço
            .trim();
    }

    searchInput.addEventListener('input', () => {
        const searchTerm = normalizeText(searchInput.value).toLowerCase();
        const products = productsList.getElementsByClassName('product-card');
        let hasVisibleProduct = false;

        Array.from(products).forEach(product => {
            const productName = normalizeText(product.querySelector('.product-name').textContent).toLowerCase();
            if (productName.includes(searchTerm)) {
                product.style.display = '';
                hasVisibleProduct = true;
            } else {
                product.style.display = 'none';
            }
        });

        // Verifica se há produtos visíveis e exibe a mensagem caso contrário
        let noProductsMessage = document.getElementById('noProductsMessage');
        if (!hasVisibleProduct) {
            if (!noProductsMessage) {
                noProductsMessage = document.createElement('p');
                noProductsMessage.id = 'noProductsMessage';
                noProductsMessage.textContent = 'Nenhum produto encontrado.';
                noProductsMessage.style.textAlign = 'center';
                noProductsMessage.style.fontWeight = 'bold';
                productsList.appendChild(noProductsMessage);
            }
        } else if (noProductsMessage) {
            noProductsMessage.remove();
        }
    });