import os
import json
import re
import shutil
import sys
import threading
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path
import webbrowser

import click
from jsonschema.exceptions import ValidationError
from jinja2 import Template
from werkzeug.datastructures import FileStorage

from converter_app.app import create_app
from converter_app.profile_migration.utils.registration import Migrations
from converter_app.utils import get_app_root, run_conversion, load_public_profiles
from converter_app.converters import Converter
from converter_app.models import File, Profile
from converter_app.readers import Readers
from converter_app.validation import validate_profile

os.environ["TYPEGUARD_DISABLE"] = "1"


def copy_profiles(profile_dir: Path | str):
    if isinstance(profile_dir, str):
        profile_dir = Path(profile_dir)
    root = get_app_root() / 'profiles'
    if not root.exists():
        return
    for t in os.listdir(root):
        dst = profile_dir / t
        src = root / t
        if not dst.exists():
            ProfileFile.convert_path_to_profile(src)
            shutil.copy2(src, dst)


# ----------------------------
# Custom Click Types & Validators
# ----------------------------
class ExistingFile(click.Path):
    def convert(self, value, param, ctx):
        path = Path(value)
        if not path.exists():
            raise click.BadParameter(f"{path} does not exist!")
        if path.is_dir():
            raise click.BadParameter(f"{path} is a directory!")
        return path


class ProfileFile(ExistingFile):
    def convert(self, value, param, ctx):
        path = super().convert(value, param, ctx)
        return self.convert_path_to_profile(Path(path))

    @classmethod
    def convert_path_to_profile(cls, path: Path):
        try:
            Migrations().prepare_and_run_migration(path, False)
            content = json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, KeyError):
            raise click.BadParameter(f"{path} is not a valid JSON!")
        try:
            validate_profile(content)
        except  ValidationError as e:
            raise click.BadParameter(e.message)
        return path


class CamelCaseName(click.ParamType):
    name = "CamelCaseName"
    regex = re.compile(r'^[A-Za-z]+$')

    def convert(self, value, param, ctx):
        if not self.regex.match(value):
            raise click.BadParameter(f"{value} is not a valid name! Must be letters only.")
        # Transform to snake-case list like original code
        value = f'{value[0].lower()}{value[1:]}'
        return re.sub(r'([A-Z])', lambda m: f' {m.group(0).lower()}', value).split()


class OutputType(click.Choice):
    def __init__(self):
        super().__init__(["jcampzip", "rdf", "jcamp"])


# ----------------------------
# Main CLI Group
# ----------------------------
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Run the Converter in web browser"""
    if ctx.invoked_subcommand is None:
        if not Profile.cli_profiles_dir.exists():
            load_public_profiles(Profile.cli_profiles_dir / 'cli')
        copy_profiles(Profile.cli_profiles_dir / 'cli')
        app = create_app(True, True)

        def open_browser():
            webbrowser.open("http://127.0.0.1:5000")

        threading.Timer(1.0, open_browser).start()
        app.run(host='127.0.0.1', port=5000)
# ----------------------------
# Main dev Group
# ----------------------------
@click.group()
def dev():
    """Converter App development tools"""
    pass


# ----------------------------
# Edit CLI Profiles
# ----------------------------
@cli.command()
def edit_cli_profiles():
    """Run the profile editor in web browser"""
    if not Profile.cli_profiles_dir.exists():
        load_public_profiles(Profile.cli_profiles_dir / 'cli')
    copy_profiles(Profile.cli_profiles_dir / 'cli')
    app = create_app(True)

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000")

    threading.Timer(1.0, open_browser).start()
    app.run(host='127.0.0.1', port=5000)


# ----------------------------
# New Reader
# ----------------------------
@dev.command()
@click.option('-n', '--name', type=CamelCaseName(), prompt=True,
              help='Reader name in CamelCase')
@click.option('-p', '--priority', type=int, prompt=True,
              help='Lower number → higher priority for reader selection')
@click.option('--profile', type=ProfileFile(), help='Optional test profile JSON')
@click.option('-t', '--test-file', type=ExistingFile(), prompt=True,
              help='Test file for development')
def new_reader(name, priority, profile, test_file):
    reader_name_sc = "_".join(name)
    context = {
        "READER_NAME_CC": "".join([x.capitalize() for x in name]),
        "READER_NAME_SC": reader_name_sc,
        "UUID": str(uuid.uuid4()),
        "PRIO": priority,
        "TEST_FILE": f"test_static/test_files/{reader_name_sc}_{test_file.name}"
    }

    template_path = get_app_root() / 'converter_app/readers/helper/READER_TEMPLATE.py.txt'
    test_template_path = get_app_root() / 'converter_app/readers/helper/TEST_TEMPLATE.py.txt'
    target_reader_path = get_app_root() / f'converter_app/readers/{reader_name_sc}_reader.py'
    target_reader_test_path = get_app_root() / f'converter_app/test_static/test_{reader_name_sc}_reader.py'
    target_reader_test_file_path = get_app_root() / context["TEST_FILE"]

    os.makedirs(target_reader_test_file_path.parent, exist_ok=True)
    shutil.copy(test_file, target_reader_test_file_path)

    for src, dst in [(template_path, target_reader_path), (test_template_path, target_reader_test_path)]:
        with open(src, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        with open(dst, 'w+', encoding='utf-8') as f:
            f.write(template.render(**context))


# ----------------------------
# Convert Command
# ----------------------------
@cli.command()
@click.option('-i', '--input-file', type=ExistingFile(), required=True,
              help='File to convert')
@click.option('-o', '--output', type=OutputType(), required=True,
              help='Output type')
def convert(input_file, output):
    """Convert a File -> Output will be in the same directory as the input file!"""
    if not Profile.cli_profiles_dir.exists():
        load_public_profiles(Profile.cli_profiles_dir / 'cli')
        copy_profiles(Profile.cli_profiles_dir / 'cli')

    with open(input_file, 'rb') as f:
        content_type, _ = mimetypes.guess_type(input_file.name)
        content_type = content_type or "application/octet-stream"
        content_length = os.fstat(f.fileno()).st_size
        fs = FileStorage(stream=f, filename=input_file.name, content_type=content_type,
                         content_length=content_length, )
        file = File(fs)
        reader = Readers.instance().match_reader(file)
        if not reader:
            raise click.ClickException(f"No reader available for {input_file}")
        reader.process()
        converter = Converter.match_profile('cli', reader.as_dict)
        writer = run_conversion(converter, output)
    output_file = str(input_file) + writer.suffix
    with open(output_file, 'wb+') as out_f:
        out_f.write(writer.write())
    click.echo(f"Conversion complete: {output_file}")


# ----------------------------
# Migrate Command
# ----------------------------
@cli.command()
@click.option('-f', '--force', is_flag=True, help="Apply all migrations")
@click.option('--profile', type=ProfileFile(), help='Optional test profile JSON')
def migrate(force, profile):
    if profile is not None and force:
        pf = Path(profile)
        Migrations().prepare_and_run_migration(pf, force)
    else:
        profile_dir = create_app().config['PROFILES_DIR']
        click.echo(f'Migrating all profiles in {profile_dir}')
        Migrations().run_migration(profile_dir, force)
    click.echo("Migration complete!")


# ----------------------------
# New Migration
# ----------------------------
@dev.command()
def new_migration():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    context = {
        'LAST_IDENTIFIER': Migrations().last,
        'IDENTIFIER': timestamp,
    }

    template_path = get_app_root() / 'converter_app/profile_migration/utils/MIGRATION_TEMPLATE.py.txt'
    target_path = get_app_root() / f'converter_app/profile_migration/{timestamp}_migration.py'

    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())

    with open(target_path, 'w+', encoding='utf-8') as f:
        f.write(template.render(**context))

    click.echo(f"Migration created: {target_path}")


# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    if not getattr(sys, 'frozen', False):
        cli.add_command(dev)
    cli()
