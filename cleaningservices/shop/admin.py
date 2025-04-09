from django.contrib import admin
from .models import ProductCategory, Product, ProductImage, ProductReview, ShopSettings, AffiliateClick


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ['user', 'rating', 'title', 'comment', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'sale_price', 'is_featured', 'is_active', 'created_at')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline, ProductReviewInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'description', 'features')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Amazon Affiliate', {
            'fields': ('amazon_asin', 'amazon_url', 'affiliate_tag')
        }),
        ('Images and Display', {
            'fields': ('image_main', 'rating', 'is_featured', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # If affiliate_tag is not set, use the global one from shop settings
        if not obj.affiliate_tag:
            try:
                settings = ShopSettings.objects.first()
                if settings and settings.amazon_affiliate_id:
                    obj.affiliate_tag = settings.amazon_affiliate_id
            except ShopSettings.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('title', 'comment', 'user__username', 'product__title')
    readonly_fields = ['created_at']


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one instance of ShopSettings
        return not ShopSettings.objects.exists()


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'ip_address', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('product__title', 'user__username', 'ip_address')
    readonly_fields = ['product', 'user', 'ip_address', 'user_agent', 'referrer', 'timestamp']
    
    def has_add_permission(self, request):
        return False