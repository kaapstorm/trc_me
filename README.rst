trc.me
======

trc.me (pronounced "track me") is a tool for crowdsourcing the geolocation of
objects. Or, in English, it's a tool for tracking your stuff.

How It Works
------------

There are three steps:

1. Tag it: Create a new tag using trc.me by filling out a quick and simple
   form. When you are done, you will be able to print the tag. The important
   part of the tag will be a URL, which looks like "trc.me/234567". Mark 
   your object with that URL, or print out the tag and attach it to the 
   object.

2. Flag it: When you find a trc.me tag, go to that web address using a PC or
   a phone to flag its location, and earn trc.me points and sometimes 
   prizes.

3. Track it: Log in to see where your stuff has been flagged.

Cool things to tag are things you lend or give away, like books and CDs; things
that travel, like shoes, or cash; things that you want to flag in cool place,
like a backpack; or your own products, so people can see how popular your brand
is! trc.me also provides an excellent way to find out more about your
customers, where they are, how they use your product, and what they think about
it.

(The square barcode on a tag is its URL written as a barcode. Modern phones
with applications like Google Goggles allow users to go straight to the URL
without typing it in.)

Get stuff
~~~~~~~~~

Flagging a code can score you trc.me points. The owner of a code can also allow
you to redeem points for other things, like cellphone airtime, or discount
vouchers. trc.me points vary according to the trc.me points rules.

trc.me points rules
~~~~~~~~~~~~~~~~~~~

* Flagging your own code scores no points.

* The further a flag is from its code's previous flag, the more points you 
  get. Scale is logarithmic.

* 20th, 30th, 40th, etc. or 200th, 300th, 400th, etc. flags score bonus 
  points.

* 10th, 100th, 1000th, etc. flags score big bonus points.

* If you are caught flagging codes falsely, your account will be suspended, 
  and your points will be revoked.

* By default, you only earn points the first time you flag a code.

Installation
------------

Requirements
~~~~~~~~~~~~

Django database requirements

subhub Installation
~~~~~~~~~~~~~~~~~~~

Setup a cron job that will process pending subscriptions and distribute
failed notifications: ::

    # Process subscriptions every 3 hours
    0    */3  * * *   user  /path/to/manage.py subhub_maintenance --subscribe

    # Distribute notifications every 15 minutes
    */15 *    * * *   user  /path/to/manage.py subhub_maintenance --distribute

HTTP Basic Authentication for API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The API allows HTTP Basic authentication. This requires a couple of .htaccess 
files and FCGI scripts. e.g.

/var/www/hosts/trc.me/.htaccess: ::

    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ trc_me.fcgi/$1 [QSA,L]

/var/www/hosts/trc.me/trc_me.fcgi: ::

    #!/usr/bin/env python

    import sys, os

    sys.path.insert(0, "/path/to/virtenv/lib/python2.5")
    sys.path.insert(1, "/path/to/virtenv/lib/python2.5/site-packages")
    sys.path.insert(2, "/path/to/src/trc_me/src")

    os.environ['DJANGO_SETTINGS_MODULE'] = "trc_me.settings"

    from django.core.servers.fastcgi import runfastcgi
    runfastcgi(method="threaded", daemonize="false")

/var/www/hosts/trc.me/api/.htaccess: ::

    AuthType Basic
    AuthName "trc.me API"
    AuthBasicProvider wsgi
    WSGIAuthUserScript /path/to/src/trc_me/src/trc_me/wsgi/auth.wsgi
    Require valid-user

    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ ../trc_me.fcgi/api/$1 [QSA,L]

The WSGI script provided in src/trc_me/wsgi/auth.wsgi will need the path in 
the following line ::

    sys.path.append('/path/to/src/trc_me/src')

to be changed to suit the deployment environment.

Credits
-------

`famfamfam Silk icons`_


.. _famfamfam Silk icons: http://www.famfamfam.com/lab/icons/silk/
