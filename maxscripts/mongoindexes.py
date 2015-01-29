
import argparse
import ConfigParser

import sys
import pymongo
import re


def as_bool(value):
    return not str(value).lower() in ['0', 'false', 'none', '']


class CreateMongoIndexes(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.maxconfig = ConfigParser.ConfigParser()
        self.maxconfig.read(self.options.maxconfigfile)

        try:
            self.cluster = as_bool(self.maxconfig.get('app:main', 'mongodb.cluster').capitalize())
            self.standaloneserver = self.maxconfig.get('app:main', 'mongodb.url')
            self.hosts = self.maxconfig.get('app:main', 'mongodb.hosts')
            self.replica_set = self.maxconfig.get('app:main', 'mongodb.replica_set')
            self.db_name = self.maxconfig.get('app:main', 'mongodb.db_name')

        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):

        # Check if we're connecting to a cluster
        if self.cluster:
            print 'Connecting to database @ cluster "{}" ...'.format(self.replica_set)
            self.connection = pymongo.MongoReplicaSetClient(self.hosts, replicaSet=self.replica_set)

        #Otherwise make a single connection
        else:
            print 'Connecting to database @ {} ...'.format(self.standaloneserver)
            self.connection = pymongo.Connection(self.standaloneserver)

        self.db = self.connection[self.db_name]

        indexes_file = open(self.options.indexesfile).read()
        clean = re.sub(r'(?:^|\n)#+[^\n]*', r'', indexes_file)
        count = 0
        indexes = re.findall(r'(\w+):([^\s]+)', clean, re.DOTALL)
        for collection, index_key in indexes:
            sys.stdout.write('. ')
            sys.stdout.flush()
            self.db[collection].create_index(index_key)
            count += 1
        if count:
            print "\nAdded {} indexes to database '{}'".format(count, self.db_name)


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Initialize Mongodb Indexes."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '-i', '--indexes',
        dest='indexesfile',
        type=str,
        default='config/mongodb.indexes',
        help=("File with indexes definition"))

    parser.add_argument(
        '-c', '--config',
        dest='maxconfigfile',
        type=str,
        default='config/max.ini',
        help=("Max configuration file"))
    options = parser.parse_args()

    command = CreateMongoIndexes(options)
    return command.run()
