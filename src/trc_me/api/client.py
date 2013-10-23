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

"""API piston_mini_client

cf. http://packages.python.org/piston-mini-client/
"""
from piston_mini_client import PistonAPI, returns_json

class TagAPI(PistonAPI):
    default_service_root = 'http://localhost:8000/api'

    @returns_json
    def get_tag(self, tag_id):
        return self._get('tag/%s/' % tag_id)

    @returns_json
    def create_tag(self):
        data = {
            'description': 'This is a test tag. #test',
            'visibility': 'pub',
        }
        return self._post('tag', data=data)
