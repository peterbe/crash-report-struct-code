import argparse
import sys
import json
from pprint import pprint

import re


START_AT = '' #' ' * 6


def camelize(s):
    def replacer(match):
        return match.group().replace('_', '').upper()

    return re.sub('_([a-z])', replacer, s)


def get_rows(schema, depth=1, python=False):
    # assert schema
    # if 'properties' not in schema:
    #
    #     assert schema['items']['$ref'], schema
    #     schema = definitions[schema['items']['$ref'].split('/')[-1]]
    #     print "NEW SCHEMA", schema
    #     # raise Exception(schema)
    if 'properties' not in schema:
        print "******"
        print schema
        raise Exception('HELL!!')

    def render_bool(thing, value):
        if python:
            return '{}={}'.format(thing, value)#TEMP
        else:
            value = value and 'true' or 'false'
            return '{} = {}'.format(thing, value)

    def render_type(thing):
        if python:
            return thing + '()'
        else:
            return thing

    for prop in sorted(schema['properties']):
        meta = schema['properties'][prop]
        if 'string' in meta['type']:
            if 'integer' in meta['type']:
                print >>sys.stderr, (
                    "NOTE!! {!r} allows the type to be String AND Integer".format(
                        prop
                    )
                )
            yield 'StructField("{}", {}, {})'.format(
                prop,
                render_type('StringType'),
                render_bool('nullable', 'null' in meta['type'])
            )
        elif 'integer' in meta['type']:
            yield 'StructField("{}", {}, {})'.format(
                prop,
                render_type('IntegerType'),
                render_bool('nullable', 'null' in meta['type'])
            )
        elif 'boolean' in meta['type']:
            yield 'StructField("{}", {}, {})'.format(
                prop,
                render_type('BooleanType'),
                render_bool('nullable', 'null' in meta['type'])
            )
        elif meta['type'] == 'array' and 'items' not in meta:
            # Assuming strings in the array
            # XXX what does this containsNull = false mean?!
            yield (
                'StructField("{}", ArrayType({}, {}'
                '), {})'.format(
                    prop,
                    render_type('StringType'),
                    render_bool('containsNull', False),
                    render_bool('nullable', True)
                )
            )
        elif meta['type'] == 'array' and 'items' in meta:
            # Assuming strings in the array
            # XXX what does this containsNull = false mean?!
            # if 'properties' not in meta:
            #     meta = definitions[prop]
            rows = list(get_rows(meta['items'], depth=depth + 1, python=python))
            yield (
                'StructField("{}", ArrayType({}), {})'.format(
                    prop,
                    write_rows(rows, ' ' * (2 * (depth + 1)), python=python),
                    render_bool('nullable', True)
                )
            )
        elif meta['type'] == 'object':
            rows = list(get_rows(meta, depth=depth + 1, python=python))
            yield 'StructField("{}", {}, {})'.format(
                prop,
                write_rows(rows, ' ' * (2 * (depth + 1)), python=python),
                render_bool('nullable', True)
            )

        else:
            print >>sys.stderr, "TROUBLE", prop, str(meta)[:100]

def write_rows(rows, indentation=' ' * 2, python=False):
    if python:
        code = 'StructType([\n'
    else:
        code = 'StructType(List(\n'

    for row in rows:
        code += '{}{}'.format(indentation, row)
        code += ',\n'
    code = code.rstrip().rstrip(',')
    if python:
        code += '\n{}])'.format(indentation[:-2])
    else:
        code += '\n{}))'.format(indentation[:-2])

    # if python:
    #     def replacer(match):
    #         a, b = match.groups()
    #         return '{}={}'.format(a, b.title())
    #     code = re.sub(
    #         r'(\w+) = (true|false)',
    #         replacer,
    #         code,
    #     )
    #     # code = code.replace('StringType', 'StringType()')
    #     # code = code.replace('BooleanType', 'BooleanType()')
    #     # code = code.replace('nullable = false', 'nullable=False')
    #     # code = code.replace('nullable = true', 'nullable=True')
    #     # code = code.replace('containsNull = false', 'containsNull=False')
    return code


def replace_definitions(schema, definitions):
    if 'properties' in schema:
        for prop, meta in schema['properties'].items():
            replace_definitions(meta, definitions)
    elif 'items' in schema:
        if '$ref' in schema['items']:
            ref = schema['items']['$ref'].split('/')[-1]
            schema['items'] = definitions[ref]
            replace_definitions(schema['items'], definitions)
        else:
            replace_definitions(schema['items'], definitions)
    elif '$ref' in str(schema):
        print str(schema)
        raise Problem

# definitions =
def run(schema_uri, python=False):
    if '://' in schema_uri and schema_uri.startswith('http'):
        import requests
        schema = requests.get(schema_uri).json()
    else:
        with open(schema_uri) as f:
            schema = json.load(f)
    replace_definitions(schema, schema['definitions'])

    assert '$ref' not in str(schema), 're-write didnt work'

    rows = list(get_rows(schema, python=python))
    indentation = ''
    code = ''
    code += '\n'
    code += write_rows(rows, python=python)

    print code

    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'schema',
        help="Location of the crash_report.json schema file (URL or file)",
        # nargs='+'
    )
    parser.add_argument(
        '--python',
        help="Generate Python code instead of Scala code",
        action="store_true",
    )
    args = parser.parse_args()
    return run(
        args.schema,
        python=args.python,
    )

if __name__ == '__main__':
    sys.exit(main())
    # import sys
    # schema = json.load(open(sys.argv[1]))
    # sys.exit(run(schema))
