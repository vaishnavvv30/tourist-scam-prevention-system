from django import forms
from .models import Trip, Location

class TripPlannerForm(forms.Form):
    """Trip planning form with free-text destination that auto-creates Location objects."""
    destination = forms.CharField(
        max_length=200,
        label="Destination",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Idukki, Munnar, Wayanad, Goa...',
            'autocomplete': 'off',
        })
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    budget = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5000'})
    )
    group_type = forms.ChoiceField(
        choices=Trip.GROUP_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preferences = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'e.g. waterfalls, trekking, safe food',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be before start date.")
        return cleaned_data

    def save(self, user):
        """Create the Trip with an auto-created Location."""
        data = self.cleaned_data
        # Get or create the location from the text input
        location, _ = Location.objects.get_or_create(
            name__iexact=data['destination'].strip(),
            defaults={'name': data['destination'].strip()}
        )
        duration_days = (data['end_date'] - data['start_date']).days + 1
        trip = Trip.objects.create(
            user=user,
            destination=location,
            start_date=data['start_date'],
            end_date=data['end_date'],
            duration_days=duration_days,
            budget=data['budget'],
            group_type=data['group_type'],
            preferences=data.get('preferences', ''),
        )
        return trip
