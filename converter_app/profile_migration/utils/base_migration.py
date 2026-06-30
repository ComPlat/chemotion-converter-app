from abc import ABC, abstractmethod

from converter_app.profile_migration.utils.registration import Migrations


class ProfileMigration(ABC):

    def __init__(self):
        Migrations().register(self)


    @property
    @abstractmethod
    def identifier(self) -> str:
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """
        ...

    @abstractmethod
    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """
        ...

    @abstractmethod
    def up(self, profile: dict):
        """
        Updates the profile.
        """
        ...