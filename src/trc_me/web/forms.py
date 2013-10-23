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
from trc_me.core.models import Flag, Position, Tag

class FlagForm(forms.ModelForm):
    class Meta:
        model = Flag
        fields = ('note', 'img', 'visibility')


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ('latitude', 'longitude', 'accuracy', 'sensor', 'geolocation_support')


class TagForm(forms.ModelForm):
    """Used when creating tags.
    
    tag.user is set to request.user
    """
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': '5'}))
    visibility = forms.ChoiceField(
        choices=Tag.VISIBILITY_CHOICES,
        initial='pub',
        widget=forms.RadioSelect)
    class Meta:
        model = Tag
        fields = ('description', 'img', 'visibility')

