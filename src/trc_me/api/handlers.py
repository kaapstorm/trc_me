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
    from piston.decorator import decorator
except ImportError:
    from decorator import decorator
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc, FormValidationError
from trc_me.api.forms import TagForm
from trc_me.core.forms import FlagPositionForm
from trc_me.core.models import Tag, Position
from trc_me.core.utils import base62_decode


def validate(v_form, operation='POST'):
    """Validates forms with files
    
    by Alexander Pugachev / peroksid
    http://bitbucket.org/jespern/django-piston/issue/124/pistonutilsvalidate-post-and-files
    cf. http://groups.google.com/group/django-piston/browse_thread/thread/6f3f964b8b3ccf72/bd1658121bb1874c?show_docid=bd1658121bb1874c&pli=1
    """
    @decorator
    def wrap(f, self, request, *a, **kwa):
        if type(operation) in [list, tuple]:
            form = v_form(*[getattr(request, x) for x in operation])
        else:
            form = v_form(getattr(request, operation))
    
        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap


class AnonymousTagHandler(AnonymousBaseHandler):
    allowed_methods = ('GET', )
    model = Tag
    exclude = ('user', 'visibility', 'created_at')
    
    def read(self, request, id=None):
        """Anonymous users can get info about public tags. 
        """
        if id:
            # Specific tag requested
            try:
                tag = Tag.objects.get(pk=base62_decode(id))
            except Tag.DoesNotExist:
                return rc.NOT_FOUND
            if not tag.visibility == 'pub':
                return rc.FORBIDDEN
            # Include the 5 most-recent public flags
            kwargs = {'incl_flags': True,
                      'incl_flags_public': True,
                      'incl_flags_end': 5}
            return tag._api_dict(**kwargs)
        # Return last five public tags
        return [tag._api_dict() for tag in Tag.objects.filter(visibility='pub')[:5]]
    
    @validate(FlagPositionForm, ['PUT', 'FILES'])
    def update(self, request, id):
        """Anonymous users can flag any tags, but flags are always hidden
        """
        try:
            tag = Tag.objects.get(pk=base62_decode(id))
        except Tag.DoesNotExist:
            return rc.NOT_FOUND
        # Create position
        position = Position.objects.create(
            latitude=request.form.cleaned_data['latitude'],
            logitude=request.form.cleaned_data['longitude'],
            accuracy=request.form.cleaned_data['accuracy'],
            geolocation_support=request.form.cleaned_data['geolocation_support'],
            sensor=request.form.cleaned_data['sensor'])
        # Create flag
        tag.flag_set.create(
            user=None,
            position=position,
            note=request.form.cleaned_data['note'],
            visibility='prv',
            img=request.form.cleaned_data['img'])
        return rc.ALL_OK


class TagHandler(BaseHandler):
    anonymous = AnonymousTagHandler
    allowed_methods = ('POST', 'GET', 'PUT', 'DELETE')
    model = Tag
    exclude = ('user', 'created_at')
    
    @validate(TagForm, ['POST', 'FILES'])
    def create(self, request):
        """Create tag from POST data.
        """
        tag = Tag.objects.create(
            user=request.user,
            description=request.form.cleaned_data['description'],
            visibility=request.form.cleaned_data['visibility'],
            img=request.form.cleaned_data.get('img', None),
            redirect_url=request.form.cleaned_data.get('redirect_url', None),
        )
        hashtags = tag.get_hashtags('description', request.POST.get('hashtags', None))
        Hashtag.objects.update_tags(tag, hashtags)
        # Return 201 Created + tag
        response = rc.CREATED
        response.write(tag.code)
        return response
    
    def read(self, request, id=None):
        """Return a specific tag, or a list of tags if no tag ID is given.
        """
        if id:
            # Specific tag requested
            try:
                tag = Tag.objects.get(pk=base62_decode(id))
            except Tag.DoesNotExist:
                return rc.NOT_FOUND
            if not tag.visibility == 'pub' and not tag.user == request.user:
                return rc.FORBIDDEN
            kwargs = {'incl_flags': True,
                      'incl_flags_end': 5}
            if tag.user == request.user:
                # The tag belongs to the user. Give them all flags
                kwargs['incl_flags_all'] = True
            else:
                # Give the user their and public flags
                kwargs['incl_flags_user'] = request.user
                kwargs['incl_flags_public'] = True
            return tag._api_dict(**kwargs)
        # Return user's last five tags
        return [tag._api_dict() for tag in Tag.objects.filter(user=request.user)[:5]]
    
    @validate(FlagPositionForm, ['PUT', 'FILES'])
    def update(self, request, id):
        """Update the position (i.e. "flag") the specified tag.
        """
        try:
            tag = Tag.objects.get(pk=base62_decode(id))
        except Tag.DoesNotExist:
            return rc.NOT_FOUND
        # Create position
        position = Position.objects.create(
            latitude=request.form.cleaned_data['latitude'],
            logitude=request.form.cleaned_data['longitude'],
            accuracy=request.form.cleaned_data['accuracy'],
            geolocation_support=request.form.cleaned_data['geolocation_support'],
            sensor=request.form.cleaned_data['sensor'])
        # Create flag
        # Hide this if the flagger or the tag owner wants it hidden
        visibility = 'pub' if (request.form.cleaned_data['visibility'] == 'pub' 
                               and tag.visbility == 'pub')\
                           else 'prv'
        tag.flag_set.create(
            user=request.user,
            position=position,
            note=request.form.cleaned_data['note'],
            visibility=visibility,
            img=request.form.cleaned_data['img'])
        # Return 200 OK
        return rc.ALL_OK
    
    def delete(self, request, id):
        """Delete the specified tag.
        """
        try:
            tag = Tag.objects.get(pk=base62_decode(id))
        except Tag.DoesNotExist:
            return rc.NOT_FOUND
        if not tag.user == request.user:
            return rc.FORBIDDEN
        tag.delete()
        return rc.DELETED

