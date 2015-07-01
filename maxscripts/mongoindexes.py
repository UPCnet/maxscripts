"""MAX Mongodb index initializer

Creates, modifies and cleans indexes on mongodb based on static definition

Usage:
    max.mongoindexes [options]

Options:

    -c <maxini>, --config <maxini>            INI file with max configuration [default: config/max.ini]
    -i <indexes>, --indexes <indexes>         File with index definitions [default: config/mongodb.indexes]
    -d <database>, --database <database>        Alternate database name other than the one in max.ini
"""

import ConfigParser
from docopt import docopt
import sys
from maxutils import mongodb
import re
from pymongo import ASCENDING
from pymongo import DESCENDING


def asbool(value):
    return not str(value).lower() in ['0', 'false', 'none', '']


class CreateMongoIndexes(object):  # pragma: no cover

    def __init__(self, settings_file, indexes_file, database, quiet=False):
        self.quiet = quiet
        self.indexes_file = indexes_file

        self.maxconfig = ConfigParser.ConfigParser()
        self.maxconfig.read(settings_file)

        self.db_name = self.maxconfig.get('app:main', 'mongodb.db_name')
        if database is not None:
            self.db_name = database

        self.cluster = asbool(self.maxconfig.get('app:main', 'mongodb.cluster'))
        self.standaloneserver = self.maxconfig.get('app:main', 'mongodb.url')
        self.clustermembers = self.maxconfig.get('app:main', 'mongodb.hosts')
        self.replicaset = self.maxconfig.get('app:main', 'mongodb.replica_set')

        self.mongo_auth = asbool(self.maxconfig.get('app:main', 'mongodb.auth'))
        self.mongo_authdb = self.maxconfig.get('app:main', 'mongodb.authdb')
        self.mongo_username = self.maxconfig.get('app:main', 'mongodb.username')
        self.mongo_password = self.maxconfig.get('app:main', 'mongodb.password')

    def run(self):

        # Mongodb connection initialization
        cluster_enabled = self.cluster
        auth_enabled = self.mongo_auth
        mongodb_uri = self.clustermembers if cluster_enabled else self.standaloneserver

        conn = mongodb.get_connection(
            mongodb_uri,
            use_greenlets=True,
            cluster=self.replicaset if cluster_enabled else None)

        # Log the kind of connection we're making
        if self.cluster:
            print 'Connecting to database {} @ cluster "{}" ...'.format(self.db_name, self.replicaset)
        else:
            print 'Connecting to database {} @ {} ...'.format(self.db_name, self.standaloneserver)

        db = mongodb.get_database(
            conn,
            self.db_name,
            username=self.mongo_username if auth_enabled else None,
            password=self.mongo_password if auth_enabled else None,
            authdb=self.mongo_authdb if auth_enabled else None)

        indexes_file = open(self.indexes_file).read()
        clean = re.sub(r'(?:^|\n)#+[^\n]*', r'', indexes_file)
        count = 0
        indexes = re.findall(r'(\w+):([^\s:]+)(?::([^\s]+))?', clean, re.DOTALL)

        # Group indexes by collection
        indexes_by_collection = {}
        for collection_name, index_def, options in indexes:
            indexes_by_collection.setdefault(collection_name, [])
            indexes_by_collection[collection_name].append((index_def, options))

        def query_options(options_string):
            query_options = {
            }
            if 's' in options:
                query_options['sparse'] = True
            return query_options

        def get_direction(sort_dir):
            return DESCENDING if sort_dir == '-' else ASCENDING

        def check_index(current, key, options):
            found = None

            # Look if there's any index with the same key
            for index_name, index_params in current.items():
                if index_params['key'] == key:
                    found = index_name

            # if the index exists, check that the options are the same
            if found is not None:
                sameoptions = True
                for name, value in options.items():
                    if name in current[found]:
                        sameoptions = sameoptions and current[found][name] == value
                    else:
                        sameoptions = False
                        break

                if sameoptions:
                    current.pop(found)
                    return 'OK', found
                else:
                    current.pop(found)
                    return 'CHANGED', found
            else:
                return 'MISSING', None

        for collection_name, col_indexes in indexes_by_collection.items():
            collection = db[collection_name]
            current_indexes = collection.index_information()

            for index_def, options in col_indexes:
                index_options = query_options(options)
                index_keys = [(key, get_direction(sort_dir)) for sort_dir, key in re.findall(r'(-?)([^,]+)', index_def)]
                index_status, index_name = check_index(current_indexes, index_keys, index_options)
                # sys.stdout.write('. ')
                # sys.stdout.flush()
                if index_status == 'CHANGED':
                    collection.drop_index(index_name)
                    print '-> Detected change in index "{}". Deleting'

                if index_status in ['CHANGED', 'MISSING']:
                    print '-> Creating index from keys: ', index_def, index_options if index_options else ''
                    collection.create_index(index_keys, **index_options)

                if index_status == 'OK':
                    print 'Index already exists: ', index_name

            for index, params in current_indexes.items():
                if params['key'][0][0] not in ['_id']:
                    print '-> Deleting unknown index "{}"'.format(index)
                    collection.drop_index(index)
        if count:
            print "\nAdded {} indexes to database '{}'".format(count, self.db_name)


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    arguments = docopt(__doc__, version='MAX Database initialized')
    maxini_file = arguments.get('--config')
    indexes_file = arguments.get('--indexes')
    database = arguments.get('--database', None)

    command = CreateMongoIndexes(maxini_file, indexes_file, database)
    return command.run()
