from django import forms
from .models import Document, DocumentCategory, DocumentComment, ChatConversation, ChatMessage


class DocumentForm(forms.ModelForm):
    """Form for uploading cleaning documents."""
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-role': 'tagsinput'}),
        help_text='Enter tags separated by commas'
    )
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file', 'access_level', 'document_type', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'access_level': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        
        # If instance exists, convert tags list to comma-separated string
        if self.instance.pk and self.instance.tags:
            self.initial['tags'] = ', '.join(self.instance.tags)
    
    def clean_tags(self):
        """Convert comma-separated tags to list."""
        tags_input = self.cleaned_data.get('tags', '')
        if tags_input:
            # Split by comma, strip whitespace, and filter out empty strings
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            return tags
        return []


class DocumentCategoryForm(forms.ModelForm):
    """Form for creating document categories."""
    class Meta:
        model = DocumentCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DocumentCommentForm(forms.ModelForm):
    """Form for adding comments to documents."""
    class Meta:
        model = DocumentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add your comment here...'}),
        }


class DocumentSearchForm(forms.Form):
    """Form for searching documents."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description or tags...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    document_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Document.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    

class ChatMessageForm(forms.Form):
    """Form for sending messages to the document chatbot."""
    message = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ask a question about this document or cleaning procedures...',
            'autocomplete': 'off'
        }),
        required=True
    )
    conversation_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )
    document_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )
