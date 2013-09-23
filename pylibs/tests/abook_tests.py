import os
from os import path
import sys
import docopt
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


class TestAbookDatabaseNoIgnore(unittest.TestCase):
    a_name = 'a'
    a_address = 'a@a.com'
    a_record = (a_name, a_address)

    long_name = 'name'
    long_address = 'address@address.com'
    long_record = (long_name, long_address)

    def setUp(self):
        self.config = abook.NotMuchConfig(test_config_noignore)
        self.db = abook.SQLiteStorage(self.config)

    def tearDown(self):
        if path.exists(testdb):
            os.remove(testdb)

    def assertNumEntries(self, expected_count):
        with self.db.connect() as c:
            rows = c.execute('SELECT COUNT(*) FROM AddressBook')
            result = rows.fetchall()
            actual_count = result[0][0]
            self.assertEqual(expected_count, actual_count)

    def assertNameEquals(self, address, expected_name):
        with self.db.connect() as c:
            rows = c.execute('SELECT name FROM AddressBook WHERE address = ?', (address,))
            result = rows.fetchall()
            actual_name = result[0][0]
            self.assertEqual(expected_name, actual_name)

    def createFakeDb(self):
        with open(testdb, 'w') as f:
            f.write('nonsense')

    def do_update_a(self):
        self.db.update(self.a_record)

    def do_update_a2(self, replace=False):
        self.db.update(('a2', self.a_address), replace)

    def do_update_b(self):
        self.db.update(('b', 'b@b.com'))

    def do_update_long(self):
        self.db.update(self.long_record)

    def create_with_a_and_b(self):
        self.db.create()
        self.do_update_a()
        self.do_update_b()

    def create_with_name_order_different_to_address(self):
        self.db.create()
        self.db.update(('b', 'a@a.com'))
        self.db.update(('a', 'b@b.com'))

    def create_with_a_b_and_long(self):
        self.create_with_a_and_b()
        self.do_update_long()

    def three_address_generator(self):
        three_address = [
            ('a', 'a@a.com'),
            ('b', 'b@b.com'),
            ('c', 'c@c.com'),
        ]
        for address in three_address:
            yield address

    def three_address_generator_with_duplicates(self):
        three_address = [
            ('a', 'a@a.com'),
            ('b', 'b@b.com'),
            ('c', 'a@a.com'),
        ]
        for address in three_address:
            yield address

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

    def test_connect_works_after_create_is_run(self):
        try:
            self.db.create()
            self.db.connect()
        except Exception as e:
            self.fail('Unexpected exception %s' % e)

    def test_db_empty_after_create(self):
        # if this breaks, it will break many other tests
        self.db.create()
        # assert the database is empty
        self.assertNumEntries(0)

    def test_can_add_name_address_to_empty_db(self):
        self.db.create()
        self.do_update_a()
        self.assertNumEntries(1)
        self.do_update_b()
        self.assertNumEntries(2)

    def test_duplicate_name_does_not_get_added(self):
        self.db.create()
        self.do_update_a()
        self.assertNumEntries(1)
        self.do_update_a()
        self.assertNumEntries(1)
        self.do_update_a2()
        self.assertNumEntries(1)

    def test_new_name_does_not_overwrite_old_name(self):
        self.db.create()
        self.do_update_a()
        self.assertNumEntries(1)
        self.do_update_a2()
        self.assertNumEntries(1)
        self.assertNameEquals(self.a_address, self.a_name)

    def test_duplicate_name_can_replace(self):
        self.db.create()
        self.do_update_a()
        self.assertNumEntries(1)
        self.do_update_a2(replace=True)
        self.assertNumEntries(1)
        self.assertNameEquals(self.a_address, 'a2')

    def test_replace_argument_works_when_not_replacing(self):
        self.db.create()
        self.do_update_a2(replace=True)
        self.assertNumEntries(1)
        self.assertNameEquals(self.a_address, 'a2')

    def test_lookup_a_returns_one_correct_entry(self):
        self.create_with_a_and_b()
        results = list(self.db.lookup('a'))
        self.assertEqual(1, len(results))
        self.assertSequenceEqual(self.a_record, results[0])

    def test_lookup_finds_match_only_in_name_field(self):
        self.create_with_a_b_and_long()
        results = list(self.db.lookup(self.long_name))
        self.assertEqual(1, len(results))
        self.assertSequenceEqual(self.long_record, results[0])

    def test_lookup_finds_match_only_in_address_field(self):
        self.create_with_a_b_and_long()
        results = list(self.db.lookup(self.long_address))
        self.assertEqual(1, len(results))
        self.assertSequenceEqual(self.long_record, results[0])

    def test_lookup_com_returns_two_entries(self):
        self.create_with_a_and_b()
        results = list(self.db.lookup('com'))
        self.assertEqual(2, len(results))

    def test_one_entry_left_after_delete_matches(self):
        self.create_with_a_and_b()
        self.db.delete_matches('a')
        self.assertNumEntries(1)

    def test_delete_matches_doesnt_cause_error_on_no_matches(self):
        self.create_with_a_and_b()
        try:
            self.db.delete_matches('z')
            self.assertNumEntries(2)
        except Exception as e:
            self.fail('Unexpected exception thrown by delete_matches: %s' % e)

    def test_fetchall_fetches_correct_number_of_results(self):
        self.create_with_a_b_and_long()
        self.assertNumEntries(len(list(self.db.fetchall('name'))))

    def test_fetchall_orders_by_name(self):
        self.create_with_name_order_different_to_address()
        results = list(self.db.fetchall('name'))
        self.assertEqual('a', results[0]['name'])
        self.assertEqual('b', results[1]['name'])

    def test_fetchall_orders_by_address(self):
        self.create_with_name_order_different_to_address()
        results = list(self.db.fetchall('address'))
        self.assertEqual('a@a.com', results[0]['address'])
        self.assertEqual('b@b.com', results[1]['address'])

    def test_change_name_changes_name(self):
        self.db.create()
        self.do_update_a()
        self.assertNameEquals(self.a_address, 'a')
        self.db.change_name(self.a_address, 'a2')
        self.assertNameEquals(self.a_address, 'a2')

    def test_delete_db_deletes_an_existing_database(self):
        self.db.create()
        self.db.delete_db()
        self.assertFalse(path.exists(testdb))

    def test_delete_db_does_not_give_error_when_database_doesnt_exist(self):
        self.assertFalse(path.exists(testdb))
        try:
            self.db.delete_db()
        except Exception as e:
            self.fail('Unexpected exception thrown by delete_db: %s' % e)

    def test_init_adds_all_addresses(self):
        self.db.create()
        self.db.init(self.three_address_generator)
        self.assertNumEntries(3)

    def test_init_doesnt_add_duplicate_addresses(self):
        self.db.create()
        self.db.init(self.three_address_generator_with_duplicates)
        self.assertNumEntries(2)
        # also check if only the first name was used
        self.assertNameEquals(self.a_address, self.a_name)

    # TODO: test no name doesn't cause problems


class TestDocOpt(unittest.TestCase):

    def test_docopt_parses_doc_string(self):
        # if the docopt string is badly formatted, we'll get an exception
        # thrown here
        options = docopt.docopt(abook.__doc__, argv=['--help'], help=False)
        self.assertTrue(options['--help'])
