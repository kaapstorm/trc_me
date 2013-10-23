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

from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from trc_me.accounts.views import *
from trc_me.web.views import *
from trc_me.web.feeds import TagFeed, UserFeed
from django.views.generic.simple import redirect_to


admin.autodiscover()

urlpatterns = patterns(
    '',

    # Redirect blog URLs
    (r'^blog/(?P<query>.*)$', redirect_to, {'url': 'http://blog.trc.me/%(query)s', 'permanent': True}),

    # Redirect old dev URLs
    (r'^d/(?P<query>.*)$', redirect_to, {'url': 'http://trc.me/%(query)s', 'permanent': True}),

    (r'^admin/', include(admin.site.urls)),

    (r'^$', index),
    (r'^q/$', search),
    (r'^new/$', create_tag),
    (r'^(?P<code>[0-9a-zA-Z]{6,})/$', update_tag),
    (r'^tag/(?P<id>\d+)/view/$', view_tag),
    (r'^tag/(?P<id>\d+)/edit/$', edit_tag),
    (r'^tag/(?P<id>\d+)/print/$', print_tag),
    (r'^tag/(?P<id>\d+)/delete/$', delete_tag),
    url(r'^tag/(?P<id>\d+)/atom/$', TagFeed(), name='tag_feed'),
    (r'^flag/(?P<id>\d+)/view/$', view_flag),
    # If we restrict access to uploaded images ...
    #(r'^dl/tag/(?P<id>[0-9a-zA-Z]{6,}).jpeg$', tag_img),
    #(r'^dl/flag/(?P<id>\d+).jpeg', flag_img),
    #(r'^dl/profile/(?P<id>\d+).jpeg', profile_img),

    (r'cmt/', include('django.contrib.comments.urls')),
    (r'rcmt/', include('richcomments.urls')),

    (r'^acct/logout/$', logout_view),
    (r'^user/$', view_user),
    (r'^user/(?P<username>\w+)/$', view_user),
    url(r'^user/(?P<username>\w+)/atom/$', UserFeed(), name='user_feed'),
    (r'^acct/edit/$', edit_user),
    (r'^acct/chpwd/$', change_password),
    (r'^mobi/$', mobile_update_tag),
    (r'^mobi/page/(?P<slug>[\w\-]+)/$', mobile_view_page),
    url(r'^mobi/login/$',
        'django.contrib.auth.views.login',
        {'template_name': 'mobile/login.html',
         'authentication_form': PrettyAuthenticationForm},
        name='mobile_login'),
    (r'^mobi/register/$', mobile_register),

    (r'^ajax/$', ajax_index),
    (r'^ajax/login/$', ajax_login),
    (r'^ajax/register/$', ajax_register),
    (r'^ajax/new/$', ajax_create_tag),
    (r'^ajax/(?P<id>[0-9a-zA-Z]{6,})/$', ajax_update_tag),
    (r'^ajax/flag/(?P<id>\d+)/$', ajax_view_flag),
    (r'^ajax/chpwd/$', ajax_change_password),
    (r'^page/(?P<slug>[\w\-]+)/$', ajax_view_page),

    (r'^hub/', include('subhub.urls')),

    (r'^sub/tag/(?P<id>\d+)/track/', track_tag),
    (r'^sub/tag/(?P<id>\d+)/untrack/', track_tag, {'mode': 'unsubscribe'}),
    (r'^sub/user/(?P<username>\w+)/follow/', follow_user),
    (r'^sub/user/(?P<username>\w+)/unfollow/', follow_user, {'mode': 'unsubscribe'}),
    (r'^sub/ping/(?P<username>\w+)/tag/(?P<tag_id>\d+)/', track_tag_callback),
    (r'^sub/ping/(?P<username>\w+)/user/(?P<tracked_username>\w+)/', follow_user_callback),

    (r'^api/', include('trc_me.api.urls')),

)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )

