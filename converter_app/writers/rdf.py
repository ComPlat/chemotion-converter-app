from rdflib import Graph, Namespace, Literal, RDF, XSD
import logging
from urllib.parse import quote

from converter_app.writers.base import Writer

logger = logging.getLogger(__name__)


class RDFWriter(Writer):
    suffix = '.ttl'
    mimetype = 'application/rdf+xml'
    _namespace = 'https://chemotion.net/chemotion/#'
    _namespace_name = 'chemotion'

    def __init__(self, converter):
        super().__init__(converter)
        self._g = Graph()

    def _check_subject(self, i, subject_id, instance_name):
        return self._check_types(i, {'id': subject_id}, 'subject') and i['subject'].get('subjectInstance') == instance_name

    def _check_predicate(self, i, p):
        return self._check_types(i, p, 'predicate')

    def _check_datatype(self, i, d):
        return self._check_types(i, d, 'datatype')

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
        return quote(name.replace(' ', '_').replace(':', '_'))

    def _get_type_from_namespace_and_ontology(self, namespace_objects, ontology):
        return self._get_type_from_namespace_and_typename(namespace_objects[ontology['namespace']],
                                                          ontology['iri'].removeprefix(ontology['namespace']))

    def process(self):
        (root_ontology, subjects, predicates, datatypes, instances, namespaces, identifiers) = self._preprocess()

        namespace_objects = {}
        for ns in namespaces:
            ns_obj = Namespace(ns[0])
            self._g.bind(ns[1], ns_obj)
            namespace_objects[ns[0]] = ns_obj

        root_instance = self._get_type_from_namespace_and_typename(namespace_objects[self._namespace], self._prepare_name(self._converter.profile.as_dict['title']))

        identifiers_for_subject = [i for i in identifiers if i.get('subject') is None]

        self._add_props_to_subject(identifiers_for_subject, root_instance, namespace_objects,
                                   datatypes, predicates)

        self._g.add(
            (root_instance, RDF.type, self._get_type_from_namespace_and_ontology(namespace_objects, root_ontology)))

        for subject_id, instance_details in instances.items():
            instance_ont = next((s for s in subjects if s['id'] == subject_id), None)
            if instance_ont is not None:
                for instance_dict in instance_details:
                    instance_obj = self._get_type_from_namespace_and_typename(namespace_objects[self._namespace],
                                                                              instance_dict['name'])
                    self._g.add(
                        (instance_obj, RDF.type,
                         self._get_type_from_namespace_and_ontology(namespace_objects, instance_ont)))
                    predicate_ont = next(p for p in predicates if p['id'] == instance_dict['predicate'])
                    self._g.add(
                        (root_instance, self._get_type_from_namespace_and_ontology(namespace_objects, predicate_ont),
                         instance_obj))

                    identifiers_for_subject = [i for i in identifiers if self._check_subject(i, subject_id, instance_dict['name'])]

                    self._add_props_to_subject(identifiers_for_subject, instance_obj, namespace_objects,
                                               datatypes, predicates)

        for identifier in self._converter.profile.data['identifiers']:
            if identifier['optional']:
                if identifier['predicate']:
                    pass
                if identifier['subject']:
                    subjects.append(identifier['subject'])

    def _add_props_to_subject(self, identifiers_for_subject, instance_obj, namespace_objects, datatypes, predicates):
        for i in identifiers_for_subject:
            predicate_ont = next((p for p in predicates if self._check_predicate(i, p)), None)
            if predicate_ont is not None:
                if i.get('datatype') is not None:
                    datatype_ont = next((d for d in datatypes if self._check_datatype(i, d)))
                    object = Literal(i['value'],
                                     datatype=self._get_type_from_namespace_and_ontology(namespace_objects,
                                                                                         datatype_ont))
                else:
                    object = Literal(i['value'], datatype=XSD.string)
                self._g.add(
                    (instance_obj, self._get_type_from_namespace_and_ontology(namespace_objects, predicate_ont),
                     object))

    def _preprocess(self):
        namespaces = {(self._namespace, self._namespace_name)}
        profile = self._converter.profile.as_dict
        root_ontology = profile['rootOntology']
        subjects = profile['subjects']
        predicates = profile['predicates']
        datatypes = profile['datatypes']
        instances = profile['subjectInstances']
        identifiers = [i['identifier'] | i['result'] for i in self._converter.matches]

        for element in [root_ontology] + subjects + predicates + datatypes:
            namespaces.add((element['namespace'], element['ontology_name']))

        return root_ontology, subjects, predicates, datatypes, instances, namespaces, identifiers

    def write(self):
        return self._g.serialize(format="turtle")
