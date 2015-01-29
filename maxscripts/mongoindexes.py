
import argparse
import ConfigParser

import sys
from maxutils import mongodb
import re


def asbool(value):
    return not str(value).lower() in ['0', 'false', 'none', '']


class CreateMongoIndexes(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.maxconfig = ConfigParser.ConfigParser()
        self.maxconfig.read(self.options.maxconfigfile)

        self.common = ConfigParser.ConfigParser()
        self.common.read(self.options.commonfile)

        self.db_name = self.maxconfig.get('app:main', 'mongodb.db_name')

        self.cluster = asbool(self.common.get('mongodb', 'cluster'))
        self.standaloneserver = self.common.get('mongodb', 'url')
        self.clustermembers = self.common.get('mongodb', 'hosts')
        self.replicaset = self.common.get('mongodb', 'replica_set')

        self.mongo_auth = asbool(self.common.get('mongodb', 'auth'))
        self.mongo_authdb = self.common.get('mongodb', 'authdb')
        self.mongo_username = self.common.get('mongodb', 'username')
        self.mongo_password = self.common.get('mongodb', 'password')

    def run(self):

        # Mongodb connection initialization
        cluster_enabled = self.cluster
        auth_enabled = self.mongo_auth
        mongodb_uri = self.clustermembers if cluster_enabled else self.standaloneserver

        conn = mongodb.get_connection(
            mongodb_uri,
            use_greenlets=True,
            cluster=self.replica_set if cluster_enabled else None)

        # Log the kinf of connection we're making
        if self.cluster:
            print 'Connecting to database @ cluster "{}" ...'.format(self.replica_set)
        else:
            print 'Connecting to database @ {} ...'.format(self.standaloneserver)

        db = mongodb.get_database(
            conn,
            self.db_name,
            username=self.mongo_username if auth_enabled else None,
            password=self.mongo_password if auth_enabled else None,
            authdb=self.mongo_authdb if auth_enabled else None)

        indexes_file = open(self.options.indexesfile).read()
        clean = re.sub(r'(?:^|\n)#+[^\n]*', r'', indexes_file)
        count = 0
        indexes = re.findall(r'(\w+):([^\s]+)', clean, re.DOTALL)
        for collection, index_key in indexes:
            sys.stdout.write('. ')
            sys.stdout.flush()
            db[collection].create_index(index_key)
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

    parser.add_argument(
        '-o', '--common',
        dest='commonfile',
        type=str,
        default='config/common.ini',
        help=("Common configuration file"))

    options = parser.parse_args()

    command = CreateMongoIndexes(options)
    return command.run()
