# -*- coding: utf-8 -*-

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None

from i18NRequestHandler import I18NRequestHandler

class HomePage(I18NRequestHandler):
    def get(self):

        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/', HomePage)],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()