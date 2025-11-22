from django.db import models

# Create your models here.

class Product(models.Model):
    product_id=models.AutoField
    product_name=models.CharField(max_length=50)
    category=models.CharField(max_length=50, default="")
    subcategory=models.CharField(max_length=50, default="")
    price=models.IntegerField(default=0)
    desc=models.CharField(max_length=300)
    pub_date=models.DateField()
    image=models.ImageField(upload_to="shop/images", default="")

    def __str__(self):
            return self.product_name
        
class Contact(models.Model):
    msg_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email= models.CharField(max_length=80, default="")
    phone = models.CharField(max_length=15,default="")
    desc= models.CharField(max_length=800, default="")
    
    def __str__(self):
        return self.name

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cod_pending', 'COD Pending'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cc', 'Credit/Debit Card'),
        ('upi', 'UPI Payment'),
        ('cod', 'Cash on Delivery'),
    ]
    
    order_id = models.AutoField(primary_key=True)
    item_json = models.CharField(max_length=5000)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=70)
    zip_code = models.CharField(max_length=20)
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cc')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Shipping tracking number")
    shipping_date = models.DateField(blank=True, null=True, help_text="Date when order was shipped")
    expected_delivery_date = models.DateField(blank=True, null=True, help_text="Expected delivery date")
    delivered_date = models.DateField(blank=True, null=True, help_text="Actual delivery date")
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the order")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.name}"
    
    def get_total_items(self):
        """Calculate total number of items in order"""
        try:
            import json
            items = json.loads(self.item_json)
            total = 0
            for key, value in items.items():
                if isinstance(value, list) and len(value) > 0:
                    total += value[0]  # quantity is first element
            return total
        except:
            return 0
    
    def get_latest_update(self):
        """Get the latest order update"""
        return self.orderupdate_set.order_by('-timestamp').first()

class OrderUpdate(models.Model):
    STATUS_TYPE_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('payment_received', 'Payment Received'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('other', 'Other'),
    ]
    
    update_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderupdate_set', db_column='order_id', null=True, blank=True)
    update_desc = models.CharField(max_length=5000)
    status_type = models.CharField(max_length=20, choices=STATUS_TYPE_CHOICES, default='other', help_text="Type of status update")
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Tracking number if applicable")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Current location of shipment")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_customer_notified = models.BooleanField(default=False, help_text="Whether customer has been notified")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Order Update'
        verbose_name_plural = 'Order Updates'
    
    @property
    def order_id(self):
        """Backward compatibility property"""
        return self.order.order_id if self.order else None
    
    def __str__(self):
        order_id_val = self.order.order_id if self.order else 'N/A'
        return f"Update #{self.update_id} - Order #{order_id_val} - {self.update_desc[:50]}"