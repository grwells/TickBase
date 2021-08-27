import json
import pandas as pd
import requests
from portal_interface import Portal
from briefcase import Document

'''
    Interface for querying the Neon API

    Neon organizes data in releases which contain up-to-date data. This class then checks results for keywords and returns any matches in a list of
    Document objects.
'''
class INeon(Portal):

    def __init__(self):
        self.tag = 'neon'
        self.result_type = 'data'

    # use python string parsing to check if important elements of the dict contain the keyword
    def __contains__(self, dict_item, key):
        keys = dict_item.keys()
        print('dict keys list =', keys)

        # iterate through all key-value pairs in dictionary and check for keyword
        for dict_key in keys:
            #print('dict key =', dict_key)
            # check iterable types for the key
            if hasattr(dict_item[dict_key], '__iter__') and dict_item[dict_key] is not None:
                if key in dict_item[dict_key]:
                    print('ITEM CONTAINS KEY: \'', key, '\'')
                    return True
                else:
                    continue

            # check other non-iterable types for key
            elif type(dict_item[dict_key]) is not bool and dict_item[dict_key] is not None and key in dict_item[dict_key]:
                print('ITEM CONTAINS KEY: \'', key, '\'')
                return True

            else:
                print('CAN\'T CHECK DATA:', dict_item[dict_key])

        return False

    # override the base implementation and return error code from response
    def get_code(self, response):
        return response.status_code

    def get_content(self, response):
        return ('list', response)

    # given a keyword, searches the Neon database for related data and retrieves relevant metadata
    def query(self, key):
        path = 'https://data.neonscience.org/api/v0/products'
        # download all data in current release as a list of json objects
        r = requests.get(path)

        # list to store matching metadata
        docs = []

        # check for http error codes
        if r.status_code < 400:
            result = r.json()
            print('RAW JSON\n\t', result.keys(), '\n\t', result)

            # iterate through results and check for our keyword in each returned result
            for item in result['data']:
                # ensure NEON result contains search keyword
                if self.__contains__(item, key):
                    # save the metadata for later reference
                    print('RAW DOC\n\t', item)

                    doc = Document(title=item['productName'],
                                    link=item['productCode'],
                                    abstract=item['productAbstract'],
                                    source=item['productScienceTeam'],
                                    keywords=item['keywords'],
                                    doi=item['productCodeLong'],
                                    datatype=item['productPublicationFormatType'])

                    docs.append(doc)

                else:
                    print("MISSING SEARCH KEY: \'", key, '\'')

            return docs

        else:
            print('ERROR, bad query, status code =', r.status_code)
            return None
