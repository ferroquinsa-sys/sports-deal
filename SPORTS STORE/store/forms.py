from django import forms


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        label='Nombre y apellido', max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan Pérez'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'juan@email.com'})
    )
    phone = forms.CharField(
        label='Teléfono', max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11 1234-5678'})
    )
    address = forms.CharField(
        label='Dirección', max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle 123, Piso/Depto'})
    )
    city = forms.CharField(
        label='Ciudad', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buenos Aires'})
    )
    postal_code = forms.CharField(
        label='Código postal', max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        label='Notas del pedido (opcional)', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
