'''
    @author Garrett Wells
    @date   12/31/2021
'''



# libraries external to this project
from bs4 import BeautifulSoup
from collections import defaultdict
import requests
import csv
import json
import datetime
import pprint
import time

# libraries written for this project
# interfaces
from gscholar_interface import GScholar
from mendeley_interface import IMendeley
from mendeleydata_interface import IMendeley_Data
from figshare_interface import IFigshare
from datadryad_interface import IDataDryad
#from mendeley import Mendeley
from knb_interface import IKNB
from springer_interface import ISpringer
from neon_interface import INeon
from pubmed_interface import IPubMed
from lter_interface import ILTER
    # data structures, data verification, and external object interfaces
from briefcase import Briefcase
from doichecker import doichecker
from dspace7 import DSpace


'''
    Implements the object for running keyword queries on data repositories using the unified interface described in portal_interface.py. 
'''
class Crawler:
    dchecker = doichecker()

    # input:
    #  1. path to a csv file filled with search keywords
    #  2. an interface for the repository that provides the base functionality for querying
    def __init__(self, repository_interface, csv_path='keys.csv'):
        self.interface = repository_interface
        self.url_briefcase = Briefcase()
        if csv_path != '':
            with open(csv_path, newline='', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                res = list(reader)
            self.search_keys = res
            print(res)


    # returns a tuple containing a dictionary of sources found by search,
    def search(self, keywords=[[]]):
        # create new briefcase for storing data as member variable
        self.url_briefcase = Briefcase()
        final_list = [] # list of all DOIs collected in this search

        # run query for each keyword passed in
        rows = len(keywords) # get num of rows in table
        for row in keywords:
            cols = len(row) # get num search terms in this row
            for key in row:
                if key == '':
                    print('skipping empty key')
                    continue

                print('\nSEARCH TARGET =', key)
                t0 = time.time()
                r = self.interface.query(key)
                print('... completed query in ', time.time() - t0, ' seconds\n')
                # expect results to be an array of document type objects
                if r is None:
                    print('ERROR: query of ', self.interface.get_tag(), ' failed, probably a server error')
                    return # if query of source failed...
                # check each document DOI retrieved by query for duplicates
                for doc in r:
                    if not self.dchecker.duplicate(doc.doi): 
                        final_list.append(doc)
                    else:
                        continue

                # store results in briefcase for export later
                t0 = time.time() # save operation start time
                self.build_table(search_result=r) # build table of metadata/html content
                print('... built table in ', time.time() - t0, ' seconds\n') # print timing info for debug

                # test writing results to excel table
                #self.export_to_excel(key)

                t0 = time.time() # save operation start time
                self.export_to_csv(key)
                print('... exported to csv in ', time.time() - t0, ' seconds\n') # print timing info for debug

                # if we are searching multiple terms, pause 2 min to prevent locking server
                if rows > 1 or cols > 1:
                    time.sleep(120.0)

        # FINAL CLEANUP
        # save collected DOIs from fast access to file for later
        self.dchecker.save_fa_file()
        print('\tSUMMARY DICTIONARY:', final_list)


    # search all keys passed to the program
    def search_all(self):
        self.search(self.search_keys)


    # retrieve all links from search results in a briefcase object
    def build_table(self, search_result):
        print('BUILDING TABLE')
        # most interfaces return list of document objects
        type, output = self.interface.get_content(search_result)

        # check format of search output and process results
        # list = Document object from briefcase.py
        if type == 'json':
            print(output)

        elif type == 'html':
            bs = BeautifulSoup(output, 'html.parser')
            for lnkd_url in self.get_linked_urls(search_result.url, search_result.text):
                if lnkd_url != 'javascript:void(0)' and lnkd_url != search_result.url:
                    # store url in data structure
                    self.url_briefcase.add({'URL':lnkd_url, 'publication_date': '{:%d-%m-%Y}'.format(datetime.datetime.today())})

        elif type == 'list' and search_result is not None:
            for item in search_result:
                self.url_briefcase.add(item.data)


    # parse an html document for all hyper links
    # TODO: currently don't think this function is used as no query results are currently returned in HTML
    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        num_links = 0
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                continue

            elif path != 'javascript:void(0)':
                num_links = num_links + 1
            yield path

        print('Related Links Found', num_links)


    # export results for a specific query to a spreadsheet or csv
    # tags the file with keyword, date, and source
    def export_to_excel(self, keyword=''):
        print('\n\nexporting excel')
        if not self.url_briefcase.is_empty():
            if keyword == '':
                name = 'data/{}_{}_{}'.format(self.interface.get_tag(), self.interface.get_resultType(), '{:%d-%m-%Y}'.format(datetime.datetime.today()))
            else:
                name = 'data/{}_{}_{}_{}'.format(self.interface.get_tag(), self.interface.get_resultType(), keyword, '{:%d-%m-%Y}'.format(datetime.datetime.today()))

            name = name + '.xlsx'
            print(name)
            try:
                self.url_briefcase.to_excel(name)
            except PermissionError:
                print('ERROR: can\'t save to specified path, close excel notebook currently displaying %s first' %name)

        else:
            print('database empty, error')


    # send metadata in briefcase data structure to a csv file
    def export_to_csv(self, keyword=''):
        print('\n\nexporting csv')
        if not self.url_briefcase.is_empty():
            if keyword == '':
                name = '../data_dump/{}_{}_{}'.format(self.interface.get_tag(), self.interface.get_resultType(), '{:%d-%m-%Y}'.format(datetime.datetime.today()))
            else:
                name = '../data_dump/{}_{}_{}_{}'.format(self.interface.get_tag(), self.interface.get_resultType(), keyword, '{:%d-%m-%Y}'.format(datetime.datetime.today()))

            name = name + '.csv'
            print(name)
            try:
                self.url_briefcase.to_csv(name)
            except PermissionError:
                print('ERROR: can\'t save to specified path, close excel/notepad notebook currently displaying %s first' %name)

        else:
            print('database empty, error')


    # Export metadata to a DuraSpace simple archive formatted as a dublin core XML
    # TODO: this submission method does not currently work
    def export_to_batch(self, keyword=''):
        print('\n\nexporting batch')
        if not self.url_briefcase.is_empty():
            #meta_file_name = '{}_{}_{}_{}'.format(self.interface.get_tag(), self.interface.get_resultType(), keyword, '{:%d-%m-%Y}'.format(datetime.datetime.today()))
            batch_name = self.interface.get_tag() + '_' + keyword

            try:
                self.url_briefcase.to_batch(batch_name)
            except PermissionError:
                print('ERROR: can\'t save to specified path, close excel/notepad notebook currently displaying %s first' %name)


    # Export metadata to DuraSpace archive
    # preferred submission method to any DSpace collection archive
    def export_to_dspace(self, cid='', uname='', passwd='', base_url=''):
        if not self.url_briefcase.is_empty():
            if uname == '' or passwd == '':
                raise Exception('user name, password empty in crawler.py export_to_dspace()')

            # open connection with dspace
            dspc = DSpace(username=uname, passwd=passwd)
            dspc.authenticate()

            # check connection status and throw error if unsuccessful
            if not dspc.get_status():
                raise Exception('error in connection')
            else:
                print("AUTHENTICATION CONFIRMED")
                self.url_briefcase.export_to_dspace(cid=cid, dspace=dspc)
                # close connection with dspace
                dspc.logout()


    # add one dictionary to another
    # TODO: written for use with SQLAlchemy and SQL database creation, consider removing as not currently used
    def combine_dictionaries(self, dict_a={}, dict_b={}):
        for key in dict_b.keys():
            if key in dict_a.keys():
                dict_a[key].append(dict_b[key])
            #else:
                #print(key, ' not found in first dictionary')

        print('\t\tFINAL DICT:', dict_a)
        return dict_a


    # export a dictionary of data to a SQL database
    # TODO: consider removing as is unused
    def export_to_db(self, user='', table_name='', database='', password='', server='', data_dict={}):
        data_framed = panda.DataFrame(data_dict) # convert dict to frame
        print(data_framed.to_string())
        #engine = create_engine('mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user='root', password='GW091799', server='localhost', database=self.database_name), echo=False)
        engine = create_engine('mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user=user, password=password, server=server, database=database), echo=False)
        data_framed.to_sql(table_name, con=engine, index=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)


'''

    Implements tests for the various interfaces that have been developed to search databases.

    Currently tests are limited to verifying that the given interface can perform a full, uninterrupted series of queries
    using the search keys provided in the CSV

'''
class CrawlTester:

    # default path to test CSV
    test_csv_path = '../searches/test_search.csv' 

    # test google scholar interface with the crawler
    def test_GScholar(self):
        gs = GScholar()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    # test the mendeley interface with the crawler
    def test_Mendeley(self):
        gs = IMendeley()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    # test the mendeley data portal interface with the crawler
    def test_MendeleyData(self):
        gs = IMendeley_Data()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_Figshare(self):
        gs = IFigshare()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_DataDryad(self):
        gs = IDataDryad()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_KNB(self):
        gs = IKNB()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_SpringerNature(self):
        gs = ISpringer()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_Neon(self):
        gs = INeon()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_PubMed(self):
        gs = IPubMed()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    def test_LTER(self):
        gs = ILTER()
        a = Crawler(repository_interface=gs, csv_path=test_csv_path)
        a.search_all()

    # test briefcase
    def test_briefcase(self):
        folder = Briefcase()
        for i in range(20):
            folder.add({'URL' : 'line'.format(i)})

        folder.print()
