#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

admin_password = "bobby"

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

class AuthHandler(webapp.RequestHandler):
    def post(self):
        password = self.request.get('password')
        if password==admin_password:
            json_dict = {
                'success': True,
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success': False,
            }
            self.response.out.write(json.dumps(json_dict))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/auth', AuthHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
