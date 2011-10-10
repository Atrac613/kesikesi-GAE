# -*- coding: utf-8 -*-

import os

from django.utils import translation
from google.appengine.ext import webapp
from cookies import Cookies

class I18NRequestHandler(webapp.RequestHandler):

    def initialize(self, request, response):
        webapp.RequestHandler.initialize(self, request, response)
 
        self.request.COOKIES = Cookies(self)
        self.request.META = os.environ
        self.reset_language()

    def reset_language(self):

        # Decide the language from Cookies/Headers
        language = translation.get_language_from_request(self.request)
        translation.activate(language)
        self.request.LANGUAGE_CODE = translation.get_language()

        # Set headers in response
        self.response.headers['Content-Language'] = translation.get_language()
#        translation.deactivate()