# -*- coding: utf-8 -*-

import os

import jinja2
import webapp2
import logging

from webapp2_extras import i18n

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = \
    jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR), extensions=['jinja2.ext.i18n'])

jinja_environment.install_gettext_translations(i18n) 

AVAILABLE_LOCALES = ['en_US', 'ja']

class I18NRequestHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        
        locale = request.cookies.get('locale')
        if locale in AVAILABLE_LOCALES:
            i18n.get_i18n().set_locale(locale)
        else:
            header = request.headers.get('Accept-Language', '')
            locales = [locale.split(';')[0] for locale in header.split(',')]
            for locale in locales:
                logging.info('%s' % locale)
                if locale in AVAILABLE_LOCALES:
                    i18n.get_i18n().set_locale(locale)
                    break
            else:
                i18n.get_i18n().set_locale(AVAILABLE_LOCALES[0])
                
    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render_template(self, filename, template_values, **template_args):
        template = jinja_environment.get_template(filename)
        self.response.out.write(template.render(template_values))