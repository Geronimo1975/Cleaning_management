from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ProductCategory(models.Model):
    """Categories for shop products."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='shop/categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='children')
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for the shop."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    features = models.JSONField(default=list, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amazon_asin = models.CharField(max_length=10, blank=True, null=True)
    amazon_url = models.URLField(blank=True, null=True)
    affiliate_tag = models.CharField(max_length=50, blank=True, null=True)
    image_main = models.ImageField(upload_to='shop/products/')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def affiliate_url(self):
        """Generate the complete affiliate URL."""
        if self.amazon_url and self.affiliate_tag:
            if '?' in self.amazon_url:
                return f"{self.amazon_url}&tag={self.affiliate_tag}"
            else:
                return f"{self.amazon_url}?tag={self.affiliate_tag}"
        return self.amazon_url


class ProductImage(models.Model):
    """Additional images for products."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/products/')
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.title}"


class ProductReview(models.Model):
    """Customer reviews for products."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.product.title}"


class ShopSettings(models.Model):
    """Global settings for the shop including Amazon affiliate ID."""
    amazon_affiliate_id = models.CharField(max_length=50, blank=True, null=True)
    display_sale_badge = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='EUR')
    shipping_info = models.TextField(blank=True)
    return_policy = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Shop Settings')
        verbose_name_plural = _('Shop Settings')
    
    def __str__(self):
        return "Shop Settings"


class AffiliatePartner(models.Model):
    """Affiliate marketing partners."""
    PLATFORM_CHOICES = [
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('walmart', 'Walmart'),
        ('otto', 'Otto'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default='amazon')
    affiliate_id = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True, null=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Affiliate Partner')
        verbose_name_plural = _('Affiliate Partners')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"


class AffiliateClick(models.Model):
    """Track affiliate link clicks for analytics."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='clicks')
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Click on {self.product.title} at {self.timestamp}"


class AffiliateConversion(models.Model):
    """Track confirmed affiliate conversions/sales."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='conversions')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversions')
    order_reference = models.CharField(max_length=100, blank=True, null=True)
    sale_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    click = models.ForeignKey(AffiliateClick, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversions')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Conversion: {self.product.title} - {self.sale_amount}"


class AffiliateAttributionCookie(models.Model):
    """Track affiliate attribution cookies for proper credit assignment."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.CASCADE)
    click = models.ForeignKey(AffiliateClick, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        user_id = self.user.id if self.user else self.session_key
        return f"Attribution: {self.product.title} for {user_id}"


class MarketingCampaign(models.Model):
    """Marketing campaigns for affiliate products."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.CASCADE, related_name='campaigns')
    products = models.ManyToManyField(Product, related_name='campaigns', blank=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name