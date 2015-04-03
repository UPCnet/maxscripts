"""MAX Documentation generator

Usage:
    max.docgen <maxserver> <username> [options]

Options:

    -o <output>, --output <output>            File where to generate documentation [default: max.md]
"""

from docopt import docopt
from maxclient.wsgi import MaxClient
import os

TITLE_BLOCK = """# MAX API Documentation

"""

GROUP_BLOCK = """# Group {name}
{description}

"""

RESOURCE_BLOCK = """## {route_name} [{route_url}]

"""

METHOD_BLOCK = """### {description} [{method}]
{documentation}

"""


def generate_aglio_md(endpoints, filename):
    """
    """
    output = ""
    output += TITLE_BLOCK

    for category in endpoints:
        category.setdefault('description', '')
        output += GROUP_BLOCK.format(**category)

        for resource in category['resources']:
            resource['route_url'] = resource['route_url']
            output += RESOURCE_BLOCK.format(**resource)

            for method, params in resource['methods'].items():
                params.setdefault('documentation', 'Please document me!')
                params.setdefault('description', 'Please describe me!')
                output += METHOD_BLOCK.format(method=method, **params)

    open(filename, 'w').write(output)


def main():
    arguments = docopt(__doc__, version='MAX Documentation generator 1.0')
    maxserver = arguments.get('<maxserver>')

    client = MaxClient(maxserver)
    max_user = arguments.get('<username>')
    client.setActor(max_user)
    client.login(username=max_user)

    doc_file = os.path.realpath(arguments.get('--output'))
    endpoints = client.info.api.get(qs=dict(by_category=True))

    generate_aglio_md(endpoints, doc_file)


if __name__ == '__main__':
    main()
