# -*- coding: utf-8 -*-

import webapp2

from i18NRequestHandler import I18NRequestHandler

class HomePage(I18NRequestHandler):
    def get(self):
        template_values = {
        }
        
        self.render_template('index.html', template_values)
        
app = webapp2.WSGIApplication(
                              [('/', HomePage)],
                              debug=False)