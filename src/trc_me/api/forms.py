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
from trc_me.core.models import Tag  

class TagForm(forms.ModelForm):
    """Used when creating tags.
    
    tag.user is set to authenticated user.
    """
    class Meta:
        model = Tag
        exclude = ('user', 'img_width', 'img_height', 'created_at')
