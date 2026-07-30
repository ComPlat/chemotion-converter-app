"""
Reader for the result file of the DELFIN workflow, a wrapper around ORCA that computes
redox potentials and photophysical properties of a molecule.
"""
import json
import logging
import re

from converter_app.models import File
from converter_app.readers.helper.reader import Readers
from converter_app.readers.json_reader import JsonReader

logger = logging.getLogger(__name__)

# Top level keys a DELFIN result file always carries.
REQUIRED_KEYS = ('metadata', 'control', 'delfin_summary')

# Redox series. Every step of a series becomes a section of its own.
STATE_SERIES = ('oxidized_states', 'reduced_states')

# Single state sections that repeat the first step of a series. They are dropped if their
# content is really identical to that step.
ALIAS_SECTIONS = {
    'oxidized_state': ('oxidized_states', 'ox_step_1'),
    'reduced_state': ('reduced_states', 'red_step_1'),
}

# The redox potentials are reported once per calculation method. All of them are collected
# into a single comparison table.
REDOX_METHODS = ('m1_avg', 'm2_step', 'm3_mix', 'final')

# Key results that are lifted into the overview table for every state:
# (name in the overview, sub section of the state, key in that sub section)
STATE_OVERVIEW_KEYS = (
    ('charge', 'optimization', 'charge'),
    ('multiplicity', 'optimization', 'multiplicity'),
    ('converged', 'optimization', 'converged'),
    ('energy_hartree', 'optimization', 'hartree'),
    ('gibbs_free_energy_hartree', 'thermochemistry', 'total_gibbs_free_energy_hartree'),
    ('homo_eV', 'orbitals', 'homo_eV'),
    ('lumo_eV', 'orbitals', 'lumo_eV'),
    ('gap_eV', 'orbitals', 'gap_eV'),
)

# Keys of control.validated that describe the sample rather than the calculation setup.
SAMPLE_KEYS = (('sample_name', 'NAME'), ('smiles', 'SMILES'), ('redox_reference', 'reference_CV'))

TRAILING_NUMBER = re.compile(r'(\d+)$')


class DelfinJsonReader(JsonReader):
    """
    Implementation of the DELFIN Reader. It extends converter_app.readers.JsonReader.

    The generic JsonReader flattens a DELFIN file into a single table holding more than
    18000 metadata entries, because every list of records - molecular orbitals, vibrational
    modes, OCCUPIER candidates - is walked key by key. This reader keeps the parsing
    machinery of its parent and only rearranges the result:

    * every logical section of the run becomes an input table of its own, marked by the
      metadata key "section"
    * every list of uniform records becomes a real data table
    * the first table is a curated overview of the key results of the run
    * empty sections and sections that only repeat another one are skipped and reported
      in the overview
    """
    identifier = 'delfin_json_reader'
    priority = 15

    # Lists of scalars up to this length are inlined into the metadata as a single entry,
    # longer ones become a table of their own.
    inline_list_limit = 8

    def __init__(self, file: File, *tar_content):
        super().__init__(file, *tar_content)
        self._delfin = None
        self._record_lists = []
        self._skipped = []

    def check(self):
        """
        :return: True if the file is a json file carrying the DELFIN top level keys
        """
        if not super().check():
            return False
        try:
            data = json.loads(self.file.content)
        except (ValueError, TypeError):
            return False
        if not isinstance(data, dict) or not all(key in data for key in REQUIRED_KEYS):
            return False
        self._delfin = data
        return True

    def prepare_tables(self):
        """
        Builds one table per section of the DELFIN run. The order of the tables is fixed,
        because a profile references an input table by its index. The control section holds
        the whole calculation setup and comes last, so that the result sections stay close
        to the overview.

        :return: [overview, input, computed, states..., occupier..., rest..., control...]
        """
        if self._delfin is None:
            self._delfin = json.loads(self.file.content)
        # the inherited _pre_read_elem resolves "#/..." pointers against this document
        self.file_as_dict = self._delfin

        tables = []
        overview = self._new_section(tables, 'overview')
        # read into the overview table, or read last, so they are excluded from the
        # generic section loop
        handled = {'metadata', 'delfin_summary', 'control_flags', 'git_commit', 'control'}

        self._add_input_section(tables, handled)
        self._add_computed_section(tables, handled)
        self._add_state_sections(tables, handled)
        self._add_occupier_section(tables, handled)
        self._add_remaining_sections(tables, handled)
        self._add_control_section(tables, handled)

        self._fill_overview(overview)
        return tables

    # -- hooks of the parent reader -------------------------------------------------

    def _handle_scalar(self, key: str, value):
        self.table.add_metadata(self._key(key), self._fmt(value))

    def _handle_number_list(self, key: str, values: list):
        self._collect_scalar_list(key, values)

    def _handle_list(self, key: str, values: list) -> bool:
        if not values:
            return True
        if all(isinstance(item, dict) for item in values):
            self._record_lists.append((self._key(key), values))
            return True
        if all(not isinstance(item, (dict, list)) for item in values):
            self._collect_scalar_list(key, values)
            return True
        return False

    def _collect_scalar_list(self, key: str, values: list):
        if not values:
            return
        name = self._key(key)
        if len(values) <= self.inline_list_limit:
            self.table.add_metadata(name, ', '.join(self._fmt(value) for value in values))
        else:
            self._record_lists.append((name, [{name: value} for value in values]))

    # -- table construction --------------------------------------------------------

    def _new_section(self, tables: list, name: str):
        table = self.append_table(tables)
        table.add_metadata('section', name)
        self.table = table
        return table

    def _read_section(self, tables: list, name: str, source: dict, skip: tuple = ()):
        """
        Flattens all scalars of a section into a table of its own and turns every list of
        records below it into a separate data table.

        :param tables: the list of all tables
        :param name: name of the section, shown as metadata key "section"
        :param source: the section as read from the json document
        :param skip: keys of the section that must not be read
        :return: the section table or None if the section holds no metadata
        """
        table = self._new_section(tables, name)
        self._record_lists = []
        self._rec_reader({k: v for k, v in source.items() if k not in skip}, '')

        # a section that consists of records only does not need a table for its metadata
        if len(table['metadata']) == 1:
            tables.pop()
            table = None
            if not self._record_lists:
                self._skipped.append(f'{name} (empty)')

        for list_name, records in self._record_lists:
            self._add_record_table(tables, f'{name} {list_name}', records)
        self._record_lists = []
        return table

    def _add_record_table(self, tables: list, name: str, records: list):
        """
        Turns a list of dicts into a table. The columns are the union of all keys of the
        records, in order of their first appearance.

        :param tables: the list of all tables
        :param name: name of the table, shown as metadata key "section"
        :param records: the list of dicts
        :return: the new table
        """
        table = self.append_table(tables)
        table.add_metadata('section', name)
        columns = []
        for record in records:
            for key in record:
                if key not in columns:
                    columns.append(key)
        table['columns'] = [{'key': str(idx), 'name': key} for idx, key in enumerate(columns)]
        table['rows'] = [[self._cell(record.get(key)) for key in columns] for record in records]
        return table

    # -- sections ------------------------------------------------------------------

    def _add_input_section(self, tables: list, handled: set):
        handled.add('input')
        source = self._as_dict(self._delfin.get('input'))
        if not source:
            return
        self._read_section(tables, 'input', source, skip=('xyz_body',))
        xyz_body = source.get('xyz_body')
        if isinstance(xyz_body, list) and xyz_body:
            self._add_record_table(tables, 'input xyz_body', self._as_xyz_records(xyz_body))

    def _as_xyz_records(self, lines: list) -> list:
        """
        Splits the lines of a xyz body into element and coordinates. Lines that do not
        follow that layout are kept as they are.

        :param lines: the lines of the xyz body
        :return: a list of records
        """
        records = []
        for line in lines:
            fields = str(line).split()
            if len(fields) != 4:
                return [{'line': str(entry)} for entry in lines]
            records.append({
                'element': fields[0],
                'x': self._number(fields[1]),
                'y': self._number(fields[2]),
                'z': self._number(fields[3])
            })
        return records

    def _add_computed_section(self, tables: list, handled: set):
        handled.add('computed')
        computed = self._as_dict(self._delfin.get('computed'))
        if not computed:
            return
        redox = self._as_dict(computed.get('redox_potentials'))
        section = {key: value for key, value in computed.items() if key != 'redox_potentials'}
        if redox:
            section['redox_potentials'] = {
                key: value for key, value in redox.items()
                if key not in ('gibbs_energies_hartree', *REDOX_METHODS)
            }
        self._read_section(tables, 'computed', section)

        methods = [(name, self._as_dict(redox.get(name))) for name in REDOX_METHODS]
        methods = [(name, values) for name, values in methods if values]
        if methods:
            self._add_record_table(tables, 'computed redox_potentials per method', [
                {'method': name, **values} for name, values in methods
            ])

        gibbs = self._as_dict(redox.get('gibbs_energies_hartree'))
        if gibbs:
            self._add_record_table(tables, 'computed gibbs_energies', [
                {'charge': charge, 'gibbs_free_energy_hartree': value}
                for charge, value in gibbs.items()
            ])

    def _add_state_sections(self, tables: list, handled: set):
        handled.add('ground_state_S0')
        ground_state = self._as_dict(self._delfin.get('ground_state_S0'))
        if ground_state:
            self._read_section(tables, 'ground_state_S0', ground_state)

        for series in STATE_SERIES:
            handled.add(series)
            steps = self._as_dict(self._delfin.get(series))
            for step in self._sorted_steps(steps):
                if self._as_dict(steps[step]):
                    self._read_section(tables, f'{series} {step}', steps[step])

        for alias, (series, step) in ALIAS_SECTIONS.items():
            handled.add(alias)
            source = self._as_dict(self._delfin.get(alias))
            if not source:
                continue
            if source == self._as_dict(self._delfin.get(series)).get(step):
                self._skipped.append(f'{alias} (identical to {series}.{step})')
                continue
            self._read_section(tables, alias, source)

    def _add_occupier_section(self, tables: list, handled: set):
        handled.add('occupier')
        occupier = self._as_dict(self._delfin.get('occupier'))
        for step in self._sorted_steps(occupier):
            source = self._as_dict(occupier[step])
            if not source:
                continue
            skip = ()
            if source.get('orbitals') and source['orbitals'] == self._state_orbitals(step):
                skip = ('orbitals',)
                self._skipped.append(f'occupier.{step}.orbitals (identical to the state orbitals)')
            self._read_section(tables, f'occupier {step}', source, skip=skip)

    def _state_orbitals(self, step: str):
        """
        :param step: name of an OCCUPIER step
        :return: the orbitals of the state that belongs to the step, if there is one
        """
        if step == 'initial':
            state = self._delfin.get('ground_state_S0')
        elif step.startswith('ox_'):
            state = self._as_dict(self._delfin.get('oxidized_states')).get(step)
        elif step.startswith('red_'):
            state = self._as_dict(self._delfin.get('reduced_states')).get(step)
        else:
            state = None
        return self._as_dict(state).get('orbitals')

    def _add_control_section(self, tables: list, handled: set):
        handled.add('control')
        control = self._as_dict(self._delfin.get('control'))
        if not control:
            return
        validated = self._as_dict(control.get('validated'))
        if not validated:
            self._read_section(tables, 'control', control)
            return

        table = self._read_section(tables, 'control validated', validated)
        parsed = self._as_dict(control.get('parsed'))
        if parsed and table is not None:
            # compared on the formatted value, so that "" and null do not count as deviation
            overrides = [key for key, value in parsed.items()
                         if self._fmt(value) != self._fmt(validated.get(key))]
            for key in overrides:
                table.add_metadata(f'parsed_override_{key}', self._fmt(parsed[key]))
            self._skipped.append(
                f'control.parsed ({len(overrides)} deviating values kept as parsed_override_*)')

        others = {key: value for key, value in control.items()
                  if key not in ('parsed', 'validated')}
        if others:
            self._read_section(tables, 'control', others)

    def _add_remaining_sections(self, tables: list, handled: set):
        """
        Reads every section that has no explicit handling above. This keeps sections of a
        full DELFIN run - emission, intersystem_crossing, esd_results - readable without
        touching this reader again.
        """
        for name, value in self._delfin.items():
            if name in handled:
                continue
            if isinstance(value, dict):
                if value:
                    self._read_section(tables, name, value)
                else:
                    self._skipped.append(f'{name} (empty)')
            elif isinstance(value, list) and value:
                self._read_section(tables, name, {name: value})
            elif value in ([], None, ''):
                self._skipped.append(f'{name} (empty)')
            else:
                self._read_section(tables, name, {name: value})

    # -- overview ------------------------------------------------------------------

    def _fill_overview(self, table):
        for key, value in self._as_dict(self._delfin.get('metadata')).items():
            table.add_metadata(f'setup_{key}', self._fmt(value))

        validated = self._as_dict(self._as_dict(self._delfin.get('control')).get('validated'))
        for name, key in SAMPLE_KEYS:
            if validated.get(key) not in (None, ''):
                table.add_metadata(name, self._fmt(validated[key]))

        self._add_summary_overview(table)
        self._add_state_overview(table)
        self._add_redox_overview(table)

        for key, value in self._as_dict(self._delfin.get('control_flags')).items():
            table.add_metadata(f'control_flag_{key}', self._fmt(value))
        if 'git_commit' in self._delfin:
            table.add_metadata('git_commit', self._fmt(self._delfin['git_commit']))
        if self._skipped:
            table.add_metadata('skipped_sections', '; '.join(self._skipped))

    def _add_summary_overview(self, table):
        summary = self._as_dict(self._delfin.get('delfin_summary'))
        for key, value in self._as_dict(summary.get('redox_potentials_vs_fc')).items():
            table.add_metadata(f'summary_{key}_V', self._fmt(value))
        run_time = self._as_dict(summary.get('total_run_time'))
        if 'total_seconds' in run_time:
            table.add_metadata('total_run_time_s', self._fmt(run_time['total_seconds']))
        for key, value in summary.items():
            if not isinstance(value, (dict, list)):
                table.add_metadata(f'summary_{key}', self._fmt(value))

    def _add_state_overview(self, table):
        for label, state in self._states():
            for name, group, key in STATE_OVERVIEW_KEYS:
                source = self._as_dict(state.get(group))
                if key in source:
                    table.add_metadata(f'{label}_{name}', self._fmt(source[key]))

    def _states(self):
        """
        :return: (label, state) of the ground state and of every step of every series
        """
        states = []
        ground_state = self._as_dict(self._delfin.get('ground_state_S0'))
        if ground_state:
            states.append(('S0', ground_state))
        for series in STATE_SERIES:
            steps = self._as_dict(self._delfin.get(series))
            states += [(step, self._as_dict(steps[step])) for step in self._sorted_steps(steps)]
        return states

    def _add_redox_overview(self, table):
        redox = self._as_dict(
            self._as_dict(self._delfin.get('computed')).get('redox_potentials'))
        for key, value in self._as_dict(redox.get('final')).items():
            table.add_metadata(f'final_{key}_V', self._fmt(value))
        used = [key for key, value in self._as_dict(redox.get('method_flags')).items() if value]
        if used:
            table.add_metadata('redox_method_flags', ', '.join(used))

    # -- helper --------------------------------------------------------------------

    @staticmethod
    def _key(key: str) -> str:
        """
        Turns a json path of a section into a flat metadata key.

        :param key: json path relative to the section, "." separated
        :return: the metadata key
        """
        return key.lstrip('.').replace('.', '_') or 'value'

    @staticmethod
    def _fmt(value) -> str:
        """
        :param value: any json value
        :return: the value as string, as expected of metadata by Reader.validate
        """
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'yes' if value else 'no'
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(',', ':'))
        return str(value)

    @staticmethod
    def _cell(value):
        """
        :param value: any json value
        :return: the value as cell of a table, numbers are kept as they are
        """
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'yes' if value else 'no'
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(',', ':'))
        return value

    def _number(self, value: str):
        try:
            return self.as_number(value)
        except ValueError:
            return value

    @staticmethod
    def _as_dict(value) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _sorted_steps(steps: dict) -> list:
        """
        Sorts step names by their trailing number, so that red_step_10 follows red_step_9.

        :param steps: the steps of a series
        :return: the sorted step names
        """
        def order(name):
            match = TRAILING_NUMBER.search(name)
            return int(match.group(1)) if match else 0, name

        return sorted(steps, key=order)


Readers.instance().register(DelfinJsonReader)
