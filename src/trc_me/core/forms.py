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

# trc.me core forms
# 
# Used by web and API
#
from django import forms
from trc_me.core.models import Flag  


class FlagPositionForm(forms.Form):
    """Used for submitting new flags
    """
    # Flag fields
    note = forms.CharField(max_length=255, required=False)
    img = forms.ImageField(required=False)
    visibility = forms.ChoiceField(
        choices=Flag.VISIBILITY_CHOICES,
        initial='pub',
        widget=forms.RadioSelect)
    # Position fields
    latitude = forms.FloatField()
    longitude = forms.FloatField()
    accuracy = forms.FloatField(help_text='Metres')
    geolocation_support = forms.BooleanField(
        initial=True, 
        help_text='Device supports geolocation')
    sensor = forms.BooleanField(
        initial=True, 
        help_text='Position acquired by built-in geolocation')

