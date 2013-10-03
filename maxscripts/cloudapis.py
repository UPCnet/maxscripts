import argparse
import ConfigParser
import sys
import pymongo


class UpdateCloudAPISettings(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.config = ConfigParser.ConfigParser()
        self.config.read(self.options.commonfile)

        self.cloudapis = ConfigParser.ConfigParser()
        self.cloudapis.read(self.options.cloudapisfile)

        try:
            self.consumer_key = self.cloudapis.get('twitter', 'consumer_key')
            self.consumer_secret = self.cloudapis.get('twitter', 'consumer_secret')
            self.access_token = self.cloudapis.get('twitter', 'access_token')
            self.access_token_secret = self.cloudapis.get('twitter', 'access_token_secret')

            self.cluster = self.config.get('mongodb', 'cluster')
            self.standaloneserver = self.config.get('mongodb', 'url')
            self.clustermembers = self.config.get('mongodb', 'hosts')
            self.dbname = self.config.get('mongodb', 'db_name')
            self.replicaset = self.config.get('mongodb', 'replica_set')

        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):
        # Connect to the database
        if not self.cluster in ['true', 'True', '1', 1]:
            db_uri = self.standaloneserver
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.clustermembers
            replica_set = self.replicaset
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        dbs = [self.dbname, 'tests']
        for dbi in dbs:
            db = conn[dbi]

            # Drop any existing settings
            db.drop_collection('cloudapis')

            # Update the records
            twitter = dict(self.cloudapis.items('twitter'))
            record = {'twitter': twitter}
            db.cloudapis.insert(record)

            print('Updated the cloud APIs info in MAX Database "{}""'.format(dbi))

        print("Remember to restart max process!")


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Update Cloud API Settings"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-a', '--cloudapis',
        dest='cloudapisfile',
        type=str,
        default='config/cloudapis.ini',
        help=("Cloudapis configuration file"))
    parser.add_argument(
        '-c', '--config',
        dest='commonfile',
        type=str,
        default='config/common.ini',
        help=("Common configuration file"))
    options = parser.parse_args()
    command = UpdateCloudAPISettings(options, quiet)
    return command.run()
