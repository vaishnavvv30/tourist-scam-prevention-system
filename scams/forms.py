from django import forms
from .models import ScamReport, Bill


class ScamReportForm(forms.ModelForm):
    class Meta:
        model = ScamReport
        fields = [
            'title', 'description', 'category', 'severity',
            'location_name', 'latitude', 'longitude',
            'image', 'image2',
            'charged_amount', 'expected_amount', 'currency',
            'incident_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the scam incident'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what happened in detail...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location name or address'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'image2': forms.FileInput(attrs={'class': 'form-control'}),
            'charged_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount charged',
                'step': '0.01'
            }),
            'expected_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected fair price',
                'step': '0.01'
            }),
            'currency': forms.Select(
                choices=[
                    ('INR', 'INR (₹)'),
                    ('USD', 'USD ($)'),
                    ('EUR', 'EUR (€)'),
                    ('GBP', 'GBP (£)'),
                    ('THB', 'THB (฿)'),
                    ('JPY', 'JPY (¥)'),
                ],
                attrs={'class': 'form-select'}
            ),
            'incident_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class BillUploadForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['image', 'bill_type', 'location_name', 'total_amount', 'currency']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bill_type': forms.Select(attrs={'class': 'form-select'}),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where was this bill from?'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total amount on bill',
                'step': '0.01'
            }),
            'currency': forms.Select(
                choices=[
                    ('INR', 'INR (₹)'),
                    ('USD', 'USD ($)'),
                    ('EUR', 'EUR (€)'),
                    ('GBP', 'GBP (£)'),
                    ('THB', 'THB (฿)'),
                    ('JPY', 'JPY (¥)'),
                ],
                attrs={'class': 'form-select'}
            ),
        }


class PriceCheckForm(forms.Form):
    """Quick price verification form."""
    item_description = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Taxi from airport to hotel, 15km'
        })
    )
    price_charged = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount charged',
            'step': '0.01'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City name'
        })
    )
    currency = forms.ChoiceField(
        choices=[
            ('INR', 'INR (₹)'),
            ('USD', 'USD ($)'),
            ('EUR', 'EUR (€)'),
            ('GBP', 'GBP (£)'),
            ('THB', 'THB (฿)'),
            ('JPY', 'JPY (¥)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
