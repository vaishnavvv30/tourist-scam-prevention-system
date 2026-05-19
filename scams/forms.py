from django import forms
from .models import ScamReport, Bill

ALL_CURRENCIES = [
    ('AED', 'AED (د.إ)'), ('AFN', 'AFN (؋)'), ('ALL', 'ALL (L)'), ('AMD', 'AMD (֏)'),
    ('ANG', 'ANG (ƒ)'), ('AOA', 'AOA (Kz)'), ('ARS', 'ARS ($)'), ('AUD', 'AUD ($)'),
    ('AWG', 'AWG (ƒ)'), ('AZN', 'AZN (₼)'), ('BAM', 'BAM (KM)'), ('BBD', 'BBD ($)'),
    ('BDT', 'BDT (৳)'), ('BGN', 'BGN (лв)'), ('BHD', 'BHD (.د.ب)'), ('BIF', 'BIF (FBu)'),
    ('BMD', 'BMD ($)'), ('BND', 'BND ($)'), ('BOB', 'BOB (Bs.)'), ('BRL', 'BRL (R$)'),
    ('BSD', 'BSD ($)'), ('BTN', 'BTN (Nu.)'), ('BWP', 'BWP (P)'), ('BYN', 'BYN (Br)'),
    ('BZD', 'BZD ($)'), ('CAD', 'CAD ($)'), ('CDF', 'CDF (FC)'), ('CHF', 'CHF (Fr)'),
    ('CLP', 'CLP ($)'), ('CNY', 'CNY (¥)'), ('COP', 'COP ($)'), ('CRC', 'CRC (₡)'),
    ('CUP', 'CUP ($)'), ('CVE', 'CVE ($)'), ('CZK', 'CZK (Kč)'), ('DJF', 'DJF (Fdj)'),
    ('DKK', 'DKK (kr)'), ('DOP', 'DOP ($)'), ('DZD', 'DZD (د.ج)'), ('EGP', 'EGP (£)'),
    ('ERN', 'ERN (Nfk)'), ('ETB', 'ETB (Br)'), ('EUR', 'EUR (€)'), ('FJD', 'FJD ($)'),
    ('FKP', 'FKP (£)'), ('GBP', 'GBP (£)'), ('GEL', 'GEL (₾)'), ('GHS', 'GHS (₵)'),
    ('GIP', 'GIP (£)'), ('GMD', 'GMD (D)'), ('GNF', 'GNF (FG)'), ('GTQ', 'GTQ (Q)'),
    ('GYD', 'GYD ($)'), ('HKD', 'HKD ($)'), ('HNL', 'HNL (L)'), ('HRK', 'HRK (kn)'),
    ('HTG', 'HTG (G)'), ('HUF', 'HUF (Ft)'), ('IDR', 'IDR (Rp)'), ('ILS', 'ILS (₪)'),
    ('INR', 'INR (₹)'), ('IQD', 'IQD (ع.د)'), ('IRR', 'IRR (﷼)'), ('ISK', 'ISK (kr)'),
    ('JMD', 'JMD ($)'), ('JOD', 'JOD (د.ا)'), ('JPY', 'JPY (¥)'), ('KES', 'KES (KSh)'),
    ('KGS', 'KGS (som)'), ('KHR', 'KHR (៛)'), ('KMF', 'KMF (CF)'), ('KPW', 'KPW (₩)'),
    ('KRW', 'KRW (₩)'), ('KWD', 'KWD (د.ك)'), ('KYD', 'KYD ($)'), ('KZT', 'KZT (₸)'),
    ('LAK', 'LAK (₭)'), ('LBP', 'LBP (ل.ل)'), ('LKR', 'LKR (₨)'), ('LRD', 'LRD ($)'),
    ('LSL', 'LSL (L)'), ('LYD', 'LYD (ل.د)'), ('MAD', 'MAD (د.م.)'), ('MDL', 'MDL (L)'),
    ('MGA', 'MGA (Ar)'), ('MKD', 'MKD (ден)'), ('MMK', 'MMK (K)'), ('MNT', 'MNT (₮)'),
    ('MOP', 'MOP (P)'), ('MRU', 'MRU (UM)'), ('MUR', 'MUR (₨)'), ('MVR', 'MVR (Rf)'),
    ('MWK', 'MWK (MK)'), ('MXN', 'MXN ($)'), ('MYR', 'MYR (RM)'), ('MZN', 'MZN (MT)'),
    ('NAD', 'NAD ($)'), ('NGN', 'NGN (₦)'), ('NIO', 'NIO (C$)'), ('NOK', 'NOK (kr)'),
    ('NPR', 'NPR (₨)'), ('NZD', 'NZD ($)'), ('OMR', 'OMR (ر.ع.)'), ('PAB', 'PAB (B/.)'),
    ('PEN', 'PEN (S/)'), ('PGK', 'PGK (K)'), ('PHP', 'PHP (₱)'), ('PKR', 'PKR (₨)'),
    ('PLN', 'PLN (zł)'), ('PYG', 'PYG (₲)'), ('QAR', 'QAR (ر.ق)'), ('RON', 'RON (lei)'),
    ('RSD', 'RSD (дин)'), ('RUB', 'RUB (₽)'), ('RWF', 'RWF (FRw)'), ('SAR', 'SAR (ر.س)'),
    ('SBD', 'SBD ($)'), ('SCR', 'SCR (₨)'), ('SDG', 'SDG (ج.س.)'), ('SEK', 'SEK (kr)'),
    ('SGD', 'SGD ($)'), ('SHP', 'SHP (£)'), ('SLL', 'SLL (Le)'), ('SOS', 'SOS (Sh)'),
    ('SRD', 'SRD ($)'), ('SSP', 'SSP (£)'), ('STN', 'STN (Db)'), ('SYP', 'SYP (ل.س)'),
    ('SZL', 'SZL (L)'), ('THB', 'THB (฿)'), ('TJS', 'TJS (SM)'), ('TMT', 'TMT (T)'),
    ('TND', 'TND (د.ت)'), ('TOP', 'TOP (T$)'), ('TRY', 'TRY (₺)'), ('TTD', 'TTD ($)'),
    ('TWD', 'TWD (NT$)'), ('TZS', 'TZS (Sh)'), ('UAH', 'UAH (₴)'), ('UGX', 'UGX (USh)'),
    ('USD', 'USD ($)'), ('UYU', 'UYU ($U)'), ('UZS', 'UZS (so\'m)'), ('VES', 'VES (Bs.S)'),
    ('VND', 'VND (₫)'), ('VUV', 'VUV (Vt)'), ('WST', 'WST (T)'), ('XAF', 'XAF (FCFA)'),
    ('XCD', 'XCD ($)'), ('XOF', 'XOF (CFA)'), ('XPF', 'XPF (₣)'), ('YER', 'YER (﷼)'),
    ('ZAR', 'ZAR (R)'), ('ZMW', 'ZMW (ZK)'), ('ZWL', 'ZWL ($)')
]

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
                choices=ALL_CURRENCIES,
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
                choices=ALL_CURRENCIES,
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
        choices=ALL_CURRENCIES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
