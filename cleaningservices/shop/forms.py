from django import forms
from .models import ProductReview


class ProductReviewForm(forms.ModelForm):
    """Form for customers to review products."""
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-input'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ProductSearchForm(forms.Form):
    """Form for searching products."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Search cleaning products...'
        })
    )
    category = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max'
        })
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Relevance'),
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('rating_desc', 'Best Rated'),
            ('newest', 'Newest First'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AffiliateClickForm(forms.Form):
    """Hidden form to track affiliate link clicks."""
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    redirect_url = forms.URLField(widget=forms.HiddenInput())