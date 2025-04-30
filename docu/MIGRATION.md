# Profile Versioning

ChemConverter offers a profile migration tool for managing the versions 
of the profiles. The tool includes the creation of new migration scripts 
as well as the maintenance and execution of the migration. Both the 
creation of the scripts and the migration can be executed via a 
command line interface (CLI)

However, the migration is also performed automatically each time the Flask server
is started. When creating/updating a Profile, either via “Create new profile”
or “Import Profile”, the newly created script is also migrated automatically.

## The Migration CLI

To execute all migrations cd into the project and run:

```shell
python -m converter_app migrate [-f]
```

You can add _-f_ or _--force_ to force all migration scripts for all profiles. 
To clarify, it disregards the "_last_migration_" flag within the Profiles.

To create a new migration script run:

```shell
python -m converter_app new_migration
```
This action generates a new migration Python script in the _converter_app/profile_migration_ folder. It is essential to work only in the method _up_.
It is possible to modify all values in the profile; however, the _id_ is read-only.

> [!TIP]
> Please verify whether the change needs to be implemented. 
> If the script is applied again, it is expected to have no effect.

```python
from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    ToDo: Add a comment
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        # ToDo: Updated the profile
        raise NotImplementedError()

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20250429151003'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20250430101358'
```