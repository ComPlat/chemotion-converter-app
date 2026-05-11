from converter_app.profile_migration import ProfileMigration
from converter_app.options import DATA_LOOP_CLASSES, DATA_CLASSES


def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

def get_by_path(obj, path, first=True):
    if not path:
        return obj

    key = path[0]
    rest = path[1:]

    if isinstance(obj, list) and key == -1:
        return flatten([get_by_path(item, rest, False) for item in obj])

    if first:
        return flatten([get_by_path(obj[key], rest, False)])
    return get_by_path(obj[key], rest, False)

def set_by_path(obj, path, value):
    if len(path) == 1:
        obj[path[0]] = value
        return
    elif not path:
        return

    key = path[0]
    rest = path[1:]
    set_by_path(obj[key], rest, value)




def delete_by_path(obj, path):
    if not path:
        return

    key = path[0]
    rest = path[1:]

    # wildcard: apply to all list elements
    if isinstance(obj, list) and key == -1:
        for item in obj:
            delete_by_path(item, rest)
        return

    # final step: delete target
    if len(path) == 1:
        if isinstance(obj, dict):
            del obj[key]
        return

    delete_by_path(obj[key], rest)

def compute_has_loop(table):
    if table.get('loopType') == 'all':
        return table.get('matchTables')
    loop_header = table['table'].get('loop_header')
    loop_metadata = table['table'].get('loop_metadata')
    loop_theader = table['table'].get('loop_theader')
    return any(x for x in [loop_header, loop_metadata, loop_theader])

class ProfileMigrationScript(ProfileMigration):
    """
    Extents identifier with output options
    """

    def up(self, profile: dict):
        """

        Adds isDatasetOutput {bool}
        Adds isDatatableOutput {bool}
        Adds isRdfOutput {bool}
        """
        for i, identifier in enumerate(profile['identifiers']):
            if identifier['optional']:
                profile['identifiers'][i]['isDatasetOutput'] = identifier.get('isDatasetOutput', True)
                profile['identifiers'][i]['isDatatableOutput'] = identifier.get('isDatatableOutput', False)
                profile['identifiers'][i]['isLoobDatatableOutput'] = identifier.get('isLoobDatatableOutput', True)
                profile['identifiers'][i]['isRdfOutput'] = identifier.get('isRdfOutput', False)
                profile['identifiers'][i]['outputDatatableKey'] = identifier.get('outputDatatableKey', identifier.get('outputKey', ''))
                if not isinstance(identifier['outputTableIndex'], list):
                    profile['identifiers'][i]['outputTableIndex'] = [identifier['outputTableIndex']]

        for i, table in enumerate(profile['tables']):
            x_in_z_p = ['table', 'xColumn', 'tableIndex']
            y_in_z_p = ['table', 'yColumn', 'tableIndex']
            loop_metadata_p = ['table', 'loop_metadata', -1, 'table']
            loop_theader_p = ['table', 'loop_theader', -1, 'table']
            loop_header_p = ['table', 'loop_header', -1, 'column', 'tableIndex']
            values = list()
            for json_path in [x_in_z_p, y_in_z_p, loop_metadata_p, loop_theader_p, loop_header_p]:
                try:
                    for val in get_by_path(table, json_path):
                        values.append(int(val))
                    delete_by_path(table, json_path)
                except:
                    pass


            if 'inputTableIndex' not in profile['tables'][i]:
                profile['tables'][i]['inputTableIndex'] = values[0]  if len(values) > 0 else profile['tables'][i].get('inputTableIndex', 0)
            loop_metadata_value_p = ['table', 'loop_metadata']
            try:
                for idx, val in enumerate(get_by_path(table, loop_metadata_value_p + [-1, 'value'])):
                    set_by_path(table, loop_metadata_value_p + [idx, 'metadata'], val)
            except:
                pass
            data_class = profile['tables'][i]['header'].get('DATA CLASS')
            lot = profile['tables'][i].get('loopOutput')
            if data_class == 'NTUPLES':
                profile['tables'][i]['loopOutput'] = DATA_LOOP_CLASSES[1]
                profile['tables'][i]['header']['DATA CLASS'] = DATA_CLASSES[0]
                profile['tables'][i]['nTuplePageHeader'] = profile['tables'][i]['header']['NTUPLES_PAGE_HEADER']
                del profile['tables'][i]['header']['NTUPLES_PAGE_HEADER']
                del profile['tables'][i]['header']['NTUPLES_ID']

            lt = table.get('loopType')
            if lt not in ['none', 'condition']:
                if compute_has_loop(table):
                    profile['tables'][i]['loopType'] = 'all' if table['loopType'] == 'all' else 'condition'
                else:
                    profile['tables'][i]['loopType'] = 'none'

            elif lot is None:
                profile['tables'][i]['loopOutput'] = DATA_LOOP_CLASSES[0]


    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260430125545'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260506160404'