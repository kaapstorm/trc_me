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

from math import acos, sin, cos


def absolute_url(url):
    """An ugly hack to produce a guess at an absolute URL when the request 
    object is unavailable. 
    
    It does not consider the path to the url parameter, and relies on 
    django.contrib.sites. Rather use request.build_absolute_uri() if possible.
    @param url: The URL as returned by reverse()
    @return: A guess at the absolute URL
    """
    from django.contrib.sites.models import Site
    
    host = Site.objects.get_current().domain
    return ''.join(('http://', host, url)) 


def spherical_cosine(standpoint, forepoint):
    """Spherical cosine for sides derivation of great-circle distance formula.
    
    cf. http://en.wikipedia.org/wiki/Great-circle_distance#Spherical_cosine_for_sides_derivation
    @param standpoint: base coordinates (decimal)
    @param forepoint: destination coordinates
    @return: distance (km) 
    """
    R = 6371 # circular radius of Earth (km)
    lat1, lon1 = standpoint
    lat2, lon2 = forepoint
    d = acos(sin(lat1) * sin(lat2) \
             + cos(lat1) * cos(lat2) * cos(lon2 - lon1)) * R
    return d 


# Thank you Baishampayan Ghose
# http://stackoverflow.com/questions/1119722/base-62-conversion-in-python

# Confusing characters omitted (1, I, 0, O)
# Upper case only for easy SMSing
ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def base62_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X
    
    @param num: The number to encode
    @param alphabet: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number
    
    @param string: The encoded string
    @param alphabet: The alphabet to use for encoding
    @param uc_only: If alphabet is upper-case only, converts lower-case chars
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


# list of mobile User Agents
mobile_uas = [
    'w3c ','acs-','alav','alca','amoi','audi','avan','benq','bird','blac',
    'blaz','brew','cell','cldc','cmd-','dang','doco','eric','hipt','inno',
    'ipaq','java','jigs','kddi','keji','leno','lg-c','lg-d','lg-g','lge-',
    'maui','maxo','midp','mits','mmef','mobi','mot-','moto','mwbp','nec-',
    'newt','noki','oper','palm','pana','pant','phil','play','port','prox',
    'qwap','sage','sams','sany','sch-','sec-','send','seri','sgh-','shar',
    'sie-','siem','smal','smar','sony','sph-','symb','t-mo','teli','tim-',
    'tosh','tsm-','upg1','upsi','vk-v','voda','wap-','wapa','wapi','wapp',
    'wapr','webc','winw','xda','xda-']

mobile_ua_hints = ['Android', 'iPad', 'iPhone', 'Opera Mini', 'SymbianOS']

def is_mobile_browser(request):
    """Super simple device detection, returns True for mobile devices
    
    Credit: Ronan at mobiForge
    http://mobiforge.com/developing/story/build-a-mobile-and-desktop-friendly-application-django-15-minutes
    """
    # Check whether full or mobi have been requested
    if 'mobi' in request.GET:
        request.session['mobi'] = request.GET['mobi']
        return request.GET['mobi'] == 'True'
    if 'mobi' in request.session:
        return request.session['mobi'] == 'True'
        
    # Check user agent
    ua = request.META['HTTP_USER_AGENT'].lower()[0:4]
    if (ua in mobile_uas):
        return True
    for hint in mobile_ua_hints:
        if request.META['HTTP_USER_AGENT'].find(hint) > 0:
            return True
    return False

