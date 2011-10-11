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
import logging
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

admin_password = "bobby"

#Database Objects
class Location(db.Model):
    name = db.StringProperty(required=True)
    
class MenuItem(db.Model):
    location = db.ReferenceProperty(Location, collection_name='menu_items')
    name = db.StringProperty()
    price = db.FloatProperty()

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

class LocationsHandler(webapp.RequestHandler):
    def get(self):
        query = Location.all(keys_only=True)
        locations_list = list(key.name() for key in query)
        locations_list.sort()
        self.response.out.write(json.dumps(locations_list))
        
    def post(self):
        password = self.request.get('password')
        if (password!=admin_password): return
        location_name = self.request.get('name')
        location = Location.get_by_key_name(location_name)
        if not location:
            location = Location(key_name=location_name, name=location_name)
            location.put()
            json_dict = {
                'success': True,
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success': False,
                'reason': "Location exists"
            }
            self.response.out.write(json.dumps(json_dict))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/auth', AuthHandler),
                                          ('/locations', LocationsHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
