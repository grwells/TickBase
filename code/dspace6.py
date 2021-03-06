"""
    DSpace API 1.0

    Compatible with DSpace 6.x backend

    @author:    Garrett Wells
    @date:      08/2021
"""

import os
import csv
import json
import requests
import warnings
from bs4 import BeautifulSoup
from doiresolver import DOIResolver
from briefcase import Briefcase
from briefcase import Document

# Class provides API for DuraSpace development
class DSpace:

    # DSpace 6.x as of 08/2021
    _nkn_base_url = 'http://dspace-dev.nkn.uidaho.edu:8080/rest'
    _csrf_tkn = ''      # token received from server with each request to verify source of requests, changes periodically
   
    def __init__(self, username='', passwd='', base_url='', csrf_token=''):
        self.username = username
        self.passwd = passwd
        self.csrf_token = csrf_token

        # default value of session id, shows not logged in if ''
        # may be able to use system without logging in but getting session status will not
        # be available
        self.session_id = ''

        if base_url == '':
            self.base_url = self._nkn_base_url
        else:
            self.base_url = base_url + '/rest'


    # Check if REST API is installed
    def api_running(self):
        r = requests.get(self.base_url+'/test')
        if r.text == 'REST api is running':
            return True
        else:
            return False


    # attempt to authenticate, return true if successful
    def authenticate(self):
        #payload = 'email=garrettrwells%40gmail.com&password=GW091799'
        payload='email={}&password={}'.format(self.username, self.passwd)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

        r = requests.post(self.base_url + '/login', headers=headers, data=payload)

        if r.status_code != 200:
            print(self.base_url+'/login')
            #raise Exception('failed authentication, HTTP code ' + str(r.status_code))
            return False
        else:
            print('successful authentication, HTTP code ', r.status_code)
            # get the JSESSIONID which will be used to authenticate future requests
            self.session_id = r.cookies
            print(r.cookies['JSESSIONID'])
            return True



    # log the current user out of the database
    def logout(self):
        r = requests.post(self.base_url + '/logout', cookies=self.session_id)


    # get status of tyhe user token/API
    def get_status(self):
        if self.session_id == '':
            print('Warning: get_status() not conclusive because you are not logged in currently.\nIf login is not required you may still be able to use server, but you can\'t use this function.')
            return

        r = requests.get(self.base_url+'/status')

        if r.status_code != 200:
            #warnings.warn('connection to '+self.base_url+' failed')
            return False
        else:
            print(r.text)
            return True


    '''
        Get the status of the connection to dspace and return a dictionary with the following information:

            okay: boolean state of connection, true if good connection
            authenticated: true if the session has a valid JSESSIONID, can only be true if user has submitted email and passwd using /login
            email: email of the user whose account was used for authentication
            fullname: name/role associated with this account
            apiVersion: version of the API running on server
            sourceVersion: version of code on server
    '''
    def get_session_status(self):
        r = requests.get(self.base_url+'/status')
        json_output = r.json()

        return json_output 


    # get the DSpace metadata for a single item specified by the uuid
    def get_item_metadata(self, uuid):
        r = requests.get(self.base_url + '/items/{}/metadata'.format(uuid))

        if r.status_code != 200:
            raise Exception('unable to get item: ' + uuid + '\n\t' + r.text)
        else:
            # convert from DSpace complex metadata format to simple key value pair dict
            dense_meta = {} # dictionary with simple key, value pairs
            for meta in r.json():
                dense_meta[meta['key']] = meta['value']
            return dense_meta


    # Get an array of all the communities in the repository
    def get_communities(self, debug=True):
        communities = []
        offset = 0

        # run loop infinitely or until server can't give full page of results
        while True:
            r = requests.get(self.base_url+'/communities?offset={}&limit=100'.format(offset))

            # make sure request went through, otherwise throw error
            if r.status_code != 200:
                raise Exception('connnection to '+self.base_url+' failed')

            communities.append(r.json())

            # check if there are more results beyond this page
            if len(r.json()) < 100:
                break
            else:
                offset = offset + 100

        # print info about all communities returned
        if debug:
            for i in r.json():
                print('COMMUNITY \'{}\':'.format(i['name']))
                print('\tUUID:', i['uuid'], '\n\tHANDLE:', i['handle'])

        return communities


    # Get an array of all the collections in the repository
    def get_collections(self, debug=True):
        collections = []
        offset = 0

        # run loop infinitely or until server can't give full page of results
        while True:
            r = requests.get(self.base_url+'/collections?offset={}&limit=100'.format(offset))

            # make sure request went through, otherwise throw error
            if r.status_code != 200:
                raise Exception('connnection to '+self.base_url+' failed')

            collections.append(r.json())

            # check if there are more results beyond this page
            if len(r.json()) < 100:
                break
            else:
                offset = offset + 100

        # print info about all communities returned
        if debug:
            for i in r.json():
                print('COLLECTION \'{}\':'.format(i['name']))
                print('\tUUID:', i['uuid'], '\n\tHANDLE:', i['handle'])

        return collections[0]


    # Get an array of all the items in the repository
    def get_items(self, cid='', debug=False):
        items = []
        offset = 0

        # adjust for cid in urls
        if cid == '':
            url = self.base_url + '/items?offset={}&limit=100'
        else:
            url = self.base_url + '/collections/{}/items?offset{}&limit=100'.format(cid, '{}')

        i = 0

        # run loop infinitely or until server can't give full page of results
        while True and i < 5:
            r = requests.get(url.format(offset))

            # make sure request went through, otherwise throw error
            if r.status_code != 200:
                raise Exception('connnection to '+self.base_url+' failed')

            items.append(r.json())

            # check if there are more results beyond this page
            if len(r.json()) < 100:
                break
            else:
                offset = offset + 100

            i = i + 1

        # print info about all communities returned
        if debug:
            for i in r.json():
                print('ITEM \'{}\':'.format(i['name']))
                print('\tUUID:', i['uuid'], '\n\tHANDLE:', i['handle'])

        return items[0]


    # Get an array of all the collections in the repository
    def get_bitstreams(self, debug=True):
        bitstreams = []
        offset = 0

        # run loop infinitely or until server can't give full page of results
        while True:
            r = requests.get(self.base_url+'/bitstreams?offset={}&limit=100'.format(offset))

            # make sure request went through, otherwise throw error
            if r.status_code != 200:
                raise Exception('connnection to '+self.base_url+' failed')

            bitstreams.append(r.json())

            # check if there are more results beyond this page
            if len(r.json()) < 100:
                break
            else:
                offset = offset + 100

        # print info about all communities returned
        if debug:
            for i in r.json():
                print('BITSTREAMS \'{}\':'.format(i['name']))
                print('\tUUID:', i['uuid'], '\n\tHANDLE:', i['handle'])

        return bitstreams


    # return the object specified by the handle passed to this function
    def get_handle(self, handle=''):
        if handle == '':
            raise Exception('handle is empty, please input a value')

        r = requests.get(self.base_url+'/handle/{}'.format(handle))

        if r.status_code != 200:
            raise Exception('connection to '+self.base_url+' failed')
        else:
            print('After Get Handle:', r.json())
            return r.json()


    # get the metadata from DSpace for an item identified by UUID
    def get_item(self, uuid):
        r = requests.get(self.base_url+'/items/{}'.format(uuid))

        if r.status_code != 200:
            raise Exception('connection to '+self.base_url+' failed')
        else:
            print('After Get Item:', r.json())
            return r.json()


    # update the metadata record for an item using a list structure or the doi of the item
    def update_item(self, ditem, new_meta={}):
        doi = ''
        if ditem is {} and new_meta is {}:
            raise Exception('insufficient information, need dspace item json object or doi resolver json object')

        elif ditem is not {}:
            # get metadata so we can get DOI to resolve
            #print('DITEM UUID:', ditem['uuid'])
            dspace_meta = self.get_item_metadata(ditem['uuid'])

            # handle errors with bad/insufficient metadata
            if 'dc.identifier' not in dspace_meta.keys() or dspace_meta['dc.identifier'] == '':
                print('no doi attached to object\n\t\t', dspace_meta)
                return

            doi = dspace_meta['dc.identifier']
            dres = DOIResolver()
            new_meta = dres.get_meta(doi)
            #print('NEW META:\n\t\t', new_meta)

            # check for keys before adding them to metadata
            abstract = ''
            URL = ''
            authors = ''
            publisher = ''
            date = ''
            if 'abstract' in new_meta.keys():
                abstract = new_meta['abstract']
            if 'URL' in new_meta.keys():
                URL = new_meta['URL']
            if 'author' in new_meta.keys():
                authors = dres.authors_to_str(new_meta['author'])
            if 'publisher' in new_meta.keys():
                publisher = new_meta['publisher']

            # format metadata and upload
            payload = json.dumps([
                {
                    'key': "dc.identifier.uri", 
                    'value': URL, 
                    'language': None
                },
                {
                    'key': 'dc.contributor.author',
                    'value': authors,
                    'language': None
                },
                {
                    'key': 'dc.publisher',
                    'value': publisher,
                    'language': None
                },
                {
                    'key': 'dc.description.abstract',
                    'value': abstract,
                    'language': None
                },
                {
                    'key': 'dc.date',
                    'value': dres.get_date(new_meta),
                    'language': None
                }
            ])

            headers = {
                'Content-Type': 'application/json'
            }

            r = requests.post(self.base_url + '/items/{}/metadata'.format(ditem['uuid']), headers=headers, data=payload, cookies=self.session_id)

            if r.status_code != 200:
                raise Exception('could not update item', r.text)


    # update all items in a collection or list of collections
    def update_items(self, cids=[]):
        items = []

        # get all known metadata for items in specified collections
        # will use uuids to resolve dois
        for cid in cids:
            # get items in collection
            item_list = self.get_items(cid=cid)
            # add each new item to the comprehensive list
            for item in item_list:
                items.append(item)

        # for each item, get uuid and doi by getting item metadata(dspace), then update that item
        for item in items:
            self.update_item(item)


    # Create a new community
    # TODO: test this more if needed and clean up later
    def create_community(self, id=000, name='', handle='', type='community', link='/rest/communities/000',
                        expand=["parentCommunity","collections","subCommunities","logo","all"], logo=None, parentCommunity=None,
                        copyrightText='', introductoryText='', shortDesc='', sidebarText='', countItems=0, subCommunities=[], collections=[]):

        '''
        community_obj = { "id":id,
                          "name":name,
                          "handle":handle,
                          "type":type,
                          "link":link,
                          "expand":expand,
                          "logo":logo,
                          "parentCommunity":parentCommunity,
                          "copyrightText":copyrightText,
                          "introductoryText":introductoryText,
                          "shortDescription":shortDesc,
                          "sidebarText":sidebarText,
                          "countItems":countItems,
                          "subcommunities":subCommunities,
                          "collections":collections
                        }'''

        community_obj = {
            'id': '12345',
            'name': name,
            'link': link,
            'handle': handle
        }

        r = requests.put(self.base_url + '/communities', data=community_obj)


    # TODO implement this function
    def create_collection(self, community=''):
        print('Implement create collection!')


    # create an item and add to collection
    def create_item(self, cid, title, author, description, doi):
        dres = DOIResolver()
        if doi != '':
            try:
                sup_meta = dres.get_meta(doi)
            except:
                sup_meta = {}
        else:
            sup_meta = {}

        if 'abstract' in sup_meta.keys():
            abstract = sup_meta['abstract']
        else:
            abstract = ''

        # construct new item object with metadata using dublin core identifiers, convert json dict to string
        payload = json.dumps(
                    {
                        "metadata": [
                            {
                                "key": "dc.contributor.author",
                                "value": author
                            },
                            {
                                "key": "dc.description",
                                "value": description
                            },
                            {
                                "key": "dc.title",
                                "value": title
                            },
                            {
                                "key": "dc.identifier",
                                "value": doi
                            },
                            {
                                'key': 'dc.date',
                                'value': dres.get_date(sup_meta)
                            },
                            {
                                'key': 'dc.description.abstract',
                                'value': abstract
                            }
                        ]
                    }
                )

        # construct headers with session id(authentication key) and submit request
        print('Session ID', self.session_id)
        headers = {
            'Authorization': 'Bearer 999C94C5A92473D707225B890C08C398',
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID='+self.session_id['JSESSIONID']
        }
        r = requests.request("POST", self.base_url+'/collections/{}/items'.format(cid), headers=headers, data=payload)

        # check status of item post and print message if unsuccessful
        if r.status_code != 200:
            print('HTTP ERROR RESPONSE:\n\t',r.text)
        else:
            print('SUCCESS: ', r.status_code)


    # remove an item from the collection, requires UUID instead of handle
    def delete_item(self, item_id):
        if '/' in item_id:
            raise Exception('Identifier passed to delete item is invalid, contains \'\/\' try using UUID instead of handle')

        r = requests.delete(self.base_url+'/items/{id}'.format(id=item_id), cookies=self.session_id)

        if r.status_code != 200:
            raise Exception('Unable to remove item from collection, connection failed\n\tHTTP CODE:{}\n\tHTTP BODY{}'.format(r.status_code, r.text))

    # delete all items from the dspace collection specified
    def empty_collection(self, cid):
        items = self.get_items(cid=cid)
        print(items)
        for item in items:
            print(item)
            self.delete_item(item['uuid'])

    '''
        iterate through csv and convert each entry into a dspace 'item'
        then create a new dspace collection and place items in the collection.

        TODO: decide whether this is a helpful feature or not 
    '''
    def export_to_Briefcase(self, filepath):
        # list of XML objects formatted as dspace 'items' to add to the repository
        items = []

        case = Briefcase()

        # currently just prints out the key word
        with open(filepath, 'r') as csv_file:
            r = csv.reader(csv_file)
            for row in r:
                doc = Document(title=row[7], 
                    authors=row[1], link='', abstract=row[0], 
                    source=row[6], keywords=row[5], doi=row[2], datatype=row[3], date=row[4])
                
                case.add(doc.to_dictionary())

        return case