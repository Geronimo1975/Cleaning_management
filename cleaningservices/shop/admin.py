from django.contrib import admin
from .models import (
    ProductCategory, Product, ProductImage, ProductReview, ShopSettings, 
    AffiliateClick, AffiliatePartner, AffiliateConversion, 
    AffiliateAttributionCookie, MarketingCampaign
)


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


@admin.register(AffiliatePartner)
class AffiliatePartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'affiliate_id', 'commission_rate', 'is_active')
    list_filter = ('platform', 'is_active', 'created_at')
    search_fields = ('name', 'affiliate_id', 'contact_person', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'platform', 'affiliate_id', 'website', 'is_active')
        }),
        ('Commission Settings', {
            'fields': ('commission_rate',)
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class AffiliateConversionInline(admin.TabularInline):
    model = AffiliateConversion
    extra = 0
    fields = ('product', 'partner', 'sale_amount', 'commission_amount', 'is_verified')
    readonly_fields = ('timestamp',)


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'partner', 'ip_address', 'timestamp')
    list_filter = ('timestamp', 'partner')
    search_fields = ('product__title', 'user__username', 'ip_address', 'utm_source', 'utm_campaign')
    readonly_fields = ['product', 'user', 'partner', 'ip_address', 'user_agent', 'referrer', 
                       'utm_source', 'utm_medium', 'utm_campaign', 'timestamp']
    inlines = [AffiliateConversionInline]
    
    def has_add_permission(self, request):
        return False


@admin.register(AffiliateConversion)
class AffiliateConversionAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'sale_amount', 'commission_amount', 'is_verified', 'timestamp')
    list_filter = ('is_verified', 'timestamp', 'partner')
    search_fields = ('product__title', 'user__username', 'order_reference')
    readonly_fields = ['timestamp']
    
    actions = ['mark_as_verified', 'mark_as_unverified']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} conversions marked as verified.")
    mark_as_verified.short_description = "Mark selected conversions as verified"
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} conversions marked as unverified.")
    mark_as_unverified.short_description = "Mark selected conversions as unverified"


@admin.register(AffiliateAttributionCookie)
class AffiliateAttributionCookieAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'partner', 'created_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'partner')
    search_fields = ('user__username', 'session_key', 'product__title')
    readonly_fields = ['created_at']
    
    actions = ['mark_as_inactive']
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} attribution cookies marked as inactive.")
    mark_as_inactive.short_description = "Mark selected cookies as inactive"


class ProductInline(admin.TabularInline):
    model = MarketingCampaign.products.through
    extra = 1
    verbose_name = "Product"
    verbose_name_plural = "Campaign Products"


@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'partner', 'start_date')
    search_fields = ('name', 'description', 'utm_source', 'utm_campaign')
    readonly_fields = ['created_at']
    exclude = ('products',)
    inlines = [ProductInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'partner', 'is_active')
        }),
        ('Campaign Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('UTM Parameters', {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_campaign', 'activate_campaigns', 'deactivate_campaigns']
    
    def duplicate_campaign(self, request, queryset):
        for campaign in queryset:
            # Create a copy of the campaign
            campaign.pk = None
            campaign.name = f"Copy of {campaign.name}"
            campaign.save()
            
            # Copy products
            original_campaign = MarketingCampaign.objects.get(name=campaign.name.replace("Copy of ", ""))
            for product in original_campaign.products.all():
                campaign.products.add(product)
            
            self.message_user(request, f"Campaign '{campaign.name}' has been duplicated.")
    duplicate_campaign.short_description = "Duplicate selected campaigns"
    
    def activate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} campaigns have been activated.")
    activate_campaigns.short_description = "Activate selected campaigns"
    
    def deactivate_campaigns(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} campaigns have been deactivated.")
    deactivate_campaigns.short_description = "Deactivate selected campaigns"