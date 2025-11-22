from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
import json

from .models import Product, Contact, Order, OrderUpdate


# Inline Admin for Order Updates
class OrderUpdateInline(admin.TabularInline):
    model = OrderUpdate
    extra = 1
    fields = ('status_type', 'update_desc', 'tracking_number', 'location', 'timestamp', 'is_customer_notified')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    class Media:
        css = {
            'all': ('admin/css/order_admin.css',)
        }


# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_info', 'order_status_badge', 'payment_status_badge', 'amount_display', 'total_items', 'created_at', 'tracking_link', 'actions_column')
    list_filter = ('order_status', 'payment_status', 'payment_method', 'created_at', 'city')
    search_fields = ('order_id', 'name', 'email', 'phone', 'tracking_number', 'address', 'city')
    readonly_fields = ('order_id', 'created_at', 'get_order_items_display', 'get_order_timeline')
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'order_status', 'created_at', 'amount')
        }),
        ('Customer Information', {
            'fields': ('name', 'email', 'phone', 'address', 'city', 'zip_code')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Shipping & Tracking', {
            'fields': ('tracking_number', 'shipping_date', 'expected_delivery_date', 'delivered_date')
        }),
        ('Order Items', {
            'fields': ('get_order_items_display',),
            'classes': ('collapse',)
        }),
        ('Order Timeline', {
            'fields': ('get_order_timeline',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderUpdateInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def save_model(self, request, obj, form, change):
        """Override save to automatically create OrderUpdate when order_status changes"""
        if change:  # Only for existing orders, not new ones
            try:
                # Get the original order from database
                original_order = Order.objects.get(pk=obj.pk)
                original_status = original_order.order_status
                new_status = obj.order_status
                
                # If order status changed, create an update
                if original_status != new_status:
                    status_messages = {
                        'pending': 'Order status set to Pending.',
                        'confirmed': 'Order has been confirmed and is being prepared for processing.',
                        'processing': 'Your order is being processed and prepared for shipment.',
                        'shipped': f'Your order has been shipped. Tracking number: {obj.tracking_number or "Will be updated soon"}.',
                        'out_for_delivery': 'Your order is out for delivery and will reach you soon.',
                        'delivered': 'Your order has been delivered successfully. Thank you for shopping with us!',
                        'cancelled': 'Order has been cancelled.',
                        'refunded': 'Order has been refunded.',
                    }
                    
                    status_types = {
                        'pending': 'order_placed',
                        'confirmed': 'order_confirmed',
                        'processing': 'processing',
                        'shipped': 'shipped',
                        'out_for_delivery': 'out_for_delivery',
                        'delivered': 'delivered',
                        'cancelled': 'cancelled',
                        'refunded': 'refunded',
                    }
                    
                    update_desc = status_messages.get(new_status, f'Order status changed to {obj.get_order_status_display()}.')
                    status_type = status_types.get(new_status, 'other')
                    
                    # Create order update
                    OrderUpdate.objects.create(
                        order=obj,
                        status_type=status_type,
                        update_desc=update_desc,
                        tracking_number=obj.tracking_number if new_status == 'shipped' else None,
                        location=obj.city if new_status in ['shipped', 'out_for_delivery'] else None
                    )
                
                # Also check if tracking_number was added/changed
                if obj.tracking_number and obj.tracking_number != original_order.tracking_number:
                    # Create update for tracking number
                    OrderUpdate.objects.create(
                        order=obj,
                        status_type='shipped' if new_status == 'shipped' else 'other',
                        update_desc=f'Tracking number updated: {obj.tracking_number}',
                        tracking_number=obj.tracking_number,
                        location=obj.city
                    )
                
                # Update delivered_date if status is delivered
                if new_status == 'delivered' and not obj.delivered_date:
                    from datetime import date
                    obj.delivered_date = date.today()
                
                # Update shipping_date if status is shipped
                if new_status == 'shipped' and not obj.shipping_date:
                    from datetime import date
                    obj.shipping_date = date.today()
                    
            except Order.DoesNotExist:
                # New order, no need to check for changes
                pass
            except Exception as e:
                # Log error but don't prevent save
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating order update: {e}")
        
        # Save the order
        super().save_model(request, obj, form, change)
    
    def customer_info(self, obj):
        return format_html(
            '<strong>{}</strong><br>'
            '<small>{}</small><br>'
            '<small>{}</small>',
            obj.name,
            obj.email,
            obj.phone
        )
    customer_info.short_description = 'Customer'
    
    def order_status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'processing': '#8b5cf6',
            'shipped': '#06b6d4',
            'out_for_delivery': '#10b981',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
            'refunded': '#6b7280',
        }
        color = colors.get(obj.order_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_order_status_display()
        )
    order_status_badge.short_description = 'Order Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'paid': '#10b981',
            'cod_pending': '#3b82f6',
            'failed': '#ef4444',
            'refunded': '#6b7280',
        }
        color = colors.get(obj.payment_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    
    def amount_display(self, obj):
        formatted_amount = f"{obj.amount:,}"
        return format_html('<strong>₹{}</strong>', formatted_amount)
    amount_display.short_description = 'Amount'
    
    def total_items(self, obj):
        return obj.get_total_items()
    total_items.short_description = 'Items'
    
    def tracking_link(self, obj):
        try:
            if obj.tracking_number:
                tracking_display = obj.tracking_number[:20] + '...' if len(obj.tracking_number) > 20 else obj.tracking_number
                tracker_url = f'/shop/tracker/?order_id={obj.order_id}'
                return format_html(
                    '<a href="{}" target="_blank" style="color: #3b82f6;">{}</a>',
                    tracker_url,
                    tracking_display
                )
        except Exception:
            pass
        return format_html('<span style="color: #9ca3af;">No tracking</span>')
    tracking_link.short_description = 'Tracking'
    
    def actions_column(self, obj):
        return format_html(
            '<a href="{}" class="button" style="padding: 4px 8px; background: #3b82f6; color: white; text-decoration: none; border-radius: 4px; font-size: 11px;">View</a>',
            reverse('admin:shop_order_change', args=[obj.pk])
        )
    actions_column.short_description = 'Actions'
    
    def get_order_items_display(self, obj):
        try:
            items = json.loads(obj.item_json)
            html = '<div style="max-height: 400px; overflow-y: auto;">'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '<thead><tr style="background: #f3f4f6;"><th style="padding: 8px; text-align: left; border: 1px solid #e5e7eb;">Item</th><th style="padding: 8px; text-align: center; border: 1px solid #e5e7eb;">Qty</th><th style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;">Price</th><th style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;">Total</th></tr></thead>'
            html += '<tbody>'
            total = 0
            for key, value in items.items():
                if isinstance(value, list) and len(value) >= 3:
                    qty = value[0]
                    name = value[1]
                    price = value[2]
                    size = value[3] if len(value) > 3 else ''
                    color = value[4] if len(value) > 4 else ''
                    item_total = qty * price
                    total += item_total
                    variant = ''
                    if size or color:
                        variant = f'<br><small style="color: #6b7280;">Size: {size}, Color: {color}</small>'
                    price_formatted = f"{price:,}"
                    item_total_formatted = f"{item_total:,}"
                    html += f'<tr><td style="padding: 8px; border: 1px solid #e5e7eb;">{name}{variant}</td><td style="padding: 8px; text-align: center; border: 1px solid #e5e7eb;">{qty}</td><td style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;">₹{price_formatted}</td><td style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;"><strong>₹{item_total_formatted}</strong></td></tr>'
            html += '</tbody>'
            total_formatted = f"{total:,}"
            html += f'<tfoot><tr style="background: #f9fafb;"><td colspan="3" style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;"><strong>Total:</strong></td><td style="padding: 8px; text-align: right; border: 1px solid #e5e7eb;"><strong>₹{total_formatted}</strong></td></tr></tfoot>'
            html += '</table></div>'
            return mark_safe(html)
        except:
            return 'Unable to parse order items'
    get_order_items_display.short_description = 'Order Items'
    
    def get_order_timeline(self, obj):
        try:
            updates = obj.orderupdate_set.all().order_by('-timestamp')
            if not updates:
                return 'No updates yet'
            html = '<div style="max-height: 400px; overflow-y: auto;">'
            html += '<div style="position: relative; padding-left: 30px;">'
            for update in updates:
                status_colors = {
                    'order_placed': '#3b82f6',
                    'order_confirmed': '#10b981',
                    'payment_received': '#10b981',
                    'processing': '#8b5cf6',
                    'packed': '#06b6d4',
                    'shipped': '#06b6d4',
                    'in_transit': '#f59e0b',
                    'out_for_delivery': '#f59e0b',
                    'delivered': '#10b981',
                    'cancelled': '#ef4444',
                    'refunded': '#6b7280',
                }
                color = status_colors.get(update.status_type, '#6b7280')
                location_html = f'<div style="color: #6b7280; font-size: 12px; margin-top: 4px;"><i class="fas fa-map-marker-alt"></i> {update.location}</div>' if update.location else ''
                tracking_html = f'<div style="color: #3b82f6; font-size: 11px; margin-top: 4px;"><i class="fas fa-truck"></i> Tracking: {update.tracking_number}</div>' if update.tracking_number else ''
                timestamp_str = update.timestamp.strftime("%d %b %Y, %I:%M %p") if update.timestamp else 'N/A'
                html += f'''
                <div style="position: relative; padding-bottom: 20px;">
                    <div style="position: absolute; left: -25px; top: 5px; width: 12px; height: 12px; border-radius: 50%; background: {color}; border: 2px solid white; box-shadow: 0 0 0 2px {color};"></div>
                    <div style="background: #f9fafb; padding: 12px; border-radius: 8px; border-left: 3px solid {color};">
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">{update.get_status_type_display()}</div>
                        <div style="color: #6b7280; font-size: 13px; margin-bottom: 4px;">{update.update_desc}</div>
                        <div style="color: #9ca3af; font-size: 11px;">{timestamp_str}</div>
                        {location_html}
                        {tracking_html}
                    </div>
                </div>
                '''
            html += '</div></div>'
            return mark_safe(html)
        except Exception as e:
            return f'Error loading timeline: {str(e)}'
    get_order_timeline.short_description = 'Order Timeline'
    
    # Admin Actions
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(order_status='confirmed')
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                status_type='order_confirmed',
                update_desc='Order has been confirmed and is being prepared for processing.'
            )
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected orders as Confirmed'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(order_status='processing')
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                status_type='processing',
                update_desc='Your order is being processed and prepared for shipment.'
            )
        self.message_user(request, f'{updated} order(s) marked as Processing.')
    mark_as_processing.short_description = 'Mark selected orders as Processing'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(order_status='shipped')
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                status_type='shipped',
                update_desc=f'Your order has been shipped. Tracking number: {order.tracking_number or "N/A"}'
            )
        self.message_user(request, f'{updated} order(s) marked as Shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as Shipped'
    
    def mark_as_delivered(self, request, queryset):
        from datetime import date
        updated = queryset.update(order_status='delivered', delivered_date=date.today())
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                status_type='delivered',
                update_desc='Your order has been delivered successfully. Thank you for shopping with us!'
            )
        self.message_user(request, f'{updated} order(s) marked as Delivered.')
    mark_as_delivered.short_description = 'Mark selected orders as Delivered'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(order_status='cancelled')
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                status_type='cancelled',
                update_desc='Order has been cancelled.'
            )
        self.message_user(request, f'{updated} order(s) marked as Cancelled.')
    mark_as_cancelled.short_description = 'Mark selected orders as Cancelled'


# Note: OrderUpdate is managed inline through OrderAdmin
# No standalone admin needed - admins can add/edit updates from the Order detail page


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'subcategory', 'price', 'pub_date')
    list_filter = ('category', 'subcategory', 'pub_date')
    search_fields = ('product_name', 'category', 'subcategory', 'desc')
    ordering = ('-pub_date',)


# Contact Admin
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('msg_id', 'name', 'email', 'phone', 'desc_short')
    list_filter = ('msg_id',)
    search_fields = ('name', 'email', 'phone', 'desc')
    readonly_fields = ('msg_id',)
    
    def desc_short(self, obj):
        return obj.desc[:50] + '...' if len(obj.desc) > 50 else obj.desc
    desc_short.short_description = 'Message'
