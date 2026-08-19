from collections import defaultdict

from rdflib import Graph, Namespace, Literal, RDF
import logging
from urllib.parse import quote, urlparse

from converter_app.writers.base import Writer

logger = logging.getLogger(__name__)

# Fallback for a profile that reached the writer without a rootOntology. Migration
# 20250908063445 seeds exactly this term, but a profile can still arrive without it
# (an unmigratable one, or a client POSTing a hand-built profile), and the writer must
# degrade to the generic assay rather than fail the whole conversion. The migration
# keeps its own copy on purpose: migrations are historical artefacts and must not shift
# when this default is retuned.
DEFAULT_ROOT_ONTOLOGY = {
    'description': [
        'A planned process that has the objective to produce information about a '
        'material entity (the evaluant) by examining it.'
    ],
    'id': 'obi:class:http://purl.obolibrary.org/obo/OBI_0000070',
    'iri': 'http://purl.obolibrary.org/obo/OBI_0000070',
    'label': 'assay',
    'namespace': 'http://purl.obolibrary.org/obo/',
    'obo_id': 'OBI:0000070',
    'ontology_name': 'obi',
    'ontology_prefix': 'OBI',
    'short_form': 'OBI_0000070',
    'type': 'class'
}


class RDFWriter(Writer):
    suffix = '.ttl'
    mimetype = 'application/rdf+xml'
    _namespace = 'https://chemotion.net/chemotion/#'
    _namespace_name = 'chemotion'

    def __init__(self, converter):
        super().__init__(converter)
        self._rdf_graph = Graph()
        self.namespaces = {}
        self.root_ontology = {}
        self.subjects = []
        self.predicates = []
        self.datatypes = []
        self.objects = []
        self.instances = {}

    def _check_subject(self, i, subject_id, instance_name):
        return self._check_types(i, {'id': subject_id}, 'subject') and i['subject'].get(
            'subjectInstance') == instance_name

    def _check_predicate(self, i, p):
        return self._check_types(i, p, 'predicate')

    def _check_object(self, i, p):
        return self._check_types(i, p, 'object')

    def _check_datatype(self, i, d):
        return self._check_types(i, d, 'datatype')

    def _get_ontologies(self, identifier):
        # Object (required)
        obj = identifier.get("object")
        if obj is None:
            return None, None, None

        object_ont = next(
            (p for p in self.objects if self._check_object(identifier, p)),
            None,
        )

        # Predicate (optional)
        predicate_ont = None
        if identifier.get("predicate") is not None:
            predicate_ont = next(
                (p for p in self.predicates if self._check_predicate(identifier, p)),
                None,
            )

        # Datatype (optional)
        datatype_ont = None
        if identifier.get("datatype") is not None:
            datatype_ont = next(
                (d for d in self.datatypes if self._check_datatype(identifier, d)),
                None,
            )

        return object_ont, predicate_ont, datatype_ont

    @staticmethod
    def _check_types(identifier, target, type):
        if identifier.get(type) is None:
            return False
        return identifier[type]['id'] == target['id']

    @classmethod
    def _get_type_from_namespace_and_typename(cls, namespace_object, typename):
        return getattr(namespace_object, cls._prepare_name(typename))

    @staticmethod
    def _prepare_name(name):
        temp_name = name.replace(' ', '_').replace(':', '_')
        return quote(temp_name)

    def _get_type_from_namespace_and_ontology(self, ontology):
        prepared_name = self._prepare_name(ontology['iri'].removeprefix(ontology['namespace']))
        return self._get_type_from_namespace_and_typename(self.namespaces[ontology['ontology_name']],
                                                          prepared_name)

    def _add_object(self, subject, predicate, instance_name, instance_type):
        instance_obj = self._get_type_from_namespace_and_typename(self.namespaces[self._namespace_name],
                                                                  instance_name)
        self._rdf_graph.add(
            (instance_obj, RDF.type,
             self._get_type_from_namespace_and_ontology(instance_type)))
        predicate_ont = next(p for p in self.predicates if p['id'] == predicate)
        self._rdf_graph.add(
            (subject, self._get_type_from_namespace_and_ontology(predicate_ont), instance_obj))
        return instance_obj

    def process(self):
        identifiers = self._preprocess()
        root_subject_instance = self._get_type_from_namespace_and_typename(self.namespaces[self._namespace_name],
                                                                           self._prepare_name(
                                                                               self._converter.profile.as_dict[
                                                                                   'title']))

        identifiers_without_subject = [i for i in identifiers if i.get('subject') is None]

        self._add_props_to_subject(identifiers_without_subject, root_subject_instance)

        self._rdf_graph.add(
            (root_subject_instance, RDF.type,
             self._get_type_from_namespace_and_ontology(self.root_ontology)))

        for subject_id, instance_details in self.instances.items():
            instance_ont = next((s for s in self.subjects if s['id'] == subject_id), None)
            if instance_ont is not None:
                for instance_dict in instance_details:
                    instance_obj = self._add_object(root_subject_instance,
                                                    predicate=instance_dict['predicate'],
                                                    instance_name=instance_dict['name'],
                                                    instance_type=instance_ont)

                    identifiers_without_subject = [i for i in identifiers if
                                                   self._check_subject(i, subject_id, instance_dict['name'])]

                    self._add_props_to_subject(identifiers_without_subject, instance_obj)

        for identifier in self._converter.profile.data['identifiers']:
            if identifier['optional']:
                if identifier['subject']:
                    self.subjects.append(identifier['subject'])

    def _add_props_to_subject(self, identifiers_for_subject, instance_obj):
        for i in identifiers_for_subject:
            (object_ont, predicate_ont, datatype_ont) = self._get_ontologies(i)

            if object_ont is None:
                return
            if datatype_ont:
                value_literal = Literal(i['value'],
                                        datatype=self._get_type_from_namespace_and_ontology(datatype_ont))
            else:
                value_literal = Literal(i['value'])

            if predicate_ont is not None:
                item = self._add_object(instance_obj, predicate=i.get('predicate', {}).get('id'),
                                        instance_name=f'{i['value']}_instance',
                                        instance_type=object_ont
                                        )

                temp_predicate = self._get_type_from_namespace_and_typename(self.namespaces[self._namespace_name], f'{object_ont['label'].lower()}')
                self._rdf_graph.add(
                    (item, temp_predicate, value_literal))
            else:
                self._rdf_graph.add(
                    (instance_obj, self._get_type_from_namespace_and_ontology(object_ont), value_literal))

    def _preprocess(self):
        profile = self._converter.profile.as_dict
        temp_namespaces = defaultdict(set)
        temp_namespaces[Namespace(self._namespace)].add(self._namespace_name)
        # Read defensively: these are all fields that migrations add, so a profile whose
        # migration never completed reaches this point without them. Indexing here used
        # to raise KeyError mid-conversion, which the API surfaced as a bare HTTP 500 and
        # callers reported as "conversion silently stopped working". An incomplete
        # profile now yields a thinner graph instead of no graph at all.
        root_ontology = profile.get('rootOntology')
        if not isinstance(root_ontology, dict):
            logger.warning(
                'Profile %s has no rootOntology; falling back to the generic assay term. '
                'The profile is likely mid-migration.', profile.get('id'))
            root_ontology = DEFAULT_ROOT_ONTOLOGY
        self.root_ontology = root_ontology
        self.subjects += profile.get('subjects') or []
        self.predicates += profile.get('predicates') or []
        self.datatypes += profile.get('datatypes') or []
        self.objects += profile.get('objects') or []
        self.instances.update(profile.get('subjectInstances') or {})
        identifiers = [i['identifier'] | i['result'] for i in self._converter.get_matches(rdf=True) if i['result']]

        for element in [self.root_ontology] + self.subjects + self.predicates + self.datatypes + self.objects:
            temp_namespaces[Namespace(element['namespace'])].add(element['ontology_name'])
        for (ns, objs) in temp_namespaces.items():
            if len(objs) > 1:
                path = urlparse(ns).path.strip("/")
                self._rdf_graph.bind(f"_{path.split("/")[-1]}", ns)
            else:
                self._rdf_graph.bind( next(iter(objs)), ns)
            for obj in objs:
                self.namespaces[obj] = ns
        return identifiers

    def write(self):
        return self._rdf_graph.serialize(format="turtle").encode()
