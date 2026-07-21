"""
Regression tests for the migration-resume crash (chemotion_ELN #3369 follow-up).

Real profiles were stamped ``last_migration = 20260113143334`` yet lacked fields
(``subjectInstances``, ``rootOntology``) that migrations *before* that checkpoint
add. Resuming from the checkpoint skips those field-adders, so a later migration
read the absent key and raised an *uncaught* ``KeyError`` -> HTTP 500 (which the
ELN proxy then swallowed into a silent client crash). The migrations must
tolerate the missing fields.

The second half of the file covers the follow-on bug: once the chain *does* run to
the tip, migration 20260430125545 seeds ``diff_history`` with an empty list, and
gating the history append on that list's truthiness froze the profile's version
forever (refs: #241).
"""
import copy
import tempfile

import flask
import pytest

# Importing the package registers every *_migration.py into the singleton.
import converter_app.profile_migration  # noqa: F401
from converter_app.profile_migration.utils.registration import Migrations
from converter_app.models import Profile

CHECKPOINT = '20260113143334'


def _migration(identifier):
    # Migrations register themselves on import; grab the live instance rather
    # than constructing a second one (which would raise "already registered").
    return Migrations()._registry[identifier]


@pytest.fixture(name='profiles_app')
def _profiles_app():
    # A throwaway app per test: save() writes under PROFILES_DIR, and the shared
    # test app points at the real profile fixtures.
    app = flask.Flask(__name__)
    app.config.update(SECRET_KEY='123TEST', PROFILES_DIR=tempfile.mkdtemp())
    with app.app_context():
        yield app


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


def test_empty_diff_history_still_records_first_change():
    # The regression: 20260430125545 seeds diff_history == [], and gating the
    # append on `self.data.get('diff_history')` made [] falsy -> the first entry
    # was never written, so the list could never become non-empty and the version
    # stayed put for the life of the profile.
    profile = Profile({'identifiers': [], 'tables': [], 'profile_version': '1.0', 'diff_history': []},
                      client_id='chemotion')
    origin = copy.deepcopy(profile.data)
    profile.data['identifiers'] = [{'changed': True}]

    profile.update_change_history(origin, trigger='save')

    assert profile.data['profile_version'] == '1.1'
    assert len(profile.data['diff_history']) == 1
    assert profile.data['diff_history'][0]['profile_version'] == '1.0'
    assert profile.data['diff_history'][0]['trigger'] == 'save'


def test_missing_versioning_fields_are_seeded_rather_than_raising():
    # A profile that never reached 20260430125545 has neither field; recording a
    # change must seed both instead of raising KeyError on profile_version.
    profile = Profile({'identifiers': [], 'tables': []}, client_id='chemotion')
    origin = copy.deepcopy(profile.data)
    profile.data['identifiers'] = [{'changed': True}]

    profile.update_change_history(origin, trigger='save')

    assert profile.data['profile_version'] == '1.1'
    assert len(profile.data['diff_history']) == 1


def test_unchanged_profile_does_not_bump_version():
    # The no-op path must stay a no-op: seeding is not an excuse to record.
    profile = Profile({'identifiers': [], 'tables': [], 'profile_version': '1.0', 'diff_history': []},
                      client_id='chemotion')
    origin = copy.deepcopy(profile.data)

    profile.update_change_history(origin, trigger='save')

    assert profile.data['profile_version'] == '1.0'
    assert profile.data['diff_history'] == []


def test_migrated_legacy_profile_versions_on_subsequent_saves(profiles_app):  # noqa: ARG001
    # End-to-end shape of the field report: migrate a legacy-checkpoint profile,
    # then edit and save it twice. Each save must yield a new version.
    legacy = {
        'id': '15400217-b730-47db-9d5c-a300bce7ae95',
        'last_migration': CHECKPOINT,
        'title': 'Legacy checkpoint profile',
        'converter_version': '1.9.2',
        'description': '',
        'isDisabled': False,
        'ontology': '',
        'devices': [],
        'software': [],
        'identifiers': [],
        'tables': [],
        'data': [{'metadata': {'file_name': 'x.txt'}, 'tables': [
            {'header': ['h'], 'metadata': {}, 'columns': [{'name': 'c0'}], 'rows': []},
        ]}],
        # As on disk: no profile_version / diff_history — the migration adds them.
        # deliberately NO subjectInstances / rootOntology / objects / predicates
    }
    profile = Profile(dict(legacy), client_id='chemotion', profile_id=legacy['id'])
    Migrations().migrate_profile(profile, force=False, add_history=False)

    # add_history=False, so migrating seeds the fields without recording anything.
    assert profile.data['profile_version'] == '1.0'
    assert profile.data['diff_history'] == []
    profile.save(add_to_history=False)

    # The point of the regression: each subsequent edit yields a new version.
    for expected_version, expected_len in (('1.1', 1), ('1.2', 2)):
        profile.data['title'] = f'edited for {expected_version}'
        profile.save()
        assert profile.data['profile_version'] == expected_version
        assert len(profile.data['diff_history']) == expected_len


def test_migration_changes_are_recorded_when_history_is_enabled(profiles_app):  # noqa: ARG001
    # The inverse of the test above, and the reason restore_unknown_migrations
    # works: with history on, each migration that alters the profile leaves a
    # `migration:<id>` entry behind. On an empty diff_history these were silently
    # dropped, so an unknown migration had no diff to undo.
    legacy = {
        'id': '15400217-b730-47db-9d5c-a300bce7ae95',
        'last_migration': CHECKPOINT,
        'title': 'Legacy checkpoint profile',
        'converter_version': '1.9.2',
        'description': '',
        'isDisabled': False,
        'ontology': '',
        'devices': [],
        'software': [],
        'identifiers': [],
        'tables': [],
        'data': [{'metadata': {'file_name': 'x.txt'}, 'tables': [
            {'header': ['h'], 'metadata': {}, 'columns': [{'name': 'c0'}], 'rows': []},
        ]}],
    }
    profile = Profile(dict(legacy), client_id='chemotion', profile_id=legacy['id'])
    Migrations().migrate_profile(profile, force=False, add_history=True)

    triggers = [h['trigger'] for h in profile.data['diff_history']]
    assert triggers, 'migrations must leave an undoable diff behind'
    assert all(t.startswith('migration:') for t in triggers)
    # Version advanced once per recorded migration, from the 1.0 seed.
    assert profile.data['profile_version'] == f'1.{len(triggers)}'
