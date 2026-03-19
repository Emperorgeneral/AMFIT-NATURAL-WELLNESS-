from django import forms


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Street address, apartment, building, landmarks'}))
    shipping_city = forms.CharField(max_length=100)
    shipping_state = forms.CharField(max_length=100)
    shipping_zip = forms.CharField(max_length=20, label='Postal code')
    shipping_country = forms.CharField(max_length=100, initial='Nigeria')
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional order notes'}))