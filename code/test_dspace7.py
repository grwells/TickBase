'''
    
    @author Garrett Wells
    @date   12/31/2021

'''


from dcxml import dcxml
from dspace7 import DSpace
from crawler import Crawler
from mendeleydata_interface import IMendeley_Data
from knb_interface import IKNB
from mendeleydata_interface import IMendeley_Data
from mendeley_interface import IMendeley
from doiresolver import DOIResolver
import requests
import unittest

# test framework for the DSpace interface
class TestDSpace(unittest.TestCase):

    def __init__(self):
        # control loop to test all of the available functions and larger paths too

        quit = False

        while not quit:
            self.print_menu()
            selection = input('selected test option:')
            if selection == 'q':
                break
            self.run_test_by_index(int(selection))


    def print_menu(self):
        menu = '''
                press q to quit...
                TEST FUNCTIONS
                        [0]  test authentication
                        [1]  test crawler integration
                        [2]  test single item creation
                        [3]  test single item update
                        [4]  test update all items
                        [5]  test get single item
                        [6]  test get all items in collection
                        [7]  test delete item
                        [8]  test get delete all items in collection
                        [9]  test get metadata for single item
                        [10] test all
                '''

        print(menu)

    def run_test_by_index(self, i):
        print('RUNNING TEST...')

        func = [self.test_authenticate, self.test_crawler_integration, self.test_single_item, self.test_update_item,
                    self.test_update_items, self.test_get_item, self.test_get_items,
                    self.test_delete_item, self.test_delete_items, self.test_get_metadata, self.test_all]

        if(i > len(func) or i < 0):
            print('ERROR, selection out of bounds')
        else: # run the test
            func[i]()


    def test_all(self):
        points = self.test_authenticate() + self.test_crawler_integration() + self.test_single_item() + self.test_get_items() + self.test_get_item() + self.test_update_item() + self.test_update_items() + self.test_get_metadata() + self.test_delete_items()
        print('TEST RESULTS:\n\tscore = ', str(points) + '/9', sep='')

    # test authenticating a session
    def test_authenticate(self):
        print("TESTING AUTHENTICATION")
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        container = dspc.get_status()
        dspc.logout()

        #self.assertEqual(container, True)

        return 1

    # test importing data from search
    def test_crawler_integration(self):
        print("TESTING CRAWLER")
        gs = IMendeley()
        #da_craw = Crawler(repository_interface=gs, csv_path='C:/Users/deepg/Documents/TickBase/searches/test_search.csv')
        da_craw = Crawler(repository_interface=gs, csv_path='/mnt/c/Users/deepg/Documents/TickBase/searches/test_search.csv')
        da_craw.search_all()
        da_craw.export_to_dspace(cid='59c66749-1ca0-40ee-844e-504c646f4632', uname='sheneman@uidaho.edu', passwd='foo')
        return 1

    # test creation of a single item
    def test_single_item(self):
        print("TESTING CREATE SINGLE ITEM")
        a = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        a.authenticate()
        #a.get_status()
        a.create_item(cid='59c66749-1ca0-40ee-844e-504c646f4632', title='foo 2', authors=['H. G. Wells', 'Wells, H. G.'], description='test upload', doi='10.12345/123124')
        #a.delete_item('123456789/18')
        #a.get_items()
        a.logout()
        return 1

    # test updating a single item
    def test_update_item(self):
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        item = dspc.get_item(uuid='2e003b53-da42-45a9-9172-c8f1cfeb2ece')
        dspc.update_item(ditem=item)
        return 1

    # test updating all items in a collection
    def test_update_items(self):
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        dspc.update_items(cids=['59c66749-1ca0-40ee-844e-504c646f4632'])
        return 1


    # test getting a single item from dspace
    def test_get_item(self):
        dspce = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspce.authenticate()
        print(dspce.get_item('2e003b53-da42-45a9-9172-c8f1cfeb2ece'))
        return 1

    # test getting all items from a collection
    def test_get_items(self):
        a = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        a.authenticate()
        #a.get_communities()
        #a.get_collections()
        #a.get_bitstreams()
        #a.get_handle(handle = '123456789/3')
        items = a.get_items(cid='59c66749-1ca0-40ee-844e-504c646f4632', debug=False)
        print(items)
        a.logout()
        return 1

    def test_delete_items(self):
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        dspc.empty_collection('59c66749-1ca0-40ee-844e-504c646f4632')
        res_size = len(dspc.get_items(cid='59c66749-1ca0-40ee-844e-504c646f4632'))
        if res_size <= 4:
            return 1
        else:
            print('FAILED: test_delete_items(), ', res_size, 'items remain')
            return 0

    def test_delete_item(self):
        print("TESTING DELETE ITEM")
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        items = dspc.get_items(cid='59c66749-1ca0-40ee-844e-504c646f4632')
        print('available items:\n\t', items)
        selection = input('enter UUID to delete:')
        dspc.delete_item(item_id=selection)
        return 1

    def test_get_metadata(self):
        dspc = DSpace(username='sheneman@uidaho.edu', passwd='foo')
        dspc.authenticate()
        meta = dspc.get_item_metadata('469b2a14-5532-4d36-8b8c-fded91da195a')
        if meta != None:
            print('Metadata\n\t', meta)
            return 1

        else:
            print('FAILED: test_get_metadata()')
            return 0

# test framework for the DOIResolver program
class TestDOIResolver(unittest.TestCase):

    def test_all(self):
        points = self.test_resolve_meta() + self.test_authorss_tostr()

        print('TEST RESULTS:\n\tscore = ', points, '/2', sep='')

    def test_get_date(self):
        dres = DOIResolver()
        #dres.get_date({'date-parts': [[2017]]})
        dres.get_date({'indexed': {'date-parts': [[2020, 6, 9]], 'date-time': '2020-06-09T19:21:54Z', 'timestamp': 1591730514246}, 'reference-count': 0, 'publisher': 'Frontiers Media SA', 'content-domain': {'domain': [], 'crossmark-restriction': False}, 'DOI': '10.3389/fcimb.2019.00477.s003', 'type': 'component', 'created': {'date-parts': [[2020, 1, 21]], 'date-time': '2020-01-21T05:22:03Z', 'timestamp': 1579584123000}, 'source': 'Crossref', 'is-referenced-by-count': 0, 'title': 'Table_2.XLS', 'prefix': '10.3389', 'member': '1965', 'container-title': [], 'original-title': [], 'deposited': {'date-parts': [[2020, 1, 21]], 'date-time': '2020-01-21T05:22:04Z', 'timestamp': 1579584124000}, 'score': 1.0, 'subtitle': [], 'short-title': [], 'issued': {'date-parts': [[None]]}, 'references-count': 0, 'URL': 'http://dx.doi.org/10.3389/fcimb.2019.00477.s003', 'relation': {}})

    # make sure the doi resolver is outputting real data
    def test_resolve_meta(self):
        doi = '10.1109/5.771073'

        dres = DOIResolver()
        meta = dres.get_meta(doi)

        print('meta:', meta)

        if meta != None:
            return 1

        else:
            return 0

    def test_authorss_tostr(self):
        doi = '10.1109/5.771073'

        dres = DOIResolver()
        meta = dres.get_meta(doi)

        authorss = dres.authorss_to_str(meta['authors'])
        print('authorss:', authorss)

        if authorss != '':
            return 1

        return 0

    def test_get_meta_bulk(self):
        doiR = DOIResolver()
        all_keys = []

        with open("C:/Users/deepg/Documents/TickBase/code/test_dois.csv", 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                temp_row = row[0].replace('[\'', '')
                temp_row = temp_row.replace('\']', '')
                print(temp_row)

                meta = doiR.get_meta(doi=temp_row)
                temp_keys = meta.keys()
                for key in temp_keys:
                    if key not in all_keys:
                        print('some doi meta missing', key)
                        all_keys.append(key)

                print('\n\t\t', meta)

        print('ALL KEYS FOUND:\n\t', all_keys)

TestDSpace()
#print(TestDOIResolver().test_get_date())
#print(TestDSpace().test_crawler_integration())
#print(TestDOIResolver().test_all())
'''
a.create_community(id=000, name='Test Community', handle='1234/1', link='/rest/communities/000',
                    expand=["parentCommunity","collections","subCommunities","logo","all"], logo=None, parentCommunity=None,
                    copyrightText='', introductoryText='', shortDesc='', sidebarText='', countItems=0, subCommunities=[], collections=[])
'''


#r = requests.get('http://dspace-dev.nkn.uidaho.edu:8080/rC:\Users\deepg\Documents\TickBase\searchesst/collections/123456789/2')

#print(r.json())
#a.get_status()
