from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Avg
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone

from .models import Product, ProductCategory, ProductReview, AffiliateClick, ShopSettings
from .forms import ProductReviewForm, ProductSearchForm, AffiliateClickForm


class ProductListView(ListView):
    """View for listing products with filtering and search."""
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        form = ProductSearchForm(self.request.GET)
        
        if form.is_valid():
            # Search query
            query = form.cleaned_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(category__name__icontains=query)
                )
            
            # Category filter
            category_slug = form.cleaned_data.get('category')
            if category_slug:
                queryset = queryset.filter(
                    Q(category__slug=category_slug) |
                    Q(category__parent__slug=category_slug)
                )
            
            # Price range
            min_price = form.cleaned_data.get('min_price')
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
                
            max_price = form.cleaned_data.get('max_price')
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
                
            # Sorting
            sort_option = form.cleaned_data.get('sort')
            if sort_option == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort_option == 'price_desc':
                queryset = queryset.order_by('-price')
            elif sort_option == 'rating_desc':
                queryset = queryset.order_by('-rating')
            elif sort_option == 'newest':
                queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(parent=None)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['featured_products'] = Product.objects.filter(is_featured=True, is_active=True)[:4]
        return context


class ProductDetailView(DetailView):
    """View for displaying product details."""
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Related products
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        
        # Reviews
        context['reviews'] = product.reviews.all()
        
        # Review form
        if self.request.user.is_authenticated:
            # Check if user already reviewed
            existing_review = ProductReview.objects.filter(
                product=product,
                user=self.request.user
            ).first()
            
            if existing_review:
                context['review_form'] = ProductReviewForm(instance=existing_review)
                context['has_reviewed'] = True
            else:
                context['review_form'] = ProductReviewForm()
                context['has_reviewed'] = False
        
        # Affiliate click form
        context['affiliate_form'] = AffiliateClickForm(initial={
            'product_id': product.id,
            'redirect_url': product.affiliate_url or product.amazon_url
        })
        
        return context


@login_required
def submit_product_review(request, slug):
    """View for submitting product reviews."""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        # Check if user already reviewed
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user
        ).first()
        
        if existing_review:
            form = ProductReviewForm(request.POST, instance=existing_review)
            is_new = False
        else:
            form = ProductReviewForm(request.POST)
            is_new = True
        
        if form.is_valid():
            review = form.save(commit=False)
            if is_new:
                review.product = product
                review.user = request.user
            review.save()
            
            # Update product rating
            avg_rating = ProductReview.objects.filter(
                product=product
            ).aggregate(Avg('rating'))['rating__avg']
            
            product.rating = avg_rating
            product.save()
            
            messages.success(request, 'Your review has been submitted.')
        else:
            messages.error(request, 'There was an error submitting your review.')
    
    return redirect('product_detail', slug=slug)


def track_affiliate_click(request):
    """View for tracking affiliate link clicks."""
    if request.method == 'POST':
        form = AffiliateClickForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            redirect_url = form.cleaned_data['redirect_url']
            
            product = get_object_or_404(Product, id=product_id)
            
            # Record the click
            AffiliateClick.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            
            return HttpResponseRedirect(redirect_url)
    
    # If something goes wrong, redirect to shop
    return redirect('shop')


def shop_home(request):
    """Shop home page view."""
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    top_categories = ProductCategory.objects.annotate(
        num_products=Count('products')
    ).order_by('-num_products')[:6]
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'top_categories': top_categories,
        'search_form': ProductSearchForm(),
    }
    
    return render(request, 'shop/shop_home.html', context)


def category_view(request, slug):
    """View products by category."""
    category = get_object_or_404(ProductCategory, slug=slug)
    
    # Get initial queryset including subcategories
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_active=True
    )
    
    # Pre-fill search form with category
    initial_data = {'category': category.slug}
    form = ProductSearchForm(request.GET or None, initial=initial_data)
    
    if form.is_valid():
        # Apply additional filters from form
        query = form.cleaned_data.get('query')
        if query:
            products = products.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        # Price range
        min_price = form.cleaned_data.get('min_price')
        if min_price:
            products = products.filter(price__gte=min_price)
            
        max_price = form.cleaned_data.get('max_price')
        if max_price:
            products = products.filter(price__lte=max_price)
            
        # Sorting
        sort_option = form.cleaned_data.get('sort')
        if sort_option == 'price_asc':
            products = products.order_by('price')
        elif sort_option == 'price_desc':
            products = products.order_by('-price')
        elif sort_option == 'rating_desc':
            products = products.order_by('-rating')
        elif sort_option == 'newest':
            products = products.order_by('-created_at')
    
    context = {
        'category': category,
        'products': products,
        'subcategories': ProductCategory.objects.filter(parent=category),
        'search_form': form,
    }
    
    return render(request, 'shop/category.html', context)