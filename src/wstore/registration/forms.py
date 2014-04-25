from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from wstore.registration.models import Profile


class RegistrationForm(forms.ModelForm):
    """
    """
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    username = forms.RegexField(
        regex=r'^[\w -]{5,}$', max_length=30,
        error_messages={
            'invalid': _("Enter at least 5 characters (letters, digits or"
                         " @/./+/-/_)."),
        })
    email = forms.EmailField(max_length=254)
    password = forms.CharField(
        min_length=5, widget=forms.PasswordInput(),
        error_messages={
            'min_length': _("Enter at least 5 characters."),
        })
    password_check = forms.CharField(
        label=_('Password confirmation'), widget=forms.PasswordInput())
    page = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def clean_username(self):
        """
        """
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError("The username is already taken.")

    def clean_email(self):
        """
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email):
            raise ValidationError("The email is already registered.")
        return email

    def clean_password_check(self):
        """
        """
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data['password_check']
        if not password2:
            return password2
        if password1 and password1 == password2:
            return password2
        raise ValidationError("Passwords do not match.")

    def is_valid(self):
        """
        """
        if self.data['page'] == 'login':
            for field in self.fields.values():
                field.required = False
            super(RegistrationForm, self).is_valid()
            return False
        else:
            return super(RegistrationForm, self).is_valid()

    def save(self):
        """
        """
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.save()
        profile = Profile.objects.create_profile(user)
        return profile.user
