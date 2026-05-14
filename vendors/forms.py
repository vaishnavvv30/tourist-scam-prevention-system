from django import forms
from .models import Vendor, Review


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'name', 'category', 'description', 'image',
            'phone', 'email', 'website',
            'address', 'city', 'country',
            'latitude', 'longitude',
            'price_range', 'opening_hours',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor/Business name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe this vendor...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Website URL'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'price_range': forms.Select(attrs={'class': 'form-select'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 9:00 AM - 10:00 PM'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment', 'is_scam_related', 'visit_date', 'image']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1, 'max': 5,
                'placeholder': 'Rate 1-5'
            }),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Review title'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your experience...'}),
            'is_scam_related': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
