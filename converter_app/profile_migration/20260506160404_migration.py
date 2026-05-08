from converter_app.profile_migration import ProfileMigration

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

            profile['tables'][i]['inputTableIndex'] = values[0]  if len(values) > 0 else profile['tables'][i].get('inputTableIndex', 0)


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