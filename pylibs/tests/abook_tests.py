import os
from os import path
import sys
import unittest

abook_dir = path.join(path.dirname(__file__), os.pardir)
testdata_dir = path.join(abook_dir, os.pardir, 'testdata')
test_config = path.join(testdata_dir, 'notmuch-config')
test_config_noignore = path.join(testdata_dir, 'notmuch-config-noignore')

testdb = 'testdb.sqlite'
testignore = 'testignore'

sys.path.append(abook_dir)
import notmuch_abook as abook


class TestNotmuchConfig(unittest.TestCase):

    # these two tests also confirm that our global variables have the correct
    # values in
    def test_config_gets_backend(self):
        config = abook.NotMuchConfig(test_config)
        self.assertEqual('sqlite', config.get('addressbook', 'backend'))
        self.assertEqual(testdb, config.get('addressbook', 'path'))

    def test_config_gets_ignorefile_if_present(self):
        config = abook.NotMuchConfig(test_config)
        self.assertEqual(testignore, config.get('addressbook', 'ignorefile'))

    def test_config_sets_ignorefile_to_None_if_not_present(self):
        config = abook.NotMuchConfig(test_config_noignore)
        self.assertIsNone(config.get('addressbook', 'ignorefile'))


class TestAbookDatabase(unittest.TestCase):

    def setUp(self):
        self.config = abook.NotMuchConfig(test_config)
        self.db = abook.SQLiteStorage(self.config)

    def tearDown(self):
        if path.exists(testdb):
            os.remove(testdb)

    def createFakeDb(self):
        with open(testdb, 'w') as f:
            f.write('nonsense')

    def test_path_set_correctly(self):
        self.assertEqual(testdb, self.db._SQLiteStorage__path)

    def test_connect_raises_IOError_when_db_not_present(self):
        # this is checking our assumption
        self.assertFalse(path.exists(testdb))
        # this is checking the code
        self.assertRaises(IOError, self.db.connect)

    def test_create_raises_IOError_when_db_is_present(self):
        self.createFakeDb()
        self.assertRaises(IOError, self.db.create)
