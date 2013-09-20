import os
from os import path
import sys
import unittest

abook_dir = path.join(path.dirname(__file__), os.pardir)
testdata_dir = path.join(abook_dir, os.pardir, 'testdata')

sys.path.append(abook_dir)
import notmuch_abook as abook


class TestNotmuchConfig(unittest.TestCase):

    def test_config_gets_backend(self):
        test_config = path.join(testdata_dir, 'notmuch-config')
        config = abook.NotMuchConfig(test_config)
        self.assertEqual('sqlite', config.get('addressbook', 'backend'))

    def test_config_gets_ignorefile_if_present(self):
        test_config = path.join(testdata_dir, 'notmuch-config')
        config = abook.NotMuchConfig(test_config)
        self.assertEqual('testignore', config.get('addressbook', 'ignorefile'))

    def test_config_sets_ignorefile_to_None_if_not_present(self):
        test_config = path.join(testdata_dir, 'notmuch-config-noignore')
        config = abook.NotMuchConfig(test_config)
        self.assertIsNone(config.get('addressbook', 'ignorefile'))


class TestAbookDatabase(unittest.TestCase):
    pass
