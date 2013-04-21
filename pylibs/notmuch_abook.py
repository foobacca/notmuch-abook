#!/usr/bin/env python2.6

## Filename: notmuch_addresses.py
## Copyright (C) 2010-11 Jesse Rosenthal
## Author: Jesse Rosenthal <jrosenthal@jhu.edu>

## This file is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; either version 2, or (at your
## option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## NOTE: This script requires the notmuch python bindings.

import argparse
import notmuch
import sqlite3
import ConfigParser
import optparse
import email.parser
import email.utils
import os.path
import time
import sys
import re


class Printer(object):
    def __init__(self, quiet, verbose, debug):
        if quiet and (verbose or debug):
            raise Exception('Cannot combine --quiet with either --verbose or --debug')
        self.quiet = quiet
        self.verbose = verbose or debug
        self.debug = debug

    def error(self, msg):
        print >> sys.stderr, msg

    def exception(self, exc):
        if self.verbose:
            import traceback
            traceback.print_exc()
        else:
            self.error(exc)

    def normal(self, msg):
        if not self.quiet:
            print msg

    def verbose(self, msg):
        if self.verbose:
            print msg

    def debug(self, msg):
        if self.debug:
            print msg


class NotMuchConfig(object):
    def __init__(self, nm_path):
        self.path = os.path.expanduser(nm_path)
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.path)

    def get(self, section, key):
        return self.config.get(section, key)


class MailParser(object):
    def __init__(self, printer):
        self.addresses = dict()
        self.printer = printer

    def parse_mail(self, m):
        """
        function used to extract headers from a email.message or notmuch.message email object
        yields address tuples
        """
        addrs = []
        if isinstance(m, email.message.Message):
            get_header = m.get
        else:
            get_header = m.get_header
        for h in ('to', 'from', 'cc', 'bcc'):
            v = get_header(h)
            if v > '':
                addrs.append(v)
        for addr in email.utils.getaddresses(addrs):
            if addr[1] != "" and not addr[1] in self.addresses.keys():
                addr = (addr[0].strip("'").strip('"').strip(" "), addr[1])
                self.addresses[addr[1]] = addr[0]
                for w in addr[0].split(" ") + [addr[1]]:
                    yield addr

class NotmuchAddressGetter(object):
    """Get all addresses from notmuch, based on information information from
    the user's $HOME/.notmuch-config file.
    """

    def __init__(self, config, printer):
        """
        """
        self.db_path = config.get("database", "path")
        self._mp = MailParser(printer)

    def _get_all_messages(self):
        notmuch_db = notmuch.Database(self.db_path)
        query = notmuch.Query(notmuch_db, "not tag:junk AND not folder:drafts AND not tag:deleted")
        return query.search_messages()

    def generate(self):
        msgs = self._get_all_messages()
        for m in msgs:
            for addr in self._mp.parse_mail(m):
                yield addr


class SQLiteStorage():
    """SQL Storage backend"""
    def __init__(self, config, printer):
        self.__path = config.get("addressbook", "path")
        self.printer = printer

    def connect(self):
        """
        creates a new connection to the database and returns a cursor
        throws an error if the database does not exists
        """
        if not os.path.exists(self.__path):
            raise IOError("Database '%s' does not exists" % (self.__path,))
        return sqlite3.connect(self.__path, isolation_level="DEFERRED")

    def create(self):
        """
        create a new database
        """
        if os.path.exists(self.__path):
            raise IOError("Can't create database at '%s'. File exists." % (self.__path,))
        else:
            with sqlite3.connect(self.__path) as c:
                cur = c.cursor()
                cur.execute("CREATE VIRTUAL TABLE AddressBook USING fts4(Name, Address)")
                cur.execute("CREATE VIEW AddressBookView AS SELECT * FROM addressbook")
                cur.executescript("CREATE TRIGGER insert_into_ab INSTEAD OF INSERT ON AddressBookView "+
                                  "BEGIN"+
                                  " SELECT RAISE(ABORT, 'column name is not unique')"+
                                  "   FROM addressbook"+
                                  "  WHERE name = new.name"+
                                  "     OR address = new.address;"+
                                  " INSERT INTO addressbook VALUES(new.name, new.address);"+
                                  "END;")

    def init(self, gen):
        """
        populates the database with all addresses from address book
        """
        n = 0
        with self.connect() as cur:
            cur.execute("PRAGMA synchronous = OFF")
            for elt in gen():
                try:
                    cur.execute("INSERT INTO AddressBookView VALUES(?,?)", elt)
                    n += 1
                except sqlite3.IntegrityError:
                    pass
            cur.commit()
        return n

    def update(self, addr):
        """
        updates the database with a new mail address tuple
        """
        try:
            with self.connect() as c:
                cur = c.cursor()
                cur.execute("INSERT INTO AddressBookView VALUES(?,?)", addr)
                return True
        except sqlite3.IntegrityError:
            return False

    def lookup(self, match):
        """
        lookup an address from the given match in database
        """
        with self.connect() as c:
            cur = c.cursor()
            for res in cur.execute(
                    "SELECT * FROM AddressBook WHERE AddressBook MATCH '%s'"
                    % match).fetchall():
                yield res


def run():
    parser = argparse.ArgumentParser(prog=sys.argv[0], description="""Notmuch Addressbook utility""")
    parser.add_argument("-q", "--quiet",
                        dest="quiet",
                        action="store_true",
                        help="Only show errors (not valid with lookup)")
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        help="Show full stacktraces on error")
    parser.add_argument("-d", "--debug",
                        dest="debug",
                        action="store_true",
                        help="Show lots of output")
    parser.add_argument("-c", "--config",
                        dest="config",
                        action="store",
                        help="Path to notmuch configuration file",
                        default="~/.notmuch-config")

    subparsers = parser.add_subparsers(title="Commands", help="Command description", description="")
    create_cmd = subparsers.add_parser("create", help="Create a new database.")
    update_cmd = subparsers.add_parser("update", help="Update the database with a new mail (on stdin).")
    lookup_cmd = subparsers.add_parser("lookup", help="Lookup an address in the database.")
    lookup_cmd.add_argument("-a", "--abook-output",
                            dest="abook_output",
                            action="store_true",
                            help="Output addresses in the class abook format.")
    lookup_cmd.add_argument(dest="match", help="Match string to be looked up.")

    def create_act(args, printer, db, cf):
        db.create()
        nm_mailgetter = NotmuchAddressGetter(cf, printer)
        n = db.init(nm_mailgetter.generate)
        printer.normal("added %d addresses" % n)

    def update_act(args, printer, db, cf):
        n = 0
        m = email.message_from_file(sys.stdin)
        for addr in MailParser(printer).parse_mail(m):
            if db.update(addr):
                n += 1
        printer.normal("added %d addresses" % n)

    def lookup_act(args, printer, db, cf):
        if printer.quiet:
            raise Exception('Cannot use --quiet with lookup')
        for addr in db.lookup(args.match):
            if args.abook_output:
                printer.normal(addr[1] + "\t" + addr[0])
            else:
                if addr[0] != "":
                    printer.normal(addr[0]+" <"+addr[1]+">")
                else:
                    printer.normal(addr[1])

    create_cmd.set_defaults(func=create_act)
    update_cmd.set_defaults(func=update_act)
    lookup_cmd.set_defaults(func=lookup_act)

    args = parser.parse_args()
    try:
        printer = Printer(args.quiet, args.verbose, args.debug)
        cf = NotMuchConfig(os.path.expanduser(args.config))
        if cf.get("addressbook", "backend") == "sqlite3":
            db = SQLiteStorage(cf, printer)
        else:
            printer.error("Database backend '%s' is not implemented." %
                          cf.get("addressbook", "backend"))
        args.func(args, printer, db, cf)
    except Exception as exc:
        printer.exception(exc)

if __name__ == '__main__':
    run()
