from django.db import models
from django.utils.translation import gettext_lazy as _


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


class AffiliateClick(models.Model):
    """Track affiliate link clicks for analytics."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Click on {self.product.title} at {self.timestamp}"