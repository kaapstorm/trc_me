# -*- coding: utf-8 -*-
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

from math import e, log
import re

#from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
#from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from stdimage import StdImageField
import subhub
import tagging
from trc_me.core.utils import base62_encode, ALPHABET as base62_alphabet


# The base of the logarithmic equation used to calculate points for 
# distance from first flag. 
# 20038 km is the distance half-way around Earth.
# 100 is the max points awarded. 
DIST_LOG_BASE = e ** (log(20038) / 100)


class UserItem(models.Model):
    """An item that can belong to a user; Parent class of Tag and Flag
    
    Subclassing allows simple unions, pagination, and collective ordering
    """
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    create_agent = models.CharField(max_length=50, default="web")
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        
    def __unicode__(self):
        try:
            return unicode(self.flag)
        except Flag.DoesNotExist:
            return unicode(self.tag)
    
    def is_visible_to(self, user):
        if self.is_deleted:
            # Deleted items are invisible
            return False
        if user.is_authenticated() and self.user == user:
            # A user can always see their own items
            return True
        # Leave to child classes to determine
        return None

    def get_hashtags(self, attr, string=''):
        """Extract hashtags from string, or from the specified attribute
        """
        if string:
            hashtags = string.replace('#', '')
        else:
            # Hashtags are to be extracted from an attribute of self
            value = getattr(self, attr)
            hashtags = ' '.join(re.findall(r'#(\w+)', value))

tagging.register(UserItem, 'hashtags', 'hashtagged')        

        
class TagGroup(models.Model):
    """Allows discoverable tags to reveal other tags of the same group
    """
    user = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    # Cannot be maintained when old tags are added or removed: 
    #flaggers = models.ManyToManyField(User, 
    #                                  related_name='flagged_taggroups',
    #                                  blank=True)
    
    def __unicode__(self):
        return self.name
    

class TagManager(models.Manager):
    """Adds visibility management
    """
    def get_visible_to(self, user):
        if not user.is_authenticated():
            # Only public tags are visible to AnonymousUser
            return self.exclude(is_deleted=True)\
                       .filter(visibility='pub')
        # Public tags
        # Or his own tags
        # TODO: Or discoverable tags he's flagged
        # TODO: Or tags in tag groups of tags he's flagged
        return self.exclude(is_deleted=True)\
                   .filter(Q(visibility='pub') | \
                           Q(user=user)
                           )    


class Tag(UserItem):
    VISIBILITY_CHOICES = (('prv', 'Private'),
                          ('dsc', 'Discoverable'),
                          ('pub', 'Public'))
    
    tag_groups = models.ManyToManyField(TagGroup,
                                        # TODO: TagGroup must belong to same user as Tag
                                        #limit_choices_to={'user': user}, 
                                        blank=True)
    description = models.CharField(
        max_length=255, 
        help_text=_('A description that identifies the object. Use #tags to make the object searchable.'))
    redirect_url = models.URLField(
        help_text=_('A URL to which a user is redirected after flagging. e.g. A homepage for this tag.'))
    #img = StdImageField(
    img = models.ImageField(
        upload_to='tag/%Y/%m/%d/', # TODO: Use callable. Use timestamp or hash 
        #size=(210, 297), # 210 = width. 297 = 210 * sqrt(2)
        #thumbnail_size=(52, 52, True), # 52px = 2em * 2 -- Allows a bit of resizing
        blank=True)
    visibility = models.CharField(max_length=3, 
                                  choices=VISIBILITY_CHOICES,
                                  default='pub')
    objects = TagManager()
    
    @property
    def code(self):
        c = base62_encode(self.id)
        return c.rjust(6, base62_alphabet[0]) # 6 is minimum code length
        
    @property
    def qrcode_url(self):
        return 'http://chart.apis.google.com/chart?cht=qr&chs=216x216&chl=http://trc.me/%s/' % (self.code, )

    def __unicode__(self):
        #return 'trc.me/' + self.code
        return self.description
    
    def get_absolute_url(self):
        from trc_me.web.views import view_tag
        return reverse(view_tag, kwargs={'id': self.id})
    
    def is_visible_to(self, user):
        result = super(Tag, self).is_visible_to(user)
        if result is not None:
            return result
        
        if not user.is_authenticated():
            # Only public tags are visible to AnonymousUser
            return self.visibility == 'pub'
        
        # Public tags
        # Or tags he's flagged
        # TODO: Or tags in tag groups of tags he's flagged
        if self.visibility == 'pub':
            return True
        if self.flag_set.filter(user=user).count() > 0:
            return True
        return False
    
    def save(self, **kwargs):
        super(Tag, self).save(**kwargs)
        feeds = [reverse('user_feed', kwargs={'username': self.user.username}), ]
        subhub.publish([f for f in feeds],
                       self.get_absolute_url())
        
        
    def __get_flags(self, 
                    incl_flags_public=False,
                    incl_flags_user=None,
                    incl_flags_all=False,
                    incl_flags_start=None,
                    incl_flags_end=None):
        if incl_flags_all:
            return self.flag_set.all()
        else:
            if incl_flags_public and incl_flags_user is not None:
                return self.flag_set.filter(Q(visibility='pub') | Q(user=incl_flags_user))[incl_flags_start:incl_flags_end]
            elif incl_flags_public:
                return self.flag_set.filter(visibility='pub')[incl_flags_start:incl_flags_end]
            elif incl_flags_user is not None:
                return self.flag_set.filter(user=incl_flags_user)[incl_flags_start:incl_flags_end]
        # Flags, but not all, not public, and not by a specific user. Alrighty then ... 
        return Flag.objects.get_empty_query_set()
    
    def _api_dict(self, 
                  incl_flags=False, 
                  incl_flags_public=False,
                  incl_flags_user=None,
                  incl_flags_all=False,
                  incl_flags_start=None,
                  incl_flags_end=None):
        d = {'code': self.code,
             'user': self.user.username,
             'hashtags': ','.join([unicode(h) for h in self.hashtags.all()]),
             'description': self.description,
             'redirect_url': self.redirect_url,
             'img_url': self.img.url if len(self.img.name) > 0 else None,
             'qrcode_url': self.qrcode_url,
             'visibility': self.visibility,
             'created_at': self.created_at}
        if incl_flags:
            d['flags'] = [f._api_dict() for f in self.__get_flags(
                              incl_flags_public,
                              incl_flags_user,
                              incl_flags_all,
                              incl_flags_start,
                              incl_flags_end)]
        return d


class Position(models.Model):
    """Offers the data available from an HTML5 Position object
    """
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(
        null=True, blank=True, 
        help_text=_('Metres above the reference ellipsoid'))
    accuracy = models.FloatField(help_text='Metres')
    altitude_accuracy = models.FloatField(
        null=True, blank=True, 
        help_text=_('Metres'))
    heading = models.FloatField(
        null=True, blank=True, 
        help_text=_('Degrees clockwise from true north'))
    speed = models.FloatField(
        null=True, blank=True, 
        help_text=_('Metres per second'))
    geolocation_support = models.BooleanField(
        default=True, 
        help_text=_('Device supports geolocation'))
    sensor = models.BooleanField(
        default=True, 
        help_text=_('Position acquired by buit-in geolocation'))
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        #ns = _('N') if self.latitude >= 0 else _('S')
        #ew = _('E') if self.longitude >= 0 else _('W')
        ns = 'N' if self.latitude >= 0 else 'S'
        ew = 'E' if self.longitude >= 0 else 'W'
        if self.altitude is not None:
            return u'%0.3f° %s, %0.3f° %s, %d m' % (abs(self.latitude), ns, 
                                                 abs(self.longitude), ew,
                                                 int(self.altitude))
        return u'%0.3f° %s, %0.3f° %s' % (abs(self.latitude), ns,
                                       abs(self.longitude), ew)


class FlagManager(models.Manager):
    """Adds visibility management
    """
    def get_visible_to(self, user):
        if not user.is_authenticated():
            # Only public flags of public tags are visible to AnonymousUser
            return self.exclude(is_deleted=True)\
                       .filter(tag__visibility='pub', visibility='pub')
        # TODO: Public flags of discoverable tags he has flagged
        # TODO: Public flags of tags in tag groups of tags he's flagged
        # His own flags
        # Flags of his own tags
        # Public flags of public tags
        return self.exclude(is_deleted=True)\
                   .filter(Q(user=user) | \
                           Q(tag__user=user) | \
                           Q(tag__visibility='pub'), Q(visibility='pub'))    


class Flag(UserItem):
    VISIBILITY_CHOICES = (('prv', 'Private'),
                          ('pub', 'Public'))
    
    tag = models.ForeignKey(Tag)
    position = models.ForeignKey(Position)
    note = models.CharField(max_length=255, blank=True)
    #img = StdImageField(
    img = models.ImageField(
        upload_to='flag/%Y/%m/%d/',
        #size=(210, 297),
        #thumbnail_size=(52, 52, True),
        blank=True)
    visibility = models.CharField(max_length=3, choices=VISIBILITY_CHOICES)
    is_featured = models.BooleanField(default=False)
    points = models.PositiveSmallIntegerField(default=0)
    objects = FlagManager()
    
    def __unicode__(self):
        #return u'%s @ %s (%s)' % (self.tag, self.position, self.created_at)
        return u'%s: %s (%s)' % (self.tag, self.note, self.created_at)
    
    def get_absolute_url(self):
        from trc_me.web.views import view_flag
        return reverse(view_flag, kwargs={'id': self.id})
    
    def is_visible_to(self, user):
        result = super(Flag, self).is_visible_to(user)
        if result is not None:
            return result
        
        if not user.is_authenticated():
            # Only public flags of public tags are visible to AnonymousUser
            return self.tag.visibility == 'pub' and self.visibility == 'pub'

        # Flags of his own tags
        # Public flags of public tags
        # Public flags of discoverable tags he has flagged
        # TODO: Public flags of tags in tag groups of tags he's flagged
        if self.tag.user == user:
            return True
        if self.visibility == 'pub' and self.tag.visibility == 'pub':
            return True
        if self.visibility == 'pub' \
                and self.tag.visibility == 'dsc' \
                and self.tag.flag_set.filter(user=user).count() > 0:
            return True
        return False        
    
    def save(self, **kwargs):
        super(Flag, self).save(**kwargs)
        feeds = [reverse('tag_feed', kwargs={'id': self.tag.id}), 
                 reverse('user_feed', kwargs={'username': self.user.username})]
        subhub.publish([f for f in feeds],
                       self.get_absolute_url())
        

    def _api_dict(self):
        return {'latitude': self.position.latitude,
                'longitude': self.position.longitude,
                'accuracy': self.position.accuracy,
                'user': self.user.username,
                'note': self.note,
                'img': self.img.url if len(self.img.name) > 0 else None,
                'visibility': self.visibility,
                'points': self.points,
                'created_at': self.created_at,
                'create_agent': self.create_agent }

    def calc_points(self):
        """Calculate the points accrued by this flag
        """
        # No points if you own the code
        if self.user == self.tag.user:
            return 0
        
        # No points if you've flagged it before 
        if self.id is None \
                and self.tag.flag_set.filter(user=self.user).count() > 0:
            return 0
        if self.id is not None \
                and self.tag.flag_set\
                             .filter(Q(user=self.user) & Q(id_not=self.id))\
                             .count() > 0:
            return 0
        
        # Return points for nth flag + points for distance
        return self.__calc_count_points() + self.__calc_distance_points()
    
    def __calc_count_points(self):
        """Flags usually get 1 point. 
        First flag gets 10 points. 
        Every 100th flag gets 10 points. 
        Every 1000th flag gets 100 points.
        """
        count_excludes_self = 1 if self.id is None else 0
        n = self.tag.flag_set.exclude(user=self.tag.user).count() \
            + count_excludes_self
        if n == 1:
            return 10
        if n % 1000 == 0:
            return 100
        if n % 100 == 0:
            return 10
        return 1
    
    def __calc_distance_points(self):
        """The further this flag is from the last, the more points you get.
        
        Scale is logarithmic.
        """
        from trc_me.core.utils import spherical_cosine 
        
        count_excludes_self = 1 if self.id is None else 0
        n = self.tag.flag_set.count() + count_excludes_self
        if n == 1:
            # We are the first flag. No distance from previous flag.
            return 0
        
        # Calculate distance from previous flag (in metres)
        standpoint = (self.position.latitude, self.position.longitude)
        if count_excludes_self == 1:
            # Last flag is the forepoint
            flag = self.tag.flag_set.all()[0]
        else:
            # Penultimate flag is the forepoint
            flag = self.tag.flag_set.all()[1]
        forepoint = (flag.position.latitude, flag.position.longitude)
        km = spherical_cosine(standpoint, forepoint)
        # Calculate points for distance
        pts = log(km + 1) / log(DIST_LOG_BASE)
        return int(pts)


class Notification(models.Model):
    VERB_CHOICES = (('tagged', 'tagged'), # when subject == User
                    ('flagged', 'flagged'), # when subject == User
                    ('was flagged', 'was flagged')) # when subject == Tag
    user = models.ForeignKey(User)
    subject = models.CharField(max_length=30) # A user or tag
    subject_url = models.URLField()
    verb = models.CharField(max_length=12, choices=VERB_CHOICES, blank=True)
    object = models.CharField(max_length=30, blank=True) # a tag or a flag
    object_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

