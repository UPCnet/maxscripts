import sys
import os
import re
from prettytable import PrettyTable, ALL

TEMPLATE = """

Estat dels webservices
======================

{}

"""

TABLE_TEMPLATE = """

{}
{}

{}

"""


def parseParams(function_params):
    new_params = {}
    if '=' in function_params:
        params = dict(re.findall(r'([\w_]+)=([\'"\[][\w_\'\", ]+[\'"\]])', function_params))

        for key, value in params.items():
            is_string = re.match(r'u?^[\'\"](.*?)[\'\"]$', value)
            is_list = re.match(r'^(\[.*?\])$', value)
            if is_string:
                newvalue = is_string.groups()[0]
            elif is_list:
                newvalue = eval(is_list.group())
            new_params[key] = newvalue
    return new_params


def addMissingCodeErrors(container, resources, name, prefix=''):
    """
        Found docs or tests for missing implementation WTF
    """
    res = resources[name]
    for real_method in ['HEAD', 'GET', 'POST', 'PUT', 'DELETE']:
        method = 'GET' if real_method == 'HEAD' else real_method
        has_docs = res.get(prefix + 'documentation', {}).get(method, False)
        tested_methods_match = [(testfile, testname, line) for tmethod, testfile, testname, line in res.get(prefix + 'tests', []) if method == tmethod]
        has_test = len(tested_methods_match) > 0
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if (has_docs or has_test) and not has_code:
            message = 'documented' if has_docs else ''
            message += ' and ' if has_docs else ''
            message += 'tested' if has_test else ''
            container.append('  ERROR: {} {} is {} but code not found by parser'.format(real_method, res['route'], message))
            if has_test:
                container.append('    > Referenced in tests:')
                for testfile, testname, line in tested_methods_match:
                    container.append('        - {} at line {} of file {}'.format(testname, line, testfile))


def addUntestedCodeErrors(container, resources, name, prefix=''):
    """
        Has code but no tests found
    """
    found = []
    res = resources[name]
    for method in ['HEAD', 'GET', 'POST', 'PUT', 'DELETE']:
        tested_methods_match = [True for tmethod, testfile, testname, line in res.get(prefix + 'tests', []) if method == tmethod]
        has_test = len(tested_methods_match) > 0
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if has_code and not has_test:
            found.append(prefix + method)
    if found:
        container.append('  {} ({})'.format(res['route'], ', '.join(found)))


def addUndocumentedCodeErrors(container, resources, name, prefix=''):
    """
        Has code but no docs found
    """
    found = []
    res = resources[name]
    for method in ['GET', 'POST', 'PUT', 'DELETE']:
        has_docs = res.get(prefix + 'documentation', {}).get(method, False)
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if has_code and not has_docs:
            found.append(method)
    if found:
        container.append('  {} ({})'.format(res['route'], ', '.join(found)))


def findTestNameAndLine(code, defs, matchpos):
    return [(name, line) for name, pos, line in defs if pos < matchpos][-1]


def getFunctionLineNumbers(code, func_code):
    start = code[:code.find(func_code)].count('\n') + 1
    end = start + func_code.count('\n')
    return start, end


def getEndpointStatus(resources, name, method, prefix=''):
    status = ''
    # method = 'GET' if real_method == 'HEAD' else real_method
    if method in resources[name].get(prefix + 'methods', {}):
        method_d = resources[name].get(prefix + 'methods')[method]
        status += '.. hint:: `CODE <{url}#L{startline}-L{endline}>`_'.format(**method_d)
    if method in resources[name].get(prefix + 'documentation', []):
        method_d = resources[name].get(prefix + 'documentation')[method]
        status += '\n.. tip:: `DOCS <{url}>`_'.format(**method_d)
    tested_methods_match = [True for tmethod, testfile, testname, line in resources[name].get(prefix + 'tests', []) if method == tmethod]
    if tested_methods_match:
        status += '\n.. attention:: TEST'
    return status


def main(argv=sys.argv):
    import max.rest

    # Get declared routes
    from max.rest.resources import RESOURCES
    resources = dict(RESOURCES)

    restricted_routes_with_code = []
    tables = ''
    errors = []
    untested = []
    undocumented = []

    total_functions = 0
    # Walk trough code looking for view declarations
    # and collect which methods are implemented for each route
    MAX_SRC_PATH = re.sub(r'(.*?)/max$', r'\1', max.__path__[0])
    commit_id = re.findall(r'[\da-f]{40} ([\da-f]{40})', open('{}/.git/logs/HEAD'.format(MAX_SRC_PATH)).read(), re.DOTALL)[-1]

    github_base_url = 'https://github.com/UPCnet/max/tree/{}'.format(commit_id)
    maxpath = max.rest.__path__[0]
    paths = [maxpath, '%s/admin' % maxpath]
    for path in paths:
        for item in os.listdir(path):
            filename = '%s/%s' % (path, item)
            if os.path.isfile(filename):
                if filename.endswith('.py'):
                    code = open(filename).read()
                    function_lines = re.findall(r'\n\s*@view_config\((.*?)\)(.*?)def\s+([^\(]+)(.*?)(?=\n+(?:[^\s]|$)+)', code, re.DOTALL)
                    if function_lines:
                        for fun in function_lines:
                            f_params, extra_view_configs, f_name, f_code = fun

                            # Save first occurrence of view config
                            views = [(parseParams(f_params), f_name, f_code), ]

                            # Search ant store extra @view_config statements
                            extra_params = (re.findall('\((.*?)\)', extra_view_configs))
                            for extra_param in extra_params:
                                parsed_params = parseParams(extra_param)
                                if parsed_params:
                                    views.append((parsed_params, f_name, f_code))

                            for function_params, function_name, function_code in views:
                                if not 'HTTPNotImplemented' in function_code:
                                    total_functions += 1
                                    try:
                                        method = function_params['request_method'].upper()
                                        code_key = 'methods'
                                        if 'restricted' in function_params.keys() or resources[function_params['route_name']]['route'].startswith('/admin'):
                                            code_key = 'restricted_' + code_key
                                            restricted_routes_with_code.append(function_params['route_name'])

                                        resources[function_params['route_name']].setdefault(code_key, {})
                                        startline, endline = getFunctionLineNumbers(code, function_code)
                                        view_info = {
                                            'url': '{}/{}'.format(github_base_url, filename.split('src/max/')[-1]),
                                            'startline': startline,
                                            'endline': endline}
                                        resources[function_params['route_name']][code_key][method] = view_info
                                        if "HEAD" in function_code and 'request.method' in function_code:
                                            resources[function_params['route_name']][code_key]['HEAD'] = view_info
                                    except:
                                        pass

    print ' > Found {} active view definitions'.format(total_functions)

    # Walk through documentation looking for enpoint headers:
    maxdocspath = '/'.join(maxpath.split('/')[:-2]) + '/docs/ca'
    docs = [('apirest', 'documentation'), ('apioperations', 'restricted_documentation')]

    base_url = 'file:///var/pyramid/maxdevel/src/max/docs/_build/html/ca'
    base_url = '/docs/v3/ca'
    total_docs = 0
    for doc, dockey in docs:
        docpath = '{}/{}.rst'.format(maxdocspath, doc)
        text = open(docpath).read()
        documented = re.findall(r'\.\. http:(\w+):: (.*?)\n', text)
        for method, route in documented:
            match_route = [name for name, rroute in resources.items() if re.sub(r'{(\w+)}', r':', rroute['route']) == re.sub(r'{(\w+)}', ':', route)]

            if match_route:
                total_docs += 1
                resources[match_route[0]].setdefault(dockey, {})
                anchor = '{}-{}'.format(method.lower(), re.sub(r'\/', r'-', route))
                resources[match_route[0]][dockey][method.upper()] = {
                    'url': '{}/{}.html#{}'.format(base_url, doc, anchor)}
            else:
                errors.append('ERROR: Route not matched for documented method {} {}, in file {}'.format(method.upper(), route, filename))

    print ' > Found {} method documentation entries'.format(total_docs)

    # Walk trough tests looking for endpoint routes:
    maxtestspath = '/'.join(maxpath.split('/')[:-2]) + '/max/tests'
    for filename in os.listdir(maxtestspath):
        if filename.startswith('test_'):
            testpath = '{}/{}'.format(maxtestspath, filename)
            text = open(testpath).read()
            test_def_locations = [(a.groups()[0], a.start(), getFunctionLineNumbers(text, a.groups()[0])[0]) for a in re.finditer(r'def\s+([^\(]+)', text, re.DOTALL | re.IGNORECASE)]
            tested_oauth = [a.groups() + findTestNameAndLine(text, test_def_locations, a.start()) for a in re.finditer(r'(head|get|post|put|delete)\([\"\'](\/+.*?)[\?\"\'].*?oauth2Header\((.*?)[\),]', text, re.IGNORECASE)]
            tested_anonymous = [a.groups() + ('anonymous',) + findTestNameAndLine(text, test_def_locations, a.start()) for a in re.finditer(r'(head|get|post|put|delete)\([\"\'](\/+.*?)[\?\"\'].*?\{\}', text, re.IGNORECASE)]
            tested = tested_oauth + tested_anonymous

            for method, route, user, testname, line in tested:
                route = re.sub(r'/{2,}', r'/', route)
                match_route = [name for name, rroute in resources.items() if re.sub(r'{(\w+)}', r':', rroute['route']) == re.sub(r'{(\w*)}|%s', r':', route)]
                user = 'anonymous' if user is None else user
                if match_route:
                    test_info = (method.upper(), filename, testname, line)
                    if 'test_manager' in user and match_route[0] in restricted_routes_with_code:
                        resources[match_route[0]].setdefault('restricted_tests', [])
                        resources[match_route[0]]['restricted_tests'].append(test_info)
                    else:
                        if 'test_manager' in user:
                            print 'mismatched user'
                        resources[match_route[0]].setdefault('tests', [])
                        resources[match_route[0]]['tests'].append(test_info)
                else:
                    errors.append('ERROR: Route not matched when using {} {}, in file {}'.format(method.upper(), route, filename))

#    restricted_docs = ['apioperations.rst']

    sections = [
        ('Usuaris Normals', ''),
        ('Usuaris Restringits', 'restricted_')
    ]

    routes = [(name, re.sub(r'{(\w+)}', r':\1', route['route'])) for name, route in resources.items()]
    sorted_routes = sorted(routes, key=lambda x: x[1])

    for title, prefix in sections:

        table1 = PrettyTable(['Endpoint', '**HEAD**', '**GET**', '**POST**', '**PUT**', '**DELETE**'])
        table1.hrules = ALL
        table1.align['Endpoint'] = "l"
        table1.align['**HEAD**'] = "l"
        table1.align['**GET**'] = "l"
        table1.align['**POST**'] = "l"
        table1.align['**PUT**'] = "l"
        table1.align['**DELETE**'] = "l"

        for name, route in sorted_routes:
            row = ['``{}``'.format(route),
                   getEndpointStatus(resources, name, 'HEAD', prefix=prefix),
                   getEndpointStatus(resources, name, 'GET', prefix=prefix),
                   getEndpointStatus(resources, name, 'POST', prefix=prefix),
                   getEndpointStatus(resources, name, 'PUT', prefix=prefix),
                   getEndpointStatus(resources, name, 'DELETE', prefix=prefix),
                   ]
            addMissingCodeErrors(errors, resources, name, prefix=prefix)
            addUntestedCodeErrors(untested, resources, name, prefix=prefix)
            addUndocumentedCodeErrors(undocumented, resources, name, prefix=prefix)

            table1.add_row(row)
        tables += TABLE_TEMPLATE.format(title, '-' * len(title), table1.get_string())

    open('{}/report.rst'.format(maxdocspath), 'w').write(TEMPLATE.format(tables))
    print ' > Generated new {}'.format('{}/report.rst'.format(maxdocspath))
    print
    if errors:
        print 'Errors'
        print '======'
        print
        print '\n'.join(errors)
        print
    if undocumented:
        print 'Undocumented Code'
        print '================='
        print
        print '\n'.join(undocumented)
        print
    if untested:
        print 'Untested Code'
        print '============='
        print
        print '\n'.join(untested)
        print
    print
