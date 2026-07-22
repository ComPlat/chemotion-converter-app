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

The third part covers what tolerating the missing fields did *not* fix: the profile
came out the far end of the chain still missing them, stamped at the tip and so
never revisited, and the conversion blew up later in the RDF writer instead. The
runner now treats the checkpoint as a claim and the schema as the ground truth,
replaying the chain from the root when the two disagree.
"""
import copy
import tempfile
from types import SimpleNamespace

import flask
import pytest

# Importing the package registers every *_migration.py into the singleton.
import converter_app.profile_migration  # noqa: F401
from converter_app.profile_migration.utils.registration import Migrations
from converter_app.models import Profile
from converter_app.validation import profile_validation_errors
from converter_app.writers.rdf import RDFWriter, DEFAULT_ROOT_ONTOLOGY

CHECKPOINT = '20260113143334'

# Fields that migrations add and that the real legacy profiles lack despite being
# stamped past the migrations that add them.
MIGRATION_ADDED_FIELDS = (
    'subjectInstances', 'rootOntology', 'subjects', 'predicates', 'datatypes',
    'objects', 'reactionVariations',
)


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


# --- self-healing of an untrustworthy checkpoint ------------------------------


def _valid_profile(**overrides):
    """A profile shaped the way the tip of the migration chain leaves one: schema-valid."""
    profile = {
        'id': '15400217-b730-47db-9d5c-a300bce7ae95',
        'last_migration': Migrations().last,
        'title': 'Tip profile',
        'description': '',
        'converter_version': '1.9.2',
        'profile_version': '1.0',
        'isDisabled': False,
        'ontology': '',
        'devices': [],
        'software': [],
        'tables': [],
        'identifiers': [],
        'diff_history': [],
        'subjectInstances': {},
        'subjects': [],
        'predicates': [],
        'datatypes': [],
        'objects': [],
        'reactionVariations': {'elements': [], 'identifiers': []},
        'data': [{'metadata': {'file_name': 'x.txt'}, 'tables': [
            {'header': ['h'], 'metadata': {}, 'rows': [],
             'columns': [{'name': 'c0', 'key': '0'}]},
        ]}],
    }
    profile.update(overrides)
    return profile


def _legacy_checkpoint_profile(**overrides):
    """The real failure shape: stamped past the field-adders, without their fields."""
    profile = _valid_profile(last_migration=CHECKPOINT, **overrides)
    for field in MIGRATION_ADDED_FIELDS:
        profile.pop(field, None)
    return profile


def test_fixture_matches_the_real_failure_shape():
    # Guards the tests below: the fixture is only meaningful while it reproduces the
    # bug, i.e. is invalid *and* checkpointed past the migrations that would fix it.
    assert profile_validation_errors(_valid_profile()) == set()
    assert profile_validation_errors(_legacy_checkpoint_profile()) != set()


def test_legacy_checkpoint_profile_is_repaired_to_validity():
    # The point of the fix: a plain resume (no force) must not just avoid crashing,
    # it must leave a valid profile behind.
    profile = Profile(_legacy_checkpoint_profile(), client_id='chemotion')

    applied = Migrations().migrate_profile(profile, force=False, add_history=False)

    assert applied, 'the repair must report back so the caller persists it'
    assert profile_validation_errors(profile.data) == set()
    assert isinstance(profile.data['rootOntology'], dict)
    assert profile.data['last_migration'] == Migrations().last


def test_repaired_profile_is_stable_on_a_second_pass():
    # Every boot runs the migration, so the repair has to be idempotent: the second
    # pass must find nothing to do rather than replaying the chain forever.
    profile = Profile(_legacy_checkpoint_profile(), client_id='chemotion')
    Migrations().migrate_profile(profile, force=False, add_history=False)
    repaired = copy.deepcopy(profile.data)

    assert Migrations().migrate_profile(profile, force=False, add_history=False) is False
    assert profile.data == repaired


def test_valid_profile_at_the_tip_is_left_untouched():
    # The repair is only for profiles that fail the schema; a healthy one must not pay
    # the cost of a replay, nor collect spurious history.
    profile = Profile(_valid_profile(), client_id='chemotion')
    before = copy.deepcopy(profile.data)

    assert Migrations().migrate_profile(profile, force=False, add_history=True) is False
    assert profile.data == before


def test_repair_restores_fields_despite_an_unrelated_defect():
    # A real profile carried a table header of nulls, which no migration claims to fix.
    # Demanding full validity would discard a replay that did restore the missing
    # fields, so the profile would stay unconvertible over an unrelated flaw.
    broken = _legacy_checkpoint_profile()
    broken['data'][0]['tables'][0]['header'] = [None, None]
    profile = Profile(broken, client_id='chemotion')

    applied = Migrations().migrate_profile(profile, force=False, add_history=False)

    assert applied
    assert isinstance(profile.data['rootOntology'], dict)
    assert 'subjectInstances' in profile.data
    # The unrelated defect is still reported rather than silently papered over.
    assert profile_validation_errors(profile.data)


def test_repair_is_abandoned_when_the_replay_would_make_things_worse(monkeypatch):
    # The safety guarantee: a replay that introduces a *new* violation is discarded.
    # What survives is the ordinary resume, which is legitimate work -- only the
    # repair's own replay is rolled back.
    profile = Profile(_legacy_checkpoint_profile(), client_id='chemotion')
    original = Migrations._up_migration

    def corrupt(self, last_migration, prof, add_history=True):
        result = original(self, last_migration, prof, add_history)
        if last_migration == '':          # only the replay the repair performs
            prof.data.pop('title', None)  # a required field the original had
        return result

    monkeypatch.setattr(Migrations, '_up_migration', corrupt)

    # Still True: the resume applied migrations, so the caller must persist them.
    assert Migrations().migrate_profile(profile, force=False, add_history=False) is True
    assert 'title' in profile.data, 'the corrupting replay must have been rolled back'
    # And the replay was discarded wholesale, not cherry-picked: the fields it would
    # have restored are absent, exactly as they were before the repair was attempted.
    assert 'rootOntology' not in profile.data


# --- the writer must not be the place an incomplete profile is discovered -----


def _rdf_writer_for(profile_data):
    converter = SimpleNamespace(
        tables=[],
        profile=SimpleNamespace(as_dict=profile_data),
        get_matches=lambda rdf=False: [],
    )
    return RDFWriter(converter)


def test_rdf_writer_falls_back_when_root_ontology_is_missing():
    # rootOntology is not in the schema's required list, so even a *valid* profile can
    # reach the writer without one. Indexing it raised KeyError -> HTTP 500, which the
    # ELN recorded as a failed conversion with no clue why.
    writer = _rdf_writer_for(_valid_profile())  # valid, yet has no rootOntology

    writer._preprocess()

    assert writer.root_ontology == DEFAULT_ROOT_ONTOLOGY


def test_rdf_writer_tolerates_a_wholly_unmigrated_profile():
    # The worst case: none of the migration-added fields are present.
    bare = _legacy_checkpoint_profile()
    writer = _rdf_writer_for(bare)

    writer._preprocess()  # must not raise

    assert writer.subjects == []
    assert writer.instances == {}
