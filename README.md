Notmuch Addressbook manager for vim
===================================

DEPENDENCES
-----------

* notmuch with python bindings

INSTALL
-------

* Standalone install

if you do not want to use the vim script file, you can install the module as follows:

```
python setup.py install
```

or using:

```
pip install notmuch_abook
```

* Vimscript install

Use vundle to install this script, add to your vimrc:

```
Bundle "guyzmo/notmuch-abook"
```

for convenience, you can create a symlink to your bin directory:
```
ln -s $HOME/.vim/bundle/notmuch-abook/pylibs/notmuch_addresses.py ~/bin/notmuch-abook
```

CONFIGURATION
-------------

Open notmuch configuration file (usually $HOME/.notmuch-config) and add:

```
[addressbook]
path=/home/USER/.notmuch-abook.db
backend=sqlite3
ignorefile=/home/USER/.notmuch-abook-ignore
```

where USER is your username (or at any other place).  Note the `ignorefile` line is optional, but
the other two lines are required.

If you use a non-default notmuch configuration file, you can set it in your vimrc with:

```
let g:notmuchconfig = "~/.notmuch-config-custom"
```

In your favorite mail filter program, add a rule such as (for procmail), so all new mail will be parsed:

```
:0 Wh
| python $HOME/.vim/bundle/notmuch-abook/pylibs/notmuch_abook.py update
```

If you can't use procmail (eg if you are using offlineimap) then you could put the following few lines at the start of the [post-new hook](http://notmuchmail.org/manpages/notmuch-hooks-5/) (**before** you remove the new tag).  Also note this is shell syntax, so you'll have to adapt if your hook is in another language.

```
# first update notmuch-abook
for file in $(notmuch search --output=files tag:new) ; do
    cat $file | $HOME/bin/notmuch-abook update
done
```

Note that the name used for a given email address is the name first seen associated with that email address.
Once the email address is in the database the name will not be changed by `update` (or `create`).  You have to
use `changename` (or `export`, edit the exported file and then `import --replace`) to update the name associated
with the email address.

USAGE
-----

For the first time, you shall launch the script as follows to create the addresses database (it takes ~20 seconds for 10000 mails):

```
python $HOME/.vim/bundle/notmuch-abook/pylibs/notmuch_addresses.py create
```

and then, to lookup an address, either you use the vimscript to complete (`<c-x><c-u>`) the name in a header field,
or you can call it from commandline:

```
python $HOME/.vim/bundle/notmuch-abook/pylibs/notmuch_addresses.py lookup Guyz
```

the script will match any word beginning with the pattern in the name and address parts of the entry. There are
options for the output format of the lookup command.  The ordering of the matches is most frequent first - a
count is maintained of the number of time each email address has been seen.

The full usage for the command is:

```
Usage:
  notmuch_abook.py -h
  notmuch_abook.py [-v] [-c CONFIG] create
  notmuch_abook.py [-v] [-c CONFIG] update
  notmuch_abook.py [-v] [-c CONFIG] lookup [ -f FORMAT ] <match>
  notmuch_abook.py [-v] [-c CONFIG] changename <address> <name>
  notmuch_abook.py [-v] [-c CONFIG] delete [-n] <pattern>
  notmuch_abook.py [-v] [-c CONFIG] export [ -f FORMAT ] [ -s SORT ] [<filename>]
  notmuch_abook.py [-v] [-c CONFIG] import [ -f FORMAT ] [ -r ] [<filename>]

Options:
  -h --help                   Show this help message and exit
  -v --verbose                Show full stacktraces on error
  -c CONFIG, --config CONFIG  Path to notmuch configuration file
  -f FORMAT, --format FORMAT  Format for name/address (see below) [default: email]
  -n, --noinput               Don't ask for confirmation
  -s SORT, --sort SORT        Whether to sort by name or address [default: name]
  -r, --replace               If present, then replace the current contents with
                              the imported contents.  If not then merge - add new
                              addresses, and update the name associated with
                              existing addresses.

Commands:

  create               Create a new database.
  update               Update the database with a new email (on stdin).
  lookup <match>       Lookup an address in the database.  The match can be
                       an email address or part of a name.
  changename <address> <name>
                       Change the name associated with an email address.
  delete <pattern>     Delete all entries that match the given pattern - matched
                       against both name and email address.  The matches will be
                       displayed and confirmation will be asked for, unless the
                       --noinput flag is used.
  export [<filename>]  Export database, to filename if given or to stdout if not.
  import [<filename>]  Import into database, from filename if given or from stdin
                       if not.

Valid values for the FORMAT are:

* abook - Give output in abook compatible format so it can be easily parsed
          by other programs.  The format is EMAIL<Tab>NAME
* csv   - Give output as CSV (comma separated values). NAME,EMAIL
* email - Give output in a format that can be used when composing an email.
          So NAME <EMAIL>

The database to use is set in the notmuch config file.
```

IGNORING SOME EMAIL ADDRESSES
-----------------------------

You may want to ignore some email addresses when adding them (either through `create` or `update` - say you
get lots of emails from some automated systems and you never want to send email to the from address.  In that
case you can set up an ignore file, and put the path to it in the config file.  You should put one pattern per
line into that file.  For a plain match against any part of the email address you can just put the text on
that line, eg `logwatch@` or `no-reply`.  You can also use Python regular expressions - marked by beginning
and ending the line with `/`.  So to ignore email sent to any subdomain of your company, you could use
`/@[-\.\w]+\.example.com/`

LICENSE
-------

(c)2013, Bernard Guyzmo Pratz, guyzmo at m0g dot net

Even though it is a WTFPL license, if you do improve that code, it's great, but if you
don't tell me about that, you're just a moron. And if you like that code, you have the
right to buy me a beer, thank me, or [flattr](http://flattr.com/profile/guyzmo)/[gittip](http://gittip.com/guyzmo) me.

```
DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
Version 2, December 2004 

Copyright (C) 2004 Sam Hocevar <sam@hocevar.net> 

Everyone is permitted to copy and distribute verbatim or modified 
copies of this license document, and changing it is allowed as long 
as the name is changed. 

DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION 

0. You just DO WHAT THE FUCK YOU WANT TO.
```
