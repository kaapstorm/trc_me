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

from django.contrib import admin
from trc_me.core.models import Flag, Tag, TagGroup

class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'description', 'user')
    list_display_links = ('id', 'code')
    list_filter = ('user',)
    ordering = ('id',)
    search_fields = ('description',)

class FlagAdmin(admin.ModelAdmin):
    list_filter = ('is_featured',)

admin.site.register(Flag)
admin.site.register(Tag, TagAdmin)
admin.site.register(TagGroup)

