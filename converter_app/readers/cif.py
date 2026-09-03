import logging
import os
import re
import tempfile
from functools import reduce
from math import gcd
from zipfile import ZipFile

from gemmi import cif
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

try:
    from mofid_wrapper import cif2mofid
    # Importing mofid_wrapper is what puts BABEL_DATADIR/BABEL_LIBDIR into the
    # environment, so the bundled obabel below only works via this import.
    from mofid_wrapper.cpp_cheminformatics import OBABEL_BIN, runcmd
except (ImportError, RuntimeError):
    # mofid_wrapper ships prebuilt binaries for Linux x86_64 only, and raises at
    # import time when those are missing. MOF identification is optional, so the
    # reader keeps working without it -- see _add_mofid_metadata.
    cif2mofid = None

logger = logging.getLogger(__name__)

# The MOF identifiers surfaced as 'mofid.<key>' metadata.
MOFID_RESULT_KEYS = (
    'mofid',
    'mofkey',
    'smiles',
    'smiles_nodes',
    'smiles_linkers',
    'topology',
    'cat',
)

MOFID_METADATA_PREFIX = 'mofid.'

# Integer lists (the component ratios) are joined with this, staying index-aligned
# with the '.'-joined smiles_nodes / smiles_linkers they describe.
MOFID_LIST_SEPARATOR = ','

# The CCDC deposition number is a standard CIF tag the mofid pipeline does not
# surface, so read it off the CIF text: _database_code_depnum_ccdc_archive
# 'CCDC 755080' yields '755080'.
CCDC_PATTERN = re.compile(
    r"_database_code_depnum_ccdc_archive\s+['\"]?\s*(?:CCDC\s+)?([A-Za-z0-9-]+)",
    re.IGNORECASE)

# Bounds the obabel calls that count building blocks; they are fast (well under a
# second per file), so this only catches a hang.
OBABEL_TIMEOUT = 60


def _canonical_smiles(smiles):
    """Canonical SMILES for a fragment, or None when Open Babel cannot parse it."""
    run = runcmd([OBABEL_BIN, f'-:{smiles}', '-ocan'], timeout=OBABEL_TIMEOUT)
    output = (run.stdout or '').strip().split()
    return output[0] if output else None


def _count_fragments(cif_path):
    """Count the building-block instances in one of mofid's decomposition CIFs.

    mofid writes the nodes and linkers of the whole unit cell with the other
    component stripped, so each block is a discrete fragment.
    Returns ({canonical_smiles: count}, total_count).
    """
    if not os.path.exists(cif_path):
        return {}, 0

    run = runcmd([OBABEL_BIN, cif_path, '-ocan', '--separate'], timeout=OBABEL_TIMEOUT)
    counts = {}
    total = 0
    for line in (run.stdout or '').splitlines():
        # Canonical SMILES output is '<smiles>\t<title>'.
        smiles = line.split('\t')[0].strip()
        if not smiles:
            continue
        counts[smiles] = counts.get(smiles, 0) + 1
        total += 1
    return counts, total


def _split_smiles(value):
    """Flatten a SMILES value (string or list, '.'-separated) into an ordered list."""
    items = value if isinstance(value, (list, tuple)) else [value]
    result = []
    for item in items:
        for part in str(item or '').split('.'):
            part = part.strip()
            if part:
                result.append(part)
    return result


def _assign_counts(smiles_list, counts, total):
    """Map each building block to its instance count.

    A single block takes the whole file's count, because its reported SMILES may
    differ from the decomposed cluster (a bare metal versus the full metal-oxo
    node, or a charged linker versus its radical form in the CIF) -- but only
    when every fragment in the file is the same species. Otherwise the file also
    holds pieces of clusters cut by the unit cell boundary, and counting those
    yields a wrong ratio: MOF-5's nodes.cif is 8 whole [Zn]O[Zn] plus 16 stray
    [Zn], which would report 2:3 for a framework that is 1:3.

    With siblings every block has to match. Either way None is returned rather
    than a ratio that cannot be trusted.
    """
    if not smiles_list:
        return None
    if len(smiles_list) == 1:
        return [total] if total and len(counts) == 1 else None

    resolved = []
    for smiles in smiles_list:
        count = counts.get(_canonical_smiles(smiles))
        if not count:
            return None
        resolved.append(count)
    return resolved


def _component_ratios(output_path, result):
    """Node/linker stoichiometry as smallest-integer ratios.

    The final MOFid keeps only unique building blocks and drops their
    multiplicity, so this counts mofid's own decomposition output instead: 24
    nodes and 32 linkers become [3] and [4]. Aligned with smiles_nodes /
    smiles_linkers; (None, None) when it cannot be resolved for every block.
    """
    metal_oxo = os.path.join(output_path, 'MetalOxo')
    node_counts, node_total = _count_fragments(os.path.join(metal_oxo, 'nodes.cif'))
    linker_counts, linker_total = _count_fragments(os.path.join(metal_oxo, 'linkers.cif'))

    node_ratios = _assign_counts(_split_smiles(result.get('smiles_nodes')),
                                 node_counts, node_total)
    linker_ratios = _assign_counts(_split_smiles(result.get('smiles_linkers')),
                                   linker_counts, linker_total)
    if not node_ratios or not linker_ratios:
        logger.debug('mofid: no component ratios (nodes=%s, linkers=%s)',
                     node_ratios, linker_ratios)
        return None, None

    divisor = reduce(gcd, node_ratios + linker_ratios, 0)
    if divisor <= 0:
        return None, None
    return ([count // divisor for count in node_ratios],
            [count // divisor for count in linker_ratios])


class CifReader(Reader):
    """
    Reader for .cif files. Files can be Zipped
    """
    identifier = 'cif_reader'
    priority = 10
    file_prefix = '.cif'
    cif = None

    junk_size_threshold = 500

    # two or more chars in row
    header_pattern = re.compile(r'^_[A-Za-z]{2,}')
    col_header_pattern = re.compile(r'^\s+_')
    data_row_pattern = re.compile(r'^\s+[^\s_]')
    data_str_pattern = r"'[^'\\]*(?:\\.[^'\\]*)*'"
    data_number_pattern = r"-?\d+\.?\d*\(?\d*\)?"
    data_symbol_pattern = r"[A-Za-z]{1,3}\d*"
    data_pattern = re.compile(rf"{data_str_pattern}|{data_symbol_pattern}|{data_number_pattern}")

    def _commonprefix(self, a):
        prefix_len = len(a[0])
        for x in a[1:]:
            prefix_len = min(prefix_len, len(x))
            while not x.startswith(a[0][: prefix_len]):
                prefix_len -= 1

        return a[0][: prefix_len]

    def check(self):
        """
        :return: True if it fits
        """
        if self.file.suffix.lower() == '.zip' and self.file.mime_type == 'application/zip':
            with ZipFile(self.file.fp, 'r') as zip_obj:
                try:
                    file_name = next(x for x in zip_obj.namelist() if x.lower().endswith(self.file_prefix))
                    with os.path.join(tempfile.TemporaryDirectory().name, self.file.name) as zipdir:
                        os.makedirs(zipdir)
                        path_file_name = zip_obj.extract(file_name, zipdir)
                        with open(path_file_name, 'rb') as f:
                            fs = FileStorage(stream=f, filename=os.path.basename(file_name),
                                             content_type='chemical/x-cif')
                            self.file = File(fs)
                except:
                    logger.debug('result=%s', False)
                    return False

        result = self.file.suffix.lower() == self.file_prefix and self.file.mime_type == 'text/plain'
        if result:
            try:
                self.cif = cif.read_string(self.file.content)  # copy all the data from mmCIF file
            except ValueError as e:
                if str(e).endswith('expected block header (data_)'):
                    content = 'data_' + re.split('^data_', self.file.string, flags=re.M)[-1]
                    try:
                        self.cif = cif.read_string(content)  # copy all the data from mmCIF file
                    except ValueError:
                        result = False

        return result

    def _add_mofid_metadata(self, table):
        """
        Adds the MOF identifiers of this structure to a table as 'mofid.<key>'.

        Runs the mofid pipeline (mofid_wrapper), which decomposes the framework
        into nodes and linkers and matches its topology against the RCSR archive,
        then adds the CCDC deposition number and the node/linker stoichiometry.
        Optional enrichment: a missing package, a missing Java runtime or a
        pipeline error leaves the CIF conversion untouched.
        """
        if cif2mofid is None or not (self.file.string or '').strip():
            return

        try:
            with tempfile.TemporaryDirectory(prefix='mofid_') as workdir:
                # The file name becomes the ';<name>' suffix of the MOFid.
                cif_path = os.path.join(workdir, self._mofid_cif_name())
                with open(cif_path, 'w', encoding='utf-8') as file_handle:
                    file_handle.write(self.file.string)
                output_path = os.path.join(workdir, 'Output')
                result = cif2mofid(cif_path, output_path=output_path)
                # Counted while the decomposition output still exists.
                node_ratios, linker_ratios = _component_ratios(output_path, result)
        except Exception as error:  # pylint: disable=broad-exception-caught
            # Never fail a valid CIF over the optional MOF step.
            logger.warning('mofid failed for %s: %s', self.file.name, error)
            return

        for key in MOFID_RESULT_KEYS:
            self._add_mofid_value(table, key, result.get(key))

        # Not part of the mofid pipeline's own output.
        ccdc_match = CCDC_PATTERN.search(self.file.string)
        self._add_mofid_value(table, 'ccdc_number', ccdc_match.group(1) if ccdc_match else '')
        self._add_mofid_value(table, 'node_ratios', node_ratios)
        self._add_mofid_value(table, 'linker_ratios', linker_ratios)

    @staticmethod
    def _add_mofid_value(table, key, value):
        """Adds one identifier as a string; lists are joined, None becomes empty."""
        if isinstance(value, (list, tuple)):
            separator = MOFID_LIST_SEPARATOR if all(
                isinstance(item, int) for item in value) else '.'
            value = separator.join(str(item) for item in value if item not in (None, ''))
        table.add_metadata(f'{MOFID_METADATA_PREFIX}{key}',
                           '' if value is None else str(value))

    def _mofid_cif_name(self):
        """A sanitised file name, since it ends up inside the MOFid string."""
        stem = re.sub(r'[^A-Za-z0-9._-]', '_', os.path.splitext(self.file.name)[0]).strip('_')
        return f'{stem or "structure"}.cif'

    def prepare_tables(self):
        if self.cif is None:
            return []
        all_tables = []
        for block in self.cif:  # mmCIF has exactly one block
            tables = []
            all_tables.append(tables)
            meta_table = self.append_table(tables)
            junk_table_header = []
            has_junk = False

            meta_table['header'].append(f"Block_name = {block.name}")
            meta_table['metadata']["Block_name"] = block.name

            for item in block:
                if item.pair is not None:
                    if 'highest difference peak' in ''.join(item.pair).lower():
                        meta_table['header'].append(' = '.join(item.pair[:2]))
                    elif len(item.pair[1]) > self.junk_size_threshold:
                        has_junk = True
                        junk_table_header.append(' = '.join(item.pair[:2]))
                    else:
                        meta_table['header'].append(' = '.join(item.pair[:2]))
                        meta_table['metadata'][item.pair[0]] = re.sub(r"^[;\s']+|[;\s']+$", "", item.pair[1])
                elif item.loop is not None:
                    table = self.append_table(tables)
                    table.add_metadata("Block_name", block.name)
                    prefix = self._commonprefix(item.loop.tags)
                    meta_table['metadata']['Loop_name'] = prefix
                    for tag in item.loop.tags:
                        table['header'].append(tag)
                        table['columns'].append({
                            'key': str(len(table['columns']) + 1),
                            'name': tag
                        })

                    for i in range(0, len(item.loop.values), len(item.loop.tags)):
                        table['rows'].append(
                            item.loop.values[i:(i + len(item.loop.tags))])

            if has_junk:
                junk_table = self.append_table(tables)
                junk_table.add_metadata("Block_name", block.name)
                junk_table['header'] = junk_table_header

        all_tables.sort(key=lambda x: len(x), reverse=True)

        flat_tables = [
            table
            for tables in all_tables
            for table in tables
        ]

        if flat_tables:
            self._add_mofid_metadata(flat_tables[0])

        return flat_tables


Readers.instance().register(CifReader)
