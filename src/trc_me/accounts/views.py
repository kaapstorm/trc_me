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
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from trc_me.web.views import index
from trc_me.accounts.forms import *
from trc_me.core.utils import is_mobile_browser
from trc_me.web.views import view_user


def ajax_login(request):
    """Logs in user asynchronously
    """
    result = {'success': False}
    if request.method == 'POST':
        form = PrettyAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], 
                                password=form.cleaned_data['password']) 
            login(request, user)
            result['success'] = True
            result['username'] = user.username
        else: 
            result['error'] = u'Unable to log in. Please check your username and password.'
    return HttpResponse(to_json(result),
                        mimetype='application/json')    


def ajax_register(request):
    result = {'success': False}
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Try to create user
                user = User.objects.create_user(form.cleaned_data['username'], 
                                                form.cleaned_data['email'], 
                                                form.cleaned_data['password1'])
                # Log in user
                user = authenticate(username=form.cleaned_data['username'], 
                                    password=form.cleaned_data['password1'])
                login(request, user)
                result['success'] = True
                result['username'] = user.username                
            except:
                # Form valid, but we still got a database error.
                mail_admins('Unable to create user', 
                            'Username: %s\nE-mail: %s' % (user.username, 
                                                          user.email))
                result['error'] = u'Unable to create user. Please try again later.'
        else:
            # TODO: Use field names instead of dropping them 
            # TODO: Use custom validator
            result['error'] = u' '.join([unicode(v) for v in form.errors.values()])
    return HttpResponse(to_json(result),
                        mimetype='application/json')    


# UNUSED
# cf. django.contrib.auth.views.login
def mobile_login(request):
    """Log in form for mobile users
    """
    if request.method == 'POST':
        form = PrettyAuthenticationForm(data=request.POST)
        next = request.POST['next']
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], 
                                password=form.cleaned_data['password']) 
            login(request, user)
            return HttpResponseRedirect(next)
    else:
        form = PrettyAuthenticationForm(request)
        next = reverse('trc_me.web.views.index')
    return render_to_response('mobile/login.html',
                              {'form': form,
                               'next': next},
                              context_instance=RequestContext(request))    


def mobile_register(request):
    """Registration form for mobile users
    """
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST)
        next = request.POST['next']
        if form.is_valid():
            user = User.objects.create_user(form.cleaned_data['username'], 
                                            form.cleaned_data['email'], 
                                            form.cleaned_data['password1'])
            # Log in user
            user = authenticate(username=form.cleaned_data['username'], 
                                password=form.cleaned_data['password1'])
            login(request, user)
            #login(request, form.get_user())
            # TODO: Check next
            return HttpResponseRedirect(next)
    else:
        form = RegistrationForm()
        next = reverse('trc_me.web.views.index')
    return render_to_response('mobile/register.html',
                              {'form': form,
                               'next': next},
                              context_instance=RequestContext(request))


@csrf_protect
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PrettyPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(view_user, kwargs={'username': request.user.username}))
    else:
        form = PrettyPasswordChangeForm(user=request.user)
    return render_to_response('mobile/user_chpwd.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@login_required
def ajax_change_password(request):
    result = {'success': False}
    if request.method == 'POST':
        form = PrettyPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            result['success'] = True
        else:
            # TODO: Use field names instead of dropping them 
            result['error'] = u' '.join([unicode(v) for v in form.errors.values()])
    return HttpResponse(to_json(result),
                        mimetype='application/json')


#@device
@csrf_protect
@login_required
def edit_user(request):
    profile = request.user.get_profile()
    if request.method == 'POST':
        profileform = ProfileForm(request.POST, request.FILES, instance=profile)
        if profileform.is_valid():
            profileform.save()
            return HttpResponseRedirect(reverse(view_user, kwargs={'username': request.user.username}))
    else:
        profileform = ProfileForm(instance=profile)
    template = 'web/user_edit.html' if not is_mobile_browser(request) else 'mobile/user_edit.html'
    return render_to_response(template,
                              {'profile': profile,
                               'profileform': profileform},
                              context_instance=RequestContext(request))


def logout_view(request):
    """Log out user, redirect to landing page
    """
    logout(request)
    return HttpResponseRedirect(reverse(index))
