// Simple script to add test items to cart for checkout testing
function addTestItemsToCart() {
    // Sample products
    const testItems = {
        'p1': [2, 'Premium Cotton T-Shirt', 899, 'M', 'Black'],
        'p2': [1, 'Slim Fit Jeans', 1599, '32', 'Blue'],
        'p3': [3, 'Classic Sneakers', 2499, '42', 'White']
    };
    
    // Add items to localStorage
    localStorage.setItem('cart', JSON.stringify(testItems));
    
    console.log('Test items added to cart!');
    console.log('Cart contents:', testItems);
    
    // Reload the page to see changes
    location.reload();
}

// Run this function if the URL contains a test parameter
if (window.location.search.includes('?test')) {
    document.addEventListener('DOMContentLoaded', addTestItemsToCart);
}

// Add a global function so it can be called from console if needed
window.addTestItemsToCart = addTestItemsToCart;