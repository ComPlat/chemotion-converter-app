import uuid

from converter_app.profile_migration import ProfileMigration


def get_meta_value(profile, inputTableIndex, key):
    for data in profile['data']:
        try:
            return data['tables'][inputTableIndex]['metadata'][key]
        except IndexError:
            pass
    return ''

class ProfileMigrationScript(ProfileMigration):
    """
    Output tables need a unique table name so that they can be linked to identifiers
    """

    def up(self, profile: dict):
        """
        adds a table name  to each output table. replaces table index in identifier with new name
        """

        tables_header = [[x['name'] for x in tb['columns']] for tb in profile['data'][0]['tables']]
        for i, table in enumerate(profile['tables']):
            profile['tables'][i]['tableName'] = table.get('tableName', f'Table #{i + 1}')
            profile['tables'][i]['uuid'] = table.get('uuid', uuid.uuid4().__str__())
            for lh in table.get('table').get('loop_header', []):
                if not isinstance(lh.get('column'), str):
                    ci = int(lh.get('column').get('columnIndex'))
                    try:
                        lh['column'] = tables_header[table['inputTableIndex']][ci]
                    except IndexError:
                        lh['column'] = ''
            for lm in table.get('table').get('loop_metadata', []):

                lm['value'] = get_meta_value(profile, table['inputTableIndex'], lm['metadata'])
                if 'matchMode' not in lm:
                    if lm.get('ignoreValue'):
                        lm['matchMode'] = 'key'
                    else:
                        lm['matchMode'] = 'exact'
                    if 'ignoreValue' in lm:
                        del lm['ignoreValue']
                if 'ignore_missing_values' in lm:
                    del lm['ignore_missing_values']




        for i, identifier in enumerate(profile['identifiers']):
            if identifier['optional']:
                try:
                    t_idx_list = [int(x) for x in identifier['outputTableIndex']]
                except (ValueError, TypeError):
                    return
                identifier['outputTableIndex'] = []
                for t_idx in t_idx_list:
                    try:
                        profile['identifiers'][i]['outputTableIndex'] = [profile['tables'][t_idx]['uuid']]
                    except:
                        pass

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260506160404'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260513094819'
