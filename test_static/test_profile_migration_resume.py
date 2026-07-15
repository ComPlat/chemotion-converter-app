"""
Regression tests for the migration-resume crash (chemotion_ELN #3369 follow-up).

Real profiles were stamped ``last_migration = 20260113143334`` yet lacked fields
(``subjectInstances``, ``rootOntology``) that migrations *before* that checkpoint
add. Resuming from the checkpoint skips those field-adders, so a later migration
read the absent key and raised an *uncaught* ``KeyError`` -> HTTP 500 (which the
ELN proxy then swallowed into a silent client crash). The migrations must
tolerate the missing fields.
"""
# Importing the package registers every *_migration.py into the singleton.
import converter_app.profile_migration  # noqa: F401
from converter_app.profile_migration.utils.registration import Migrations
from converter_app.models import Profile

CHECKPOINT = '20260113143334'


def _migration(identifier):
    # Migrations register themselves on import; grab the live instance rather
    # than constructing a second one (which would raise "already registered").
    return Migrations()._registry[identifier]


def test_object_ontology_migration_tolerates_missing_subject_instances():
    # 20260319060352 used to do profile['subjectInstances'].values() unguarded.
    profile = {'identifiers': [], 'predicates': []}  # no subjectInstances, no objects
    _migration('20260319060352').up(profile)
    assert profile['objects'] == []
    assert profile['predicates'] == []


def test_object_ontology_migration_tolerates_missing_identifiers():
    profile = {'subjectInstances': {}}  # no identifiers
    _migration('20260319060352').up(profile)
    assert profile['objects'] == []


def test_root_ontology_migration_tolerates_missing_root_ontology():
    # 20260323144702 used to do profile['rootOntology']['iri'] unguarded.
    profile = {}
    _migration('20260323144702').up(profile)  # must not raise
    assert 'rootOntology' not in profile


def test_migrate_profile_from_legacy_checkpoint_does_not_raise():
    # Mirrors the real data: checkpointed past the field-adders but missing the
    # fields, so a plain resume must not blow up on the way to the tip.
    legacy = {
        'id': '15400217-b730-47db-9d5c-a300bce7ae95',
        'last_migration': CHECKPOINT,
        'title': 'Legacy checkpoint profile',
        'converter_version': '1.9.2',
        'profile_version': '1.0',
        'description': '',
        'isDisabled': False,
        'ontology': '',
        'devices': [],
        'software': [],
        'diff_history': [],
        'identifiers': [],
        'tables': [],
        'data': [{'metadata': {'file_name': 'x.txt'}, 'tables': [
            {'header': ['h'], 'metadata': {}, 'columns': [{'name': 'c0'}], 'rows': []},
        ]}],
        # deliberately NO subjectInstances / rootOntology / objects / predicates
    }
    profile = Profile(dict(legacy), client_id='chemotion')
    # Must not raise (previously KeyError: 'subjectInstances').
    Migrations().migrate_profile(profile, force=False, add_history=False)
    assert profile.data.get('last_migration') == Migrations().last
