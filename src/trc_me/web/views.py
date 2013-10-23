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

try:
    from cjson import encode as to_json
except ImportError:
    from django.utils.simplejson import dumps as to_json
import logging
import re

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, Context, loader, Template
from django.views.decorators.csrf import csrf_protect

from tagging.models import Tag as Hashtag, TaggedItem as HashtaggedItem

from trc_me.core.models import Flag, Notification, Tag
from trc_me.core.utils import base62_decode, is_mobile_browser
from trc_me.accounts.forms import PrettyAuthenticationForm, PrettyPasswordChangeForm, ProfileForm, RegistrationForm
from trc_me.web.forms import FlagForm, PositionForm, TagForm
from trc_me.web.models import Page


@csrf_protect
def index(request):
    """Landing page
    """
    authform = PrettyAuthenticationForm()
    regform = RegistrationForm()
    # Featured flags
    flags = Flag.objects.filter(is_featured=True).all()
    
    #if request.device is not None \
    #        and request.device['resolution_width'] < 1024: 
    template = 'web/index.html' if not is_mobile_browser(request) else 'mobile/index.html'
    next = reverse(index)
    return render_to_response(template, 
                              {'authform': authform,
                               'regform': regform,
                               'flags': flags,
                               'next': next},
                              context_instance=RequestContext(request))


def search(request):
    if 'q' not in request.GET:
        # User came directly here with no search query
        return HttpResponseRedirect(reverse(index))
    q = request.GET['q'].replace('#', '')
    flags = HashtaggedItem.objects.get_by_model(Flag.objects.get_visible_to(request.user), q)
    tags = HashtaggedItem.objects.get_by_model(Tag.objects.get_visible_to(request.user), q)
    # TODO: Find users whose full name is like q
    # TODO: Allow users to set their full names!
    #users = ... CONCAT(first_name, ' ', last_name) LIKE '%q%';
    template = 'web/search_results.html' if not is_mobile_browser(request) else 'mobile/search_results.html'
    return render_to_response(template, 
                              {'tags': tags,
                               'flags': flags,
                               'q': request.GET['q']},
                              context_instance=RequestContext(request))


@login_required
@csrf_protect
def create_tag(request):
    """Create a new tag
    """
    if request.method == 'POST':
        form = TagForm(request.POST, request.FILES)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            tag.save()
            # Get hashtags from tag.description or from POST['hashtags']
            hashtags = tag.get_hashtags('description', request.POST['hashtags'])
            Hashtag.objects.update_tags(tag, hashtags)
            # Subscribe tag owner to tag
            try:
                track_tag(request, tag.id, silent=True)
            except Exception as ex: # TODO: Catch a real exception
                logging.debug(
                    "Exception raised when subscribing tag owner '%s' to tag '%s': %s"
                    % (request.user, tag, ex))
            return HttpResponseRedirect(reverse(view_tag, kwargs={'id': tag.id}))
    else:
        form = TagForm()
    template = 'web/tag_form.html' if not is_mobile_browser(request) else 'mobile/tag_form.html'
    return render_to_response(template,
                              {'form': form},
                              context_instance=RequestContext(request))


@login_required
@csrf_protect
def edit_tag(request, id):
    """Edit a tag's details
    """
    tag = get_object_or_404(Tag, pk=id)
    if tag.is_deleted:
        raise Http404
    if request.method == 'POST':
        form = TagForm(request.POST, request.FILES, instance=tag)
        if form.is_valid():
            tag = form.save()
            Hashtag.objects.update_tags(tag, request.POST['hashtags'].replace('#', ''))
            return HttpResponseRedirect(reverse(view_tag, kwargs={'id': tag.id}))
    else:
        form = TagForm(instance=tag)
    hashtags = ' '.join([u'#%s' % (t, ) for t in Hashtag.objects.get_for_object(tag)])
    template = 'web/tag_form.html' if not is_mobile_browser(request) else 'mobile/tag_form.html'
    return render_to_response(template,
                              {'form': form,
                               'hashtags': hashtags},
                              context_instance=RequestContext(request))


@csrf_protect
def view_tag(request, id):
    """View a tag's details
    
    The creator of a tag can see everything about it. If a tag is public, 
    anyone can see it and all its public flags. If a tag is not public, a 
    user can see it only if they have flagged it, and then they can only see 
    their flags.
    """
    from subhub.models import Subscription, SubscriptionTask
    
    tag = get_object_or_404(Tag, pk=id)
    if tag.is_deleted:
        raise Http404
    if not tag.is_visible_to(request.user):
        #return HttpResponseForbidden
        raise Http404
    
    flags = tag.flag_set.get_visible_to(request.user)
    if request.user == tag.user and len(flags) == 0:
        offer_initial_flag = True
    else:
        offer_initial_flag = False

    form = TagForm(instance=tag)
    # Find out whether user is tracking tag
    if request.user.is_authenticated():
        callback = request.build_absolute_uri(
                reverse(track_tag_callback,
                        kwargs={'username': request.user.username,
                                'tag_id': tag.id}))
        is_tracking = (
            Subscription.objects.filter(callback=callback).count() \
            + SubscriptionTask.objects.filter(callback=callback).filter(mode='subscribe').count() \
            - SubscriptionTask.objects.filter(callback=callback).filter(mode='unsubscribe').count()) > 0
    else:
        is_tracking = False        
    template = 'web/tag.html' if not is_mobile_browser(request) else 'mobile/tag.html'
    return render_to_response(template,
                              {'tag': tag,
                               'form': form,
                               'flags': flags,
                               'initial': offer_initial_flag,
                               'is_tracking': is_tracking},
                              context_instance=RequestContext(request))


@csrf_protect
def update_tag(request, code):
    """Flag a tag
    """
    tag = get_object_or_404(Tag, pk=base62_decode(code.upper()))
    if tag.is_deleted:
        raise Http404
    if request.method == 'POST':
        flag_form = FlagForm(request.POST, request.FILES)
        position_form = PositionForm(request.POST)
        if flag_form.is_valid() and position_form.is_valid():
            # Save position
            position = position_form.save()
            # Save flag
            flag = flag_form.save(commit=False)
            flag.tag = tag
            flag.position = position
            if request.user.is_authenticated():
                flag.user = request.user
            else:
                # Flags of unauthenticated users are always public
                flag.visibility = 'pub'
            flag.points = flag.calc_points()
            flag.save()
            # Get hashtags from flag.note or from POST['hashtags']
            hashtags = flag.get_hashtags('note', request.POST['hashtags'])
            Hashtag.objects.update_tags(flag, hashtags)
            if request.user.is_authenticated():
                if flag.points > 0:
                    profile = request.user.get_profile()
                    profile.points = profile.points + flag.points
                    profile.save()
                # If logged in, redirect to the user's profile, or to the tag's redirect URL
                url = tag.redirect_url if tag.redirect_url else reverse(view_user,
                                                                        kwargs={'username': request.user.username})
                return HttpResponseRedirect(url)
            # Otherwise view the tag (or go to its redirect URL)
            url = tag.redirect_url if tag.redirect_url else reverse(view_tag, kwargs={'id': tag.id})
            return HttpResponseRedirect(url)
    else:
        flag_form = FlagForm()
        position_form = PositionForm()

    authform = PrettyAuthenticationForm(request)
    regform = RegistrationForm()
    next = reverse('trc_me.web.views.update_tag', kwargs={'code': code})
    template = 'web/tag_update.html' if not is_mobile_browser(request) else 'mobile/tag_update.html'
    return render_to_response(template, 
                              {'tag': tag,
                               'authform': authform,
                               'regform': regform,
                               'flagform': flag_form,
                               'positionform': position_form,
                               'next': next}, 
                              context_instance=RequestContext(request))


@csrf_protect
def mobile_update_tag(request):
    """Handles update tag requests from the mobile index page
    
    (Web index page does this asynchronously.)
    """
    if 'code' not in request.GET:
        return HttpResponseRedirect(index)
    code = request.GET['code']
    # If user gave hostname too, strip it
    pattern = r'\/(\w{6,})\/?$';
    result = re.search(pattern, code)
    if result is not None:
        code = result.groups()[0]
    
    tag = get_object_or_404(Tag, pk=base62_decode(code.upper()))
    if tag.is_deleted:
        raise Http404
    flag_form = FlagForm()
    position_form = PositionForm()
    authform = PrettyAuthenticationForm(request)
    next = reverse(update_tag, kwargs={'code': code})
    return render_to_response('mobile/tag_update.html', 
                              {'tag': tag,
                               'authform': authform,
                               'flagform': flag_form,
                               'positionform': position_form,
                               'next': next}, 
                              context_instance=RequestContext(request))


@login_required
def track_tag(request, id, mode='subscribe', silent=False):
    """Subscribe to tag's feed, and be notified of new flags
    
    mode in ('subscribe', 'unsubscribe')
    if silent do not return HttpResponse()
    """
    import urllib
    import urllib2
    import hashlib
    from django.conf import settings
    from django.core.mail import send_mail
    
    tag = get_object_or_404(Tag, pk=id)
    if not tag.is_visible_to(request.user):
        raise Http404
    h = hashlib.sha1('%s tracking tag %d at %s' % (request.user.username, 
                                                   tag.id, 
                                                   settings.SECRET_KEY))
    data = {
        'hub.callback': request.build_absolute_uri(
            reverse(track_tag_callback,
                    kwargs={'username': request.user.username,
                            'tag_id': tag.id})),
        'hub.mode': mode,
        'hub.topic': request.build_absolute_uri(
            reverse('tag_feed', kwargs={'id': tag.id})),
        'hub.verify': 'async',
        'hub.verify_token': h.hexdigest()}
    response = urllib2.urlopen(
        request.build_absolute_uri(reverse('subhub-hub')),
        urllib.urlencode(data))
    headers = response.headers
    body = response.read()
    response.close()
    if silent:
        if headers.status == '' and body == 'Subscription queued':
            return
        return 'Error %s: %s' % (headers.status, body)
    if headers.status == '' and body == 'Subscription queued':
        if mode == 'subscribe':
            # Notify tag owner of new tracker
            # TODO: Decent multipart message body
            message = '%s [ %s ] is tracking your tag "%s".' % (
                request.user.username, 
                request.build_absolute_uri(reverse(view_user, kwargs={'username': request.user.username})),
                tag.description)
            send_mail('%s is tracking your tag', 
                      message, 
                      settings.DEFAULT_FROM_EMAIL, 
                      [tag.user.email])
            return render_to_response(
                'web/tag_untrack_button.html',
                {'tag': tag},
                context_instance=RequestContext(request))
        elif mode == 'unsubscribe':
            # Notify owner of untrack
            message = '%s [ %s ] stopped tracking your tag "%s".' % (
                request.user.username, 
                request.build_absolute_uri(reverse(view_user, kwargs={'username': request.user.username})),
                tag.description)
            send_mail('%s stopped tracking your tag', 
                      message, 
                      settings.DEFAULT_FROM_EMAIL, 
                      [tag.user.email])
            return render_to_response(
                'web/tag_track_button.html',
                {'tag': tag},
                context_instance=RequestContext(request))
    return HttpResponse('Error %s: %s' % (headers.status, body))


def track_tag_callback(request, username, tag_id):    
    """PuSH will send pings to this URL when a tag's feed is updated
    """
    import hashlib
    from django.conf import settings
    
    tag = get_object_or_404(Tag, pk=tag_id)
    user = User.objects.get(username=username)
    if 'hub.mode' in request.GET and request.GET['hub.mode'] == 'subscribe':
        # Confirm subscription
        h = hashlib.sha1(('%s tracking tag %d at %s' % (user.username, 
                                                        tag.id, 
                                                        settings.SECRET_KEY)))
        if request.GET['hub.topic'] == request.build_absolute_uri(reverse('tag_feed', kwargs={'id': tag.id})) \
                and request.GET['hub.verify_token'] == h.hexdigest():
            # TODO: Consider using the hub.secret mechanism for authentication
            # All OK
            return HttpResponse(request.GET['hub.challenge'])
        else:
            #if request.GET['hub.topic'] != request.build_absolute_uri(reverse('tag_feed', kwargs={'id': tag.id})):
            #    return HttpResponse(
            #        'Error: Topic "%s" does not match feed URL "%s"' % (
            #            request.GET['hub.topic'], 
            #            request.build_absolute_uri(
            #                reverse('tag_feed', kwargs={'id': tag.id}))))
            #if request.GET['hub.verify_token'] != h.hexdigest():
            #    return HttpResponse('Error: Tokens do not match "%s tracking tag %d"' % (user.username, 
            #                                            tag.id))
            return HttpResponse('Error confirming topic and token')
            
    # Create notification
    n = Notification.objects.create(
        user=user,
        subject=tag.description if len(tag.description) <= 30 else '%s...' % (tag.description[:27], ),
        subject_url=reverse(view_tag, kwargs={'id': tag.id}),
        verb='was flagged')
        # TODO: Fetch and parse feed item
        #object = models.CharField(max_length=30)
        #object_url = models.URLField()
    # Notify user if necessary
    if user.get_profile().notify_by_email:
        t = loader.get_template('web/email_notification.txt')
        c = Context({'n': n})
        body_text = t.render(c)
        message = EmailMultiAlternatives('Update from trc.me', 
                                         body_text, 
                                         settings.DEFAULT_FROM_EMAIL, 
                                         [user.email])
        if hasattr(settings, 'EMAIL_ADDRESS_BOUNCE'):
            message.headers = {'Return-Path': settings.EMAIL_ADDRESS_BOUNCE}
        t = loader.get_template('web/email_notification.html')
        body_html = t.render(c)
        message.attach_alternative(body_html, 'text/html')
        message.send()
    return HttpResponse('OK')
        

@login_required
def print_tag(request, id):
    tag = get_object_or_404(Tag, pk=id)
    if tag.is_deleted:
        raise Http404
    if not tag.user == request.user:
        return HttpResponseForbidden
    return render_to_response('web/tag_print.html', 
                              {'tag': tag}, 
                              context_instance=RequestContext(request))


@login_required
def delete_tag(request, id):
    tag = get_object_or_404(Tag, pk=id)
    if tag.is_deleted:
        raise Http404
    if not tag.user == request.user:
        return HttpResponseForbidden
    tag.is_deleted = True
    tag.save()
    return HttpResponseRedirect(reverse(view_user, kwargs={'username': request.user.username}))


@csrf_protect
def view_flag(request, id):
    """Open the tag page, and populate panel with flag
    """
    flag = get_object_or_404(Flag, pk=id)
    if not flag.is_visible_to(request.user):
        raise Http404
    template = 'web/flag.html' if not is_mobile_browser(request) else 'mobile/flag.html'
    return render_to_response(template,
                              {'flag': flag,
                               'tag': flag.tag}, 
                              context_instance=RequestContext(request))


@csrf_protect
def view_user(request, username=None):
    """Show account details
    """
    from subhub.models import Subscription, SubscriptionTask
    
    # TODO: Add mobile
    if username == None:
        # Redirect to authenticated user's profile
        if request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse(view_user, 
                        kwargs={'username': request.user.username}))
        # User isn't authenticated. Redirect to landing page
        return HttpResponseRedirect(reverse(index))
    
    if request.user.is_authenticated() and request.user.username == username:
        # It's the user's own profile
        u = request.user
        tags = Tag.objects.filter(user=request.user).filter(is_deleted=False)
        flags = Flag.objects.filter(user=request.user).order_by('-created_at')
        notis = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    else:
        u = User.objects.get(username=username)
        tags = Tag.objects.get_visible_to(request.user).filter(user=u)
        flags = Flag.objects.get_visible_to(request.user).filter(user=u)
        notis = []
    
    # Find out whether request.user is following user
    if request.user.is_authenticated():
        callback = request.build_absolute_uri(
                reverse(follow_user_callback,
                        kwargs={'username': request.user.username,
                                'tracked_username': u.username}))
        is_following = (
            Subscription.objects.filter(callback=callback).count() \
            + SubscriptionTask.objects.filter(callback=callback).filter(mode='subscribe').count() \
            - SubscriptionTask.objects.filter(callback=callback).filter(mode='unsubscribe').count()) > 0
    else:
        is_following = False
    profile = u.get_profile()
    profileform = ProfileForm(instance=profile)
    passwordform = PrettyPasswordChangeForm(user=u)
    template = 'web/user_home.html' if not is_mobile_browser(request) else 'mobile/user_home.html'
    return render_to_response(template,
                              {'u': u,
                               'profile': profile,
                               'is_following': is_following,
                               'profileform': profileform,
                               'passwordform': passwordform,
                               'tags': tags,
                               'flags': flags,
                               'notis': notis},
                              context_instance=RequestContext(request))


@login_required
def follow_user(request, username, mode='subscribe'):
    """Subscribe to user's feed, and be notified of new tags and flags
    """
    # Send PuSH subscription request to hub
    import urllib2
    import hashlib
    from django.conf import settings
    from django.core.mail import send_mail
    
    user = User.objects.get(username=username)
    h = hashlib.sha1(('%s tracking user %s at %s' % (request.user.username, 
                                                    user.username, 
                                                    settings.SECRET_KEY)))
    data = {
        'hub.callback': request.build_absolute_uri(
            reverse(follow_user_callback,
                    kwargs={'username': request.user.username,
                            'tracked_username': user.username})),
        'hub.mode': mode,
        'hub.topic': request.build_absolute_uri(
            reverse('user_feed', kwargs={'username': user.username})),
        'hub.verify': 'async',
        'hub.verify_token': h.hexdigest()}
    response = urllib2.urlopen(
        request.build_absolute_uri(reverse('subhub-hub')),
        data)
    headers = response.headers
    body = response.read()
    response.close()
    if headers.status == '' and body == 'Subscription queued':
        # Notify user of new tracker
        # TODO: Decent multipart message body
        if mode == 'subscribe':
            message = '%s [ %s ] is following you.' % (
                request.user.username, 
                request.build_absolute_uri(reverse(view_user, kwargs={'username': request.user.username})))
            send_mail('%s is following you', 
                      message, 
                      settings.DEFAULT_FROM_EMAIL, 
                      [user.email])
            return render_to_response(
                'web/user_unfollow_button.html',
                {'user': user},
                context_instance=RequestContext(request))
        elif mode == 'unsubscribe':
            # Uncomment to notify user on unfollow:
            #message = '%s [ %s ] stopped following you.' % (
            #    request.user.username, 
            #    request.build_absolute_uri(reverse(view_user, kwargs={'username': request.user.username})))
            #send_mail('%s stopped following you', 
            #          message, 
            #          settings.DEFAULT_FROM_EMAIL, 
            #          [user.email])
            return render_to_response(
                'web/user_follow_button.html',
                {'user': user},
                context_instance=RequestContext(request))
    return HttpResponse('Error %s: %s' % (headers.status, body))


def follow_user_callback(request, username, tracked_username):    
    """PuSH will send pings to this URL when a user's feed is updated
    """
    import hashlib
    from django.conf import settings
    
    tracked_user = get_object_or_404(Tag, username=tracked_username)
    user = User.objects.get(username=username)
    
    if 'hub.mode' in request.GET and request.GET['hub.mode'] == 'subscribe':
        # Confirm subscription
        h = hashlib.sha1(('%s tracking user %s at %s' % (request.user.username, 
                                                        tracked_user.username, 
                                                        settings.SECRET_KEY)))
        if request.GET['hub.topic'] == reverse('user_feed', kwargs={'username': tracked_username}) \
                and request.GET['hub.verify_token'] == h.hexdigest():
            # TODO: Consider using the hub.secret mechanism for authentication
            # All OK
            return HttpResponse(request.GET['hub.challenge'])
        else:
            return HttpResponse('Error confirming topic and token')
        
    # Create notification
    n = Notification.objects.create(
        user=user,
        subject=tracked_user.username,
        subject_url=reverse(view_user, kwargs={'username': tracked_user.username}))
        # TODO: Fetch and parse feed item
    # Notify user if necessary
    if user.get_profile().notify_by_email:
        t = loader.get_template('web/email_notification.txt')
        c = Context({'n': n})
        body_text = t.render(c)
        message = EmailMultiAlternatives('Update from trc.me', 
                                         body_text, 
                                         settings.DEFAULT_FROM_EMAIL, 
                                         [user.email])
        if hasattr(settings, 'EMAIL_ADDRESS_BOUNCE'):
            message.headers = {'Return-Path': settings.EMAIL_ADDRESS_BOUNCE}
        t = loader.get_template('web/email_notification.html')
        body_html = t.render(c)
        message.attach_alternative(body_html, 'text/html')
        message.send()
    return HttpResponse('OK')


def mobile_view_page(request, slug):
    """Return the page identified by the slug
    """
    # TODO: Use a generic view for this.
    page = get_object_or_404(Page, slug=slug)
    return render_to_response('mobile/page.html',
                              {'page': page},
                              context_instance=RequestContext(request))


@csrf_protect
def ajax_index(request):
    authform = AuthenticationForm()
    reg_form = RegistrationForm()
    return render_to_response('web/index_dialog.html', 
                              {'authform': authform,
                               'regform': reg_form},
                              context_instance=RequestContext(request))


@login_required
@csrf_protect
def ajax_create_tag(request):
    form = TagForm()
    return render_to_response('web/tag_form_dialog.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@csrf_protect
def ajax_update_tag(request, id):
    """Return HTML for the Update Tag dialog
    """
    tag = get_object_or_404(Tag, pk=base62_decode(id.upper()))
    flag_form = FlagForm()
    authform = AuthenticationForm()
    position_form = PositionForm()
    return render_to_response('web/tag_update_dialog.html', 
                              {'tag': tag,
                               'flagform': flag_form,
                               'authform': authform,
                               'positionform': position_form}, 
                              context_instance=RequestContext(request))


@csrf_protect
def ajax_view_flag(request, id):
    flag = get_object_or_404(Flag, pk=id)
    if not flag.is_visible_to(request.user):
        raise Http404
    return render_to_response('web/flag_panel.html', 
                              {'flag': flag,
                               'tag': flag.tag}, 
                              context_instance=RequestContext(request))


def ajax_view_page(request, slug):
    """Return the page identified by the slug
    """
    # TODO: Use a generic view for this.
    page = get_object_or_404(Page, slug=slug)
    return render_to_response('web/page.html',
                              {'page': page},
                              context_instance=RequestContext(request))
