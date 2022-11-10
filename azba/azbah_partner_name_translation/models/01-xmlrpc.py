# from googletrans import Translator
# translator = Translator()
# t=translator.translate('مركز عمار  للتسويق')
# print (t)
from googletrans import Translator

translator = Translator()

import xmlrpc.client
import csv
import time

url = "http://azbah.online:8015"
db = "azbah2"
username = "admin"
password = "z"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
start_time = time.perf_counter()

names = models.execute_kw(db, uid, password, 'res.partner',
                             'search_read', [],{'fields': ['name']})
for name in names:
    english_name=translator.translate(name['name']).text

    models.execute_kw(db, uid, password, 'res.partner', 'write', [name['id'], {'english_name': english_name}])
    print (name['id'],name['name'],english_name )

# translated = translator.translate('مركز عمار  للتسويق')
#
# print(translated.text)
'''

import xmlrpc.client
import csv
import time

url = "https://najran.demo.ejadtech.sa"
db = "test"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
start_time = time.perf_counter()

forum_id = models.execute_kw(db, uid, password, 'forum.forum',
                             'search_read', [[['type', '=', 'projects'],
                                              ['id', '=', 10]]],{'fields': ['name']})
for i in forum_id:
    print (i)


# 'domain': [[['type', '=', 'projects'], ['id', '=', 10]]]
# 'fields': ['name']
#
# 	'model': 'forum.forum'
#       'method': 'search_read',
#       'args': [],
#       'kwargs': {        'context': {'bin_size': true},
#         'domain': []
#         'fields': ['id', 'name', 'mode', 'description']
#         'limit': 300,
'''