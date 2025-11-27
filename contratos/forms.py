from django import forms


class CedulaForm(forms.Form):
    cedula = forms.RegexField(
        label="Número de cédula",
        regex=r"^\d{5,15}$",
        max_length=15,
        help_text="Ingresa solo números, sin puntos ni guiones.",
        error_messages={
            "invalid": "Introduce un número de cédula válido (solo dígitos).",
            "required": "El número de cédula es obligatorio.",
        },
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ej: 1234567890",
            "inputmode": "numeric",
        }),
    )
