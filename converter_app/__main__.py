import argparse
import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from converter_app.app import create_app
from converter_app.profile_migration.utils.registration import Migrations


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, Path(value))

    @staticmethod
    def validate(parser, value):
        fp = Path(value)
        if not fp.exists():
            parser.error(f'{fp} does not exist!')
        if fp.is_dir():
            parser.error(f'{fp} is a directory!')

class ProfileAction(FileAction):
    def validate(self, parser, value):
        super().validate(parser, value)
        with open(str(value), 'r', encoding='utf-8') as f:
            try:
                content = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                parser.error(f'{value} is not a valid JSON!')
        if 'identifier' not in content:
            parser.error(f'{value} is missing "identifier" key!')

class NameAction(argparse.Action):
    regex = re.compile(r'^[A-Za-z]+$')

    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        value = f'{value[0].lower()}{value[1:]}'
        value = re.sub(r'([A-Z])', lambda m: f' {m.group(0).lower()}', value).split()
        setattr(namespace, self.dest, value)

    @classmethod
    def validate(cls, parser, value):
        if not cls.regex.match(value):
            parser.error(f'{value} is not a valid name!')

class PrioAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @staticmethod
    def validate(parser, value):
        try:
            value = int(value)
        except ValueError:
            parser.error(f'{value} is not an integer!')

        if value < 0:
            parser.error(f'Priority must be a positive integer!')


class MethodAction(argparse.Action):
    methods = ['new_reader', 'migrate', 'new_migration']

    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @classmethod
    def validate(cls, parser, value):
       if value not in cls.methods:
           parser.error(f'{value} is not a valid method! Must be one of {cls.methods}')


def main_cli():

    parser = argparse.ArgumentParser(
        prog='python -m converter_app',
        description='Helps to develop new reader')

    parser.add_argument('methode', help=f'Must one of: {MethodAction.methods}!', action=MethodAction)

    admin_group = parser.add_argument_group('new_reader')
    name_arg = admin_group.add_argument('-n' , '--name', action=NameAction,
                        help='Reader name. The name must be in CamelCase!')
    priority_arg = admin_group.add_argument('-p', '--priority', action=PrioAction,
                        help='The lower the number, the earlier the reader is checked. Therefore, the probability that it will be used increases!')
    admin_group.add_argument('-profile', action=ProfileAction,
                        help='A test Profile if existing!')
    file_arg = admin_group.add_argument('-t', '--test_file', action=FileAction,
                        help='A test file for test drive development!')

    migrate_group = parser.add_argument_group('migrate')
    migrate_group.add_argument('-f' , '--force', action='store_true', help="If force is set all migration scripts will be appl")

    args = parser.parse_args()

    if args.methode == 'new_reader':
        _new_reader(args, parser, [name_arg, priority_arg, file_arg])
    elif args.methode == 'migrate':
        Migrations().run_migration(create_app().config['PROFILES_DIR'], args.force)
    elif args.methode == 'new_migration':
        _new_migration()


def _new_migration():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    context = {
        'LAST_IDENTIFIER': Migrations().last,
        'IDENTIFIER': timestamp,
    }

    template_path = Path(__file__).parent / 'profile_migration/utils/MIGRATION_TEMPLATE.py.txt'
    targe_reader_path = Path(__file__).parent / f'profile_migration/{timestamp}_migration.py'

    with open(str(template_path), 'r', encoding='utf-8') as f:
        template = Template(f.read())

    with open(targe_reader_path, 'w+', encoding='utf-8') as f:
        f.write(template.render(**context))

def _new_reader(args, parser, arg_objets):
    for arg in arg_objets:
        if getattr(args, arg.dest, None) is None:
            setattr(args, arg.dest, input(f'{arg.help}\n Enter {arg.dest}:'))
            arg.validate(parser, getattr(args, arg.dest, None))

    reader_name_sc = '_'.join(args.name)
    context = {
        'READER_NAME_CC': ''.join([str(x).capitalize() for x in args.name]),
        'READER_NAME_SC': reader_name_sc,
        'UUID': uuid.uuid4().__str__(),
        'PRIO': args.priority,
        'TEST_FILE': f'test_static/test_files/{reader_name_sc}_{args.test_file.name}'
    }

    template_path = Path(__file__).parent / 'readers/helper/READER_TEMPLATE.py.txt'
    test_template_path = Path(__file__).parent / 'readers/helper/TEST_TEMPLATE.py.txt'
    targe_reader_path = Path(__file__).parent / f'readers/{reader_name_sc}_reader.py'
    targe_reader_test_path = Path(__file__).parent.parent / f'test_static/test_{reader_name_sc}_reader.py'
    targe_reader_test_file_path = Path(__file__).parent.parent / context['TEST_FILE']

    os.makedirs(targe_reader_test_file_path.parent, exist_ok=True)
    shutil.copy(args.test_file, targe_reader_test_file_path)

    with open(str(template_path), 'r', encoding='utf-8') as f:
        template = Template(f.read())

    with open(targe_reader_path, 'w+', encoding='utf-8') as f:
        f.write(template.render(**context))

    with open(str(test_template_path), 'r', encoding='utf-8') as f:
        template = Template(f.read())

    with open(targe_reader_test_path, 'w+', encoding='utf-8') as f:
        f.write(template.render(**context))

if __name__ == '__main__':
    main_cli()