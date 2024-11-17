# uploads/forms.py
from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(),
        required=True
    )
