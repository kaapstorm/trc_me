# This file is part of trc.me.
#
# trc.me is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# trc.me is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# trc.me. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from trc_me.accounts.models import UserProfile


class PrettyAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': _("Username")}))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Password")},
                                   render_value=False))


class PrettyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Old password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("Old password")},
                                   render_value=False))
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'placeholder': _("New password")},
                                   render_value=False))
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(
            attrs={'placeholder': _("Confirm new password")},
            render_value=False))


class PrettyUserForm(forms.ModelForm):
    """Allows users to change their name
    """
    first_name = forms.CharField(
        label=_("First name"),
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': _("First name")}))
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': _("Last name")}))
    email = forms.EmailField(
        label=_("E-mail address"),
        widget=forms.TextInput(attrs={'placeholder': _("E-mail address")}))
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    """Allows users to change their profile pic
    
    cf. http://djangosnippets.org/snippets/2081/
    """
    #img = forms.FileField(label=_("Image"), widget=forms.FileInput())
    img = forms.ImageField(label=_("Image"), widget=forms.FileInput(attrs={'size': 5}))
    
    def __init__(self, *args, **kwargs):
        # magic 
        self.user = kwargs['instance'].user
        user_kwargs = kwargs.copy()
        user_kwargs['instance'] = self.user
        self.userform = PrettyUserForm(*args, **user_kwargs)
        # magic end 

        super(ProfileForm, self).__init__(*args, **kwargs)

        self.fields.update(self.userform.fields)
        self.initial.update(self.userform.initial)
         
        self.fields.keyOrder = (
            'first_name',
            'last_name',
            'email',
            'img'
            )

    def save(self, *args, **kwargs):
        # save both forms   
        self.userform.save(*args, **kwargs)
        return super(ProfileForm, self).save(*args, **kwargs)

    class Meta:
        model = UserProfile
        #fields = ('img', )


class RegistrationForm(UserCreationForm):
    """RegistrationForm extends ModelForm to validate users
    """
    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': _("Username")}))
    email = forms.EmailField(
        label=_("E-mail address"),
        widget=forms.TextInput(attrs={'placeholder': _("E-mail address")}))
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={'placeholder': _("Password")},
            render_value=False))
    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(
            attrs={'placeholder': _("Confirm password")},
            render_value=False))


