# Search Functionality Test Steps

## Overview
This document provides step-by-step instructions to verify that the search functionality is working correctly, including:
1. Add to Cart functionality on search results
2. Blog post "Read More" button functionality

## Prerequisites
- Django development server running at `http://127.0.0.1:8000`
- Browser with developer console open (F12)

---

## Test 1: Add to Cart Functionality on Search Results

### Step 1: Navigate to Search Page
1. Open your browser and go to `http://127.0.0.1:8000`
2. In the search box at the top, type a product name (e.g., "kurta", "shirt", "dress")
3. Click the search icon or press Enter
4. You should see search results page with URL: `http://127.0.0.1:8000/shop/search/?search=kurta`

### Step 2: Verify Products are Displayed
1. Check that product cards are visible in the "Products" section
2. Each product card should show:
   - Product image
   - Product name
   - Price (₹)
   - "Add to Cart" button

### Step 3: Test Add to Cart Button
1. Click the "Add to Cart" button on any product
2. **Expected Results:**
   - A success notification should appear (top-right corner)
   - The "Add to Cart" button should change to show quantity controls:
     - Minus button (-)
     - Quantity number (1)
     - Plus button (+)
   - The cart count in the navbar should increase (e.g., "Cart (1)")

### Step 4: Test Quantity Controls
1. Click the **Plus (+)** button
   - Quantity should increase to 2
   - Cart count in navbar should update
2. Click the **Minus (-)** button
   - Quantity should decrease to 1
   - Cart count should update
3. Click **Minus (-)** again when quantity is 1
   - Button should revert to "Add to Cart"
   - Item should be removed from cart
   - Cart count should decrease

### Step 5: Verify Cart Persistence
1. Add multiple different products to cart
2. Navigate to another page (e.g., Home or Shop)
3. Return to search results page
4. **Expected:** Previously added items should still show quantity controls (not "Add to Cart")
5. Check the cart count in navbar - it should match the total items

### Step 6: Verify Cart Popover
1. Click on the "Cart" button in the navbar
2. **Expected:** A popover should appear showing:
   - List of items in cart
   - Quantity and price for each item
   - Total items and total price
   - "View Cart" button
   - "Clear Cart" button

### Step 7: Test Multiple Products
1. Search for a different term (e.g., "shirt")
2. Add products from the new search results
3. **Expected:** All products should be in the cart together
4. Cart count should reflect total items from all searches

---

## Test 2: Blog Post "Read More" Functionality

### Step 1: Search for Blog Posts
1. In the search box, type a term that matches blog post content (e.g., "fashion", "style", "trends")
2. Click search
3. You should see a "Blog Posts" section if there are matching posts

### Step 2: Verify Blog Post Display
1. Check that blog post cards are visible
2. Each card should show:
   - Blog post thumbnail/image
   - Blog post title
   - Excerpt (first 150 characters)
   - "Read More" link with arrow icon

### Step 3: Test "Read More" Button
1. Click the "Read More" link on any blog post
2. **Expected Results:**
   - Page should navigate to the full blog post page
   - URL should be: `http://127.0.0.1:8000/blog/blogPost/{post_id}`
   - Full blog post content should be displayed
   - No 404 error should occur

### Step 4: Verify Navigation
1. After viewing a blog post, click browser back button
2. **Expected:** Should return to search results page
3. Search results should still be visible

---

## Test 3: Combined Search Results

### Step 1: Search for Common Term
1. Search for a term that matches both products and blog posts (e.g., "fashion")
2. **Expected:** Both "Products" and "Blog Posts" sections should appear

### Step 2: Test Both Functionalities
1. Add a product to cart from search results
2. Click "Read More" on a blog post
3. Return to search results
4. **Expected:** 
   - Product should still show in cart (quantity controls visible)
   - Can navigate to blog posts successfully
   - All functionality works together

---

## Debugging Steps (If Issues Occur)

### Issue: Add to Cart Button Not Working

1. **Open Browser Console (F12)**
   - Check for JavaScript errors (red text)
   - Look for "Search page cart functionality initialized successfully" message

2. **Check Button Structure:**
   - Right-click on "Add to Cart" button → Inspect
   - Verify button has:
     - `id="pr{product_id}"` (e.g., `id="pr1"`)
     - `class="btn btn-primary-custom btn-sm add-to-cart"`
     - `data-product-id="{id}"`
     - `data-product-name="Product Name"`
     - `data-product-price="{price}"`

3. **Check Container Div:**
   - Verify parent div has: `id="divpr{product_id}"` (e.g., `id="divpr1"`)

4. **Check localStorage:**
   - In console, type: `localStorage.getItem('cart')`
   - Should return JSON string with cart items
   - If null or empty, cart system may not be initialized

### Issue: Blog Post Link Not Working

1. **Check URL Pattern:**
   - Verify link href is: `/blog/blogPost/{post_id}`
   - Check that `{post_id}` is a valid number

2. **Check Blog URLs:**
   - Verify `blog/urls.py` has pattern: `path('blogPost/<int:id>', views.blogpost, name='blogPost')`
   - Verify main `urls.py` includes blog URLs: `path('blog/', include('blog.urls'))`

3. **Check Blog Post Exists:**
   - Go to Django admin: `http://127.0.0.1:8000/admin/blog/blogpost/`
   - Verify blog posts exist with valid IDs

### Issue: Cart Count Not Updating

1. **Check Cart Element:**
   - Verify navbar has element with `id="cart"`
   - In console: `document.getElementById('cart')` should return element

2. **Check Cart Data:**
   - In console: `JSON.parse(localStorage.getItem('cart'))`
   - Should show object with cart items
   - Format: `{"pr1": [quantity, name, price, size, color]}`

---

## Expected Console Output

When search page loads successfully, you should see in console:
```
Search page cart functionality initialized successfully
Current cart: {object with cart items or {}}
```

When clicking "Add to Cart", you should see:
- Success notification appears
- No JavaScript errors
- Cart count updates

---

## Success Criteria

✅ **Add to Cart works when:**
- Button click adds item to cart
- Button changes to quantity controls
- Cart count updates in navbar
- Cart persists across page navigation
- Multiple products can be added
- Quantity controls work (plus/minus)

✅ **Blog Post "Read More" works when:**
- Link navigates to correct blog post page
- No 404 errors occur
- Full blog post content displays
- Can navigate back to search results

✅ **Both work together when:**
- Can add products to cart
- Can navigate to blog posts
- Cart persists when navigating
- No conflicts between functionalities

---

## Notes

- Cart data is stored in browser's localStorage
- Cart persists across browser sessions (until cleared)
- Each browser has its own cart (localStorage is browser-specific)
- If testing in incognito/private mode, cart will be cleared when window closes

---

## Contact

If you encounter issues not covered in this guide:
1. Check browser console for errors
2. Verify Django server is running without errors
3. Check that all templates are properly saved
4. Clear browser cache and try again

