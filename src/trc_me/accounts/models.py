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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from stdimage import StdImageField


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    has_valid_email = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=0)
    img = StdImageField(
        #storage=restricted_fs, 
        upload_to='profile/%Y/%m/%d/',
        size=(128, 181), # 128 * sqrt(2) = 181
        thumbnail_size=(48, 48, True),
        blank=True)
    notify_by_email = models.BooleanField(default=True)
    
    def __unicode__(self):
        return unicode(self.user)
    
    def get_absolute_url(self):
        from trc_me.web.views import view_user
        return reverse(view_user, kwargs={'username': self.user.username})
    

def create_profile(sender, **kw):
    user = kw["instance"]
    if kw["created"]:
        profile = UserProfile(user=user)
        profile.save()

post_save.connect(create_profile, sender=User)

