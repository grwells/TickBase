'''
    @author Garrett Wells
    @date   12/31/2021
'''

import d1_client
from briefcase import Document
import requests
from portal_interface import Portal
import xml.etree.ElementTree as ET


'''
    Interface for querying LTER data repository. https://lternet.edu/
'''
class ILTER(Portal):

    def __init__(self):
        self.tag = 'LTER'
        self.result_type = 'mixed'

    def get_code(self, response):
        return response.status_code

    def get_content(self, response):
        return ('list', response)

    def query(self, key):
        self.base_url = 'https://pasta.lternet.edu/package/search/eml?{}'
        query_str = 'q=' + key + '&fl=title,author,doi,abstract,resources'

        r = requests.get(self.base_url.format(query_str))

        if r.status_code == 200:
            # parse xml
            docs = []

            root = ET.fromstring(r.text)
            print('RAW XML:\n\t\t', r.text)
            print('\t\tattributes:', root.attrib)

            # iterate over each document returned by LTER and convert to briefcase document
            for child in root:
                print('\t\tTAG:', child.tag)
                print(child)

                resDict = {}
                grndchld_txt = ''
                authors_list = []

                # parse meta from returned documents
                for grandchild in child:
                    if grandchild.tag == 'authors':
                        author_count = 0
                        # convert xml author tags to string "last, first; last, first"
                        for name in grandchild:
                            #print('\t\t\t', name.text)
                            if author_count == 0:
                                authors_list.append(name.text)
                                author_count = author_count + 1
                            else:
                                authors_list.append(name.text)
                                author_count = author_count + 1

                        resDict[grandchild.tag] = authors_list
                        print('\t\tgrandchild tag =', grandchild.tag, ' text =', authors_list)

                    else:
                        print('\t\tgrandchild tag =', grandchild.tag, ' text =', grandchild.text)
                        resDict[grandchild.tag] = grandchild.text

                doc = Document(title=resDict['title'], authors=authors_list, 
                                abstract=resDict['abstract'], doi=resDict['doi'], datatype='unkown')
                #doc.print()
                docs.append(doc)

            return docs

        else:
            return []
