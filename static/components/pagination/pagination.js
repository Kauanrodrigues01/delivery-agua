/* 
 * Global Pagination Component JavaScript
 * Used across multiple templates for consistent pagination behavior
 */

/**
 * Initialize pagination smooth scroll functionality
 * @param {string} targetSelector - CSS selector for the section to scroll to
 */
function initializePaginationScroll(targetSelector) {
    document.addEventListener('DOMContentLoaded', function () {
        const paginationLinks = document.querySelectorAll('.pagination .page-link');
        
        paginationLinks.forEach(link => {
            link.addEventListener('click', function (e) {
                // Add a small delay to allow the page to load
                setTimeout(() => {
                    const targetSection = document.querySelector(targetSelector);
                    if (targetSection) {
                        targetSection.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }, 100);
            });
        });
    });
}

/**
 * Update URL parameters for pagination and search
 * @param {Object} params - Object containing URL parameters to update
 * @param {boolean} removePage - Whether to remove the page parameter (default: true)
 */
function updatePaginationURL(params, removePage = true) {
    const url = new URL(window.location.href);
    
    // Update or remove parameters
    Object.keys(params).forEach(key => {
        if (params[key]) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    // Remove page parameter when updating filters (to go back to page 1)
    if (removePage) {
        url.searchParams.delete('page');
    }
    
    window.location.href = url;
}

/**
 * Get current URL parameters
 * @returns {Object} Object containing current URL parameters
 */
function getCurrentURLParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const params = {};
    
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
    }
    
    return params;
}

/**
 * Initialize search functionality with debounce
 * @param {string} inputSelector - CSS selector for the search input
 * @param {Array} additionalFilters - Array of additional filter selectors to preserve
 * @param {number} debounceDelay - Delay in milliseconds for debounce (default: 500)
 */
function initializePaginationSearch(inputSelector, additionalFilters = [], debounceDelay = 500) {
    document.addEventListener('DOMContentLoaded', function () {
        const searchInput = document.querySelector(inputSelector);
        
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', function () {
                clearTimeout(searchTimeout);
                
                searchTimeout = setTimeout(() => {
                    const searchValue = searchInput.value.trim();
                    const currentParams = getCurrentURLParams();
                    const currentSearch = currentParams.search || '';
                    
                    if (searchValue !== currentSearch) {
                        const params = { search: searchValue };
                        
                        // Preserve additional filters
                        additionalFilters.forEach(filterName => {
                            const filterElement = document.querySelector(`[data-filter="${filterName}"], #${filterName}Filter, select[name="${filterName}"]`);
                            if (filterElement) {
                                params[filterName] = filterElement.value;
                            }
                        });
                        
                        updatePaginationURL(params);
                    }
                }, debounceDelay);
            });
        }
    });
}
