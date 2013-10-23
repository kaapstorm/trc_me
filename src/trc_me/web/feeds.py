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
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from trc_me.core.models import Flag, Tag
from trc_me.core.utils import absolute_url


class HubAtom1Feed(Atom1Feed):
    def add_root_elements(self, handler):
        super(HubAtom1Feed, self).add_root_elements(handler)
        hub_link = self.feed.get('hub_link')
        if hub_link is not None:
            handler.addQuickElement(u'link', '', {
                u'rel': u'hub',
                u'href': hub_link,
            })


class TagFeed(Feed):
    feed_type = HubAtom1Feed
    
    def get_object(self, request, id):
        return get_object_or_404(Tag, pk=id)
    
    def title(self, obj):
        return u"Recent flags of %s" % obj.description
    
    def author_name(self, obj):
        return unicode(obj.user)

    def categories(self, obj):
        return [unicode(h) for h in obj.hashtags.all()]

    def link(self, obj):
        return obj.get_absolute_url()
    
    def items(self, obj):
        return obj.flag_set.all().order_by('-created_at')[:50]
    
    def item_title(self, item):
        return item.note
    
    def item_author_name(self, item):
        return unicode(item.user)

    def item_categories(self, item):
        return [unicode(h) for h in item.hashtags.all()]
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.created_at
    
    def feed_extra_kwargs(self, obj):
        return {
            'hub_link': absolute_url(reverse('subhub-hub')),
        }


class UserFeed(Feed):
    feed_type = HubAtom1Feed
    
    def get_object(self, request, username):
        return get_object_or_404(User, username=username)
    
    def title(self, obj):
        return u"%s's recent tags and flags" % obj.username
    
    def author_name(self, obj):
        return unicode(obj)

    def link(self, obj):
        return obj.get_profile().get_absolute_url()
    
    def items(self, obj):
        return obj.useritem_set.all()[:50]
    
    def item_title(self, item):
        try:
            return item.flag.note
        except Flag.DoesNotExist:
            return item.tag.description
    
    def item_author_name(self, item):
        return unicode(item.user)

    def item_categories(self, item):
        return [unicode(h) for h in item.hashtags.all()]
    
    def item_link(self, item):
        try:
            return item.flag.get_absolute_url()
        except Flag.DoesNotExist:
            return item.tag.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.created_at
    
    def feed_extra_kwargs(self, obj):
        return {
            'hub_link': absolute_url(reverse('subhub-hub')),
        }

