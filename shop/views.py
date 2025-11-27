from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Product,Contact,Order,OrderUpdate
from blog.models import BlogPost
from math import ceil
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Create your views here.
def index(request):
    # products = Product.objects.all()
    # n = len(products)
    # nSlides= n//4 + ceil((n/4)-(n/4))
    # params={'no_of_slides':nSlides, 'range':range(1,nSlides),'product':products}
    
    allProds = []
    catprods= Product.objects.values('category','id')
    cats = {item ['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n/4)-(n//4))
        allProds.append([prod,range(1,nSlides) ,nSlides])
   
    params = {'allProds': allProds}
    return render(request,'shop/index.html',params)

def search(request):
    """
    Enhanced search functionality that searches across:
    - Products (name, description, category, subcategory)
    - Blog Posts (title, content)
    - Categories
    """
    query = request.GET.get('search', '').strip()
    
    # Initialize result containers
    products = Product.objects.none()  # Empty QuerySet
    blog_posts = BlogPost.objects.none()  # Empty QuerySet
    categories = []
    allProds = []
    
    # Only search if query is provided and has at least 2 characters
    if query and len(query) >= 2:
        # Search Products using Q objects for better performance
        product_query = Q(product_name__icontains=query) | \
                       Q(desc__icontains=query) | \
                       Q(category__icontains=query) | \
                       Q(subcategory__icontains=query)
        
        products = Product.objects.filter(product_query).distinct()
        
        # Search Blog Posts
        blog_query = Q(title__icontains=query) | \
                    Q(head0__icontains=query) | \
                    Q(chead0__icontains=query) | \
                    Q(head1__icontains=query) | \
                    Q(chead1__icontains=query) | \
                    Q(head2__icontains=query) | \
                    Q(chead2__icontains=query) | \
                    Q(conclusion__icontains=query)
        
        blog_posts = BlogPost.objects.filter(blog_query).distinct()
        
        # Get unique categories that match the query
        matching_categories = Product.objects.filter(
            category__icontains=query
        ).values_list('category', flat=True).distinct()
        categories = list(matching_categories)
        
        # Organize products by category for display (similar to index page)
        if products.exists():
            catprods = products.values('category', 'id')
            cats = {item['category'] for item in catprods}
            for cat in cats:
                prod = products.filter(category=cat)
                n = prod.count()
                nSlides = n // 4 + ceil((n / 4) - (n // 4))
                if n > 0:
                    allProds.append([prod, range(1, nSlides), nSlides])
    
    # Prepare context - use count() for QuerySets to avoid unnecessary evaluation
    product_count = products.count()
    blog_count = blog_posts.count()
    category_count = len(categories)
    total_results = product_count + blog_count + category_count
    
    params = {
        'query': query,
        'allProds': allProds,
        'products': products,
        'blog_posts': blog_posts,
        'categories': categories,
        'total_results': total_results,
        'product_count': product_count,
        'blog_count': blog_count,
        'category_count': category_count,
        'has_results': total_results > 0,
        'msg': '' if (query and len(query) >= 2) else 'Please enter at least 2 characters to search'
    }
    
    # Show message if no results found
    if query and len(query) >= 2 and total_results == 0:
        params['msg'] = f'No results found for "{query}". Try different keywords or check your spelling.'
    
    return render(request, 'shop/search.html', params)


def productView(request, myid):
    # Fetch the product using the id
    product = get_object_or_404(Product, id=myid)
    return render(request, 'shop/prodView.html', {'product': product})
def mencat(request):
    # Fetch products with the subcategory "Men's Fashion"
    category = "Men's Fashion"
    prods = Product.objects.filter(category=category)
    
    # Divide the products into rows of 4
    n = len(prods)
    nSlides = n // 4 + ceil((n / 4) - (n // 4))
    allProds = [prods[i:i + 4] for i in range(0, n, 4)]  # Fix the range
    ran=len(allProds)
    params = {'allProds': allProds, 'ran':ran}
    # print(params)
    return render(request, 'shop/men.html', params)
def womencat(request):
    # Fetch products with the subcategory "Women's Fashion"
    category = "Women's Fashion"
    prods = Product.objects.filter(category=category)
    
    # Divide the products into rows of 4
    n = len(prods)
    nSlides = n // 4 + ceil((n / 4) - (n // 4))
    allProds = [prods[i:i + 4] for i in range(0, n, 4)]  # Fix the range
    ran=len(allProds)
    params = {'allProds': allProds, 'ran':ran}
    # print(params)
    return render(request, 'shop/women.html', params)
def kidscat(request):
    # Fetch products with the subcategory "kid's Fashion"
    category = "Kids Wear"
    prods = Product.objects.filter(category=category)
    
    # Divide the products into rows of 4
    n = len(prods)
    nSlides = n // 4 + ceil((n / 4) - (n // 4))
    allProds = [prods[i:i + 4] for i in range(0, n, 4)]  # Fix the range
    ran=len(allProds)
    params = {'allProds': allProds, 'ran':ran}
    # print(params)
    return render(request, 'shop/kids.html', params)
def cart(request):
    if request.method == "POST":
        # Process order when form is submitted
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        phone = request.POST.get('phone', '')
        city = request.POST.get('city', '')
        zip_code = request.POST.get('zip_code', '')
        
        # Save order to database
        order = Order(
            item_json=items_json,
            name=name,
            email=email,
            address=address,
            phone=phone,
            city=city,
            zip_code=zip_code
        )
        order.save()
        
        # Create order update
        update = OrderUpdate(
            order=order,
            status_type='order_placed',
            update_desc="The order has been placed"
        )
        update.save()
        
        # Show success message with order ID
        return render(request, 'shop/cart.html', {
            'thank': True,
            'id': order.order_id
        })
    
    # For GET requests, check if there's a cart in the session
    # This helps with maintaining cart state across different scenarios
    if 'cart' not in request.session:
        request.session['cart'] = {}
    
    # Return the cart page with basic context
    return render(request, 'shop/cart.html', {
        'cart_exists': True
    })

@login_required(login_url='account:login')
def checkout(request):
    if request.method=="POST":
        # Get form data
        items_json = request.POST.get('itemsJson','')
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        # Always tie order to the logged-in user's email so it appears in My Orders
        try:
            if request.user and request.user.is_authenticated and request.user.email:
                email = request.user.email
        except Exception:
            pass
        phone = request.POST.get('phone','')
        address1 = request.POST.get('address1','')
        address2 = request.POST.get('address2','')
        address = address1 + " " + address2
        city = request.POST.get('city','')
        zip_code = request.POST.get('zip_code','')
        payment = request.POST.get('payment','cc')
        order_total = request.POST.get('order_total', '0')
        try:
            amount_int = int(order_total)
        except Exception:
            amount_int = 0
        
        # Create order
        order = Order(
            item_json=items_json,
            name=name,
            email=email,
            address=address,
            phone=phone,
            city=city,
            zip_code=zip_code,
            amount=amount_int,
            payment_method=payment,
            payment_status=('cod_pending' if payment=='cod' else 'pending')
        )
        order.save()
        
        # Create order update
        update_desc = "The order has been placed"
        status_type = 'order_placed'
        if payment == 'cod':
            update_desc = "Order placed with Cash on Delivery"
        update = OrderUpdate(
            order=order,
            status_type=status_type,
            update_desc=update_desc
        )
        update.save()
        
        # Secure: Save order ID to session to verify ownership in success page
        request.session['last_order_id'] = order.order_id
        
        # Handle different payment methods
        if payment == 'cod':
            # Cash on Delivery - show confirmation page
            return render(request, 'shop/cod_confirmation.html', {
                'order_id': order.order_id,
                'name': name,
                'address': address,
                'city': city,
                'zip': zip_code
            })
        elif payment == 'upi':
            # UPI Payment - redirect to UPI payment page
            return render(request, 'shop/upi_payment.html', {
                'order_id': order.order_id,
                'amount': amount_int,
                'name': name
            })
        elif payment == 'cc':
            # Credit Card Payment - redirect to card payment processing page
            card_number = request.POST.get('card_number', '').replace(' ', '')
            expiry = request.POST.get('expiry', '')
            cvv = request.POST.get('cvv', '')
            card_name = request.POST.get('card_name', name)
            
            return render(request, 'shop/card_payment.html', {
                'order_id': order.order_id,
                'amount': amount_int,
                'name': name,
                'card_number': card_number,
                'expiry': expiry,
                'cvv': cvv,
                'card_name': card_name
            })
        else:
            # Default - return success response
            return render(request, 'shop/modern_checkout.html', {
                'order_id': order.order_id,
                'success': True
            })
    
    # For GET requests, render our modern checkout template
    return render(request, 'shop/modern_checkout.html')

@login_required(login_url='account:login')
def upi_payment_success(request):
    """Handle UPI payment success callback"""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(order_id=order_id)
            # Update payment status to paid
            order.payment_status = 'paid'
            order.save()
            
            # Create order update
            update = OrderUpdate(
                order=order,
                status_type='payment_received',
                update_desc="Payment received via UPI. Order confirmed."
            )
            update.save()
            
            return HttpResponse(json.dumps({'success': True}), content_type='application/json')
        except Order.DoesNotExist:
            return HttpResponse(json.dumps({'success': False, 'error': 'Order not found'}), content_type='application/json')
    return HttpResponse(json.dumps({'success': False, 'error': 'Invalid request'}), content_type='application/json')

@login_required(login_url='account:login')
def card_payment_success(request):
    """Handle credit card payment success callback"""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        card_last4 = request.POST.get('card_last4', '')
        try:
            order = Order.objects.get(order_id=order_id)
            # Update payment status to paid
            order.payment_status = 'paid'
            order.save()
            
            # Create order update
            update_desc = "Payment received via Credit/Debit Card. Order confirmed."
            if card_last4:
                update_desc += f" Card ending in {card_last4}."
            update = OrderUpdate(
                order=order,
                status_type='payment_received',
                update_desc=update_desc
            )
            update.save()
            
            return HttpResponse(json.dumps({'success': True}), content_type='application/json')
        except Order.DoesNotExist:
            return HttpResponse(json.dumps({'success': False, 'error': 'Order not found'}), content_type='application/json')
    return HttpResponse(json.dumps({'success': False, 'error': 'Invalid request'}), content_type='application/json')

def order_success(request):
    """Display order success page"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(order_id=order_id)
            
            # Security Check: Verify ownership (IDOR Prevention)
            # Allow if user is authenticated and email matches OR if order ID matches the one just placed in this session
            is_owner = False
            if request.user.is_authenticated and order.email == request.user.email:
                is_owner = True
            elif str(order.order_id) == str(request.session.get('last_order_id')):
                is_owner = True
                
            if not is_owner:
                # If not owner, return empty/fallback to prevent data leakage
                raise Order.DoesNotExist

            # Determine payment method display name
            payment_methods = {
                'cc': 'Credit/Debit Card',
                'upi': 'UPI Payment',
                'cod': 'Cash on Delivery'
            }
            payment_method_display = payment_methods.get(order.payment_method, 'Online Payment')
            
            return render(request, 'shop/order_success.html', {
                'order_id': order.order_id,
                'amount': order.amount,
                'payment_method': payment_method_display,
                'payment_icon': 'fa-credit-card' if order.payment_method == 'cc' else 'fa-mobile-alt' if order.payment_method == 'upi' else 'fa-money-bill-wave'
            })
        except Order.DoesNotExist:
            pass
    # Fallback if order not found
    return render(request, 'shop/order_success.html', {
        'order_id': order_id or 'N/A',
        'amount': 0,
        'payment_method': 'Online Payment',
        'payment_icon': 'fa-credit-card'
    })

def tracker(request):
    # Handle AJAX POST requests for tracking
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Order.objects.filter(order_id=orderId, email=email)
            if len(order) > 0:
                update = OrderUpdate.objects.filter(order__order_id=orderId).order_by('timestamp')
                updates = []
                for item in update:
                    updates.append({
                        'text': item.update_desc, 
                        'time': item.timestamp,
                        'status_type': item.status_type,
                        'tracking_number': item.tracking_number or '',
                        'location': item.location or ''
                    })
                response = json.dumps({
                    "status": "success", 
                    "updates": updates, 
                    "itemsJson": order[0].item_json,
                    "order": {
                        "order_id": order[0].order_id,
                        "amount": order[0].amount,
                        "name": order[0].name,
                        "address": order[0].address,
                        "city": order[0].city,
                        "zip_code": order[0].zip_code,
                        "phone": order[0].phone,
                        "payment_method": order[0].payment_method,
                        "payment_status": order[0].payment_status,
                        "order_status": order[0].order_status,
                        "tracking_number": order[0].tracking_number or "",
                        "created_at": str(order[0].created_at) if order[0].created_at else None
                    }
                }, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')
    
    # Handle GET requests - check if order_id is in URL
    order_id = request.GET.get('order_id')
    order = None
    updates = []
    order_items = []
    
    if order_id:
        try:
            # If user is logged in, try to get order by order_id and email
            if request.user.is_authenticated and request.user.email:
                order = Order.objects.filter(order_id=order_id, email=request.user.email).first()
            else:
                # If not logged in, we'll need email from form
                pass
        except:
            pass
    
    return render(request, 'shop/tracker.html', {
        'order': order,
        'updates': updates,
        'order_items': order_items,
        'order_id_param': order_id
    })
def about(request):
     return render(request, 'shop/about.html')
def contact(request):
    if request.method=="POST":
        name=request.POST.get('name','')
        email=request.POST.get('email','')
        phone=request.POST.get('phonenumber','')
        desc=request.POST.get('desc','')
        
        # Input Validation
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_regex = r'^\+?1?\d{9,15}$'
        
        if not re.match(email_regex, email):
            return HttpResponse("Invalid Email Address")
        if not re.match(phone_regex, phone):
            return HttpResponse("Invalid Phone Number")
            
        contact=Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
    return render(request, 'shop/contact.html')
def login(request):
     return render(request, 'shop/login.html')

