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
from django.utils import simplejson as json
import logging
import urllib
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

admin_password = "bobby"

"""
Database Objects
    I decided to use the object name property as it's key. This makes the URI scheme very human
    readable, but makes it a bit harder to change the name. In many cases it would be better to use a
    random unique key rather.
"""
class Location(db.Model):
    name = db.StringProperty(required=True)
    
class MenuItem(db.Model):
    location = db.ReferenceProperty(Location, collection_name='menu_items')
    name = db.StringProperty()
    price = db.FloatProperty()
    category = db.StringProperty()
    image = db.BlobProperty()

"""
Request Handlers
    all POST, PUT, and DELETE requests are authenticated against the 'admin_password'.
    normally I'd use a random session token to authenticate rather than a static password.
"""
# /
class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')
# /auth
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
# /locations
class LocationsHandler(webapp.RequestHandler):
    # outputs list of locations in json
    def get(self):
        query = Location.all(keys_only=True)
        locations_list = list(key.name() for key in query)
        locations_list.sort()
        json_dict = {
            'success': True,
            'Locations':locations_list,
        }
        self.response.out.write(json.dumps(json_dict))
    # adds a location
    def post(self):
        json_body = json.loads(self.request.body)
        password = json_body['password']
        if (password!=admin_password): return
        location_name = json_body['name']
        location = Location.get_by_key_name(location_name)
        if not location:
            location = Location(key_name=location_name, name=location_name)
            location.put()
            query = Location.all(keys_only=True)
            locations_list = list(key.name() for key in query)
            if location_name not in locations_list:
                locations_list.append(location_name)
            locations_list.sort()
            json_dict = {
                'success': True,
                'Locations':locations_list,
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success': False,
                'message': "Location exists"
            }
            self.response.out.write(json.dumps(json_dict))
    """
    NOT IMPLEMENTED
    def put(self):
        #replace all locations
    def delete(self):
        #delete all locations 
    """
# /locations/[location_name]
class SingleLocationHandler(webapp.RequestHandler):
    # outputs location name and list of menu items in json
    def get(self, location_name):
        location = Location.get_by_key_name(location_name)
        if location:
            items_query = MenuItem.all(keys_only=False).ancestor(location)
            items_dict= {}
            for item in items_query:
                if not items_dict.has_key(item.category):
                    items_dict[item.category] = [] 
                items_dict[item.category].append({'name':item.name, 'price':str(item.price), 'category':item.category})
            json_dict = {          
                'success': True,
                'name': location_name,
                'items': items_dict
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success': False,
                'message': 'Could not find that location',
            }
            self.response.out.write(json.dumps(json_dict))
    # adds menu item to a location
    def post(self, location_name):
        json_dict = json.loads(self.request.get('json'))
        password = json_dict['password']
        if (password!=admin_password): return
        location = Location.get_by_key_name(location_name)
        if not location:
            json_dict = {
                'success': False,
                'message': 'Could not find that location',
            }
            self.response.out.write(json.dumps(json_dict))
            return
        # retrieve all the json info
        item_name = json_dict['name']
        item_category = json_dict['category']
        item_price = float("%.2f" % float(json_dict['price']))
        # create item key
        item_key = db.Key.from_path('Location', location_name, 'MenuItem', item_name)
        menu_item = MenuItem.get(item_key)
        # if item already exists, output error
        if menu_item:
            json_dict = {
                'success': False,
                'message': 'Item exists with that name, try editing the previous item instead',
            }
            self.response.out.write(json.dumps(json_dict))
            return
        logging.info(json_dict)
        # create new MenuItem with key
        menu_item = MenuItem(parent=location.key(), key_name=item_key.name())
        menu_item.name = item_name
        menu_item.price = item_price
        menu_item.category = item_category
        # retrieve image data and convert to AppEngine blob
        item_image = self.request.get('image')
        menu_item.image = db.Blob(item_image)
        menu_item.put()
        json_dict = {
            'success': True,
        }
        self.response.out.write(json.dumps(json_dict))
    # deletes location  
    def delete(self, location_name):
        """
        #Currently, AppEngine does not accept bodies on http DELETE requests
        #This is an odd behavior, because it works on the development server... just not in production
        json_body = json.loads(self.request.body)
        password = json_body['password']
        if (password!=admin_password): return
        """
        location = Location.get_by_key_name(location_name)
        if location:
            child_query = MenuItem.all(keys_only=True).ancestor(location)
            to_delete = list(key.name() for key in child_query)
            to_delete.append(location)
            db.delete(to_delete)
            json_dict = {
                'success': True,
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success': False,
                'message': 'Location does not exist',
            }
            self.response.out.write(json.dumps(json_dict))
    """
    NOT IMPLEMENTED
    def put(self):
        #replace all menu items
    """
# /locations/[location_name]/[item_name]
class ItemHandler(webapp.RequestHandler):
    # outputs single item in json
    def get(self, location_name, item_name):
        location_name = urllib.unquote(location_name)
        item_name = urllib.unquote(item_name)
        key = db.Key.from_path('Location', location_name, 'MenuItem', item_name)
        item = MenuItem.get(key)
        if item:
            json_dict = {
                'success':True,
                'name':item.name,
                'category':item.category,
                'price':str(item.price)
            }
            self.response.out.write(json.dumps(json_dict))
        else:
            json_dict = {
                'success':False,
                'message':'Could not find menu item'
            }
            self.response.out.write(json.dumps(json_dict))
    # updates single, existing item
    def post(self, location_name, item_name):
        json_dict = json.loads(self.request.get('json'))
        password = json_dict['password']
        if (password!=admin_password): return
        location_name = urllib.unquote(location_name)
        item_name = urllib.unquote(item_name)
        key = db.Key.from_path('Location', location_name, 'MenuItem', item_name)
        item = MenuItem.get(key)
        if not item:
            json_dict = {
                'success': False,
                'message':'Item does not exist'
            }
            self.response.out.write(json.dumps(json_dict))
            return
        if item:
            #first check if the new name already exists, if not we can't change this item
            new_key = db.Key.from_path('Location', location_name, 'MenuItem', json_dict['name'])
            if json_dict['name']!=item_name:
                new_item = MenuItem.get(new_key)
                if new_item:
                    json_dict = {
                                 'success': False,
                                 'message':'Name already taken'
                    }
                    self.response.out.write(json.dumps(json_dict))
                    return
                #cannot change key names in app engine datastore so we have to delete and remake
                item.delete()
                item = MenuItem(parent=db.Key.from_path('Location', location_name), key_name=json_dict['name'])
            item.name = json_dict['name']
            item.category = json_dict['category']
            item.price = float("%.2f" % float(json_dict['price']))
            item.image = db.Blob(self.request.get('image'))
            item.put()
        json_dict = {
            'success': True,
        }
        self.response.out.write(json.dumps(json_dict))
    # deletes single item
    def delete(self, location_name, item_name):
        """
        #Currently, AppEngine does not accept bodies on http DELETE requests
        #This is an odd behavior, because it works on the development server... just not in production
        json_body = json.loads(self.request.body)
        password = json_body['password']
        if (password!=admin_password): return
        """
        location_name = urllib.unquote(location_name)
        item_name = urllib.unquote(item_name)
        key = db.Key.from_path('Location', location_name, 'MenuItem', item_name)
        item = MenuItem.get(key)
        if item:
            item.delete()
            json_dict = {
                'success': True,
            }
            self.response.out.write(json.dumps(json_dict))
        else:
           json_dict = {
                'success': False,
                'message':'Item does not exist'
           }
           self.response.out.write(json.dumps(json_dict)) 
    """
    NOT IMPLEMENTED
    def put(self):
        #updating a menu item should probably go here, but it's easier to handle image uploads with a post request
    """
# /locations/[location_name]/[item_name]/image
class ItemImageHandler(webapp.RequestHandler):
    # serves image content
    def get(self, location_name, item_name):
        location_name = urllib.unquote(location_name)
        item_name = urllib.unquote(item_name)
        key = db.Key.from_path('Location', location_name, 'MenuItem', item_name)
        item = MenuItem.get(key)
        if item:
            self.response.headers['Content-Type'] = "image/jpeg"
            self.response.out.write(item.image)
        else:
            self.response.out.write('no good')

# /batch/raise_prices
class BatchRaisePricesHandler(webapp.RequestHandler):
    def post(self):
        json_dict = json.loads(self.request.body)
        password = json_dict['password']
        if password!=admin_password:
            json_resp = {
                'success':False,
                'message':'Not authorized',
            }
            self.response.out.write(json.dumps(json_resp))
        else:
            location_name = json_dict['location']
            value = float(json_dict['price'])
            location = Location.get_by_key_name(location_name)
            if location:
                #create list for batch put
                tosave = []
                menu_items = MenuItem.all(keys_only=False).ancestor(location)
                for item in menu_items:
                    item.price = item.price + value
                    tosave.append(item)
                #batch put
                db.put(tosave)
                json_resp = {
                    'success':True,
                }
                self.response.out.write(json.dumps(json_resp))

# /batch/remove_images
class BatchRemoveImagesHandler(webapp.RequestHandler):
    def post(self):
        json_dict = json.loads(self.request.body)
        password = json_dict['password']
        if password!=admin_password:
            json_resp = {
                'success':False,
                'message':'Not authorized',
            }
            self.response.out.write(json.dumps(json_resp))
        else:
            location_name = json_dict['location']
            location = Location.get_by_key_name(location_name)
            if location:
                #create list for batch put
                tosave = []
                menu_items = MenuItem.all(keys_only=False).ancestor(location)
                for item in menu_items:
                    item.image = None
                    tosave.append(item)
                #batch put
                db.put(tosave)
                json_resp = {
                    'success':True,
                }
                self.response.out.write(json.dumps(json_resp))
            else:
                json_resp = {
                    'success':False,
                    'message':'Location does not exist',
                }
                self.response.out.write(json.dumps(json_resp))
            
            
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/auth', AuthHandler),
                                          ('/locations', LocationsHandler),
                                          (r'/locations/([^/]*)', SingleLocationHandler),
                                          (r'/locations/([^/]*)/([^/]*)', ItemHandler),
                                          (r'/locations/([^/]*)/([^/]*)/image', ItemImageHandler),
                                          ('/batch/raise_prices', BatchRaisePricesHandler),
                                          ('/batch/remove_images', BatchRemoveImagesHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
