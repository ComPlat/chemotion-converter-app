from rdflib import Graph, Namespace, Literal, RDF, XSD
import logging
from urllib.parse import quote

from converter_app.writers.base import Writer

logger = logging.getLogger(__name__)

default_value_predicate = {
    "description": [
        "Idiomatic property used for structured values."
    ],
    "id": "RDF:property:http://www.w3.org/1999/02/22-rdf-syntax-ns#value",
    "iri": "http://www.w3.org/1999/02/22-rdf-syntax-ns#value",
    "label": "value",
    "namespace": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "obo_id": "RDF:value",
    "ontology_name": "rdf",
    "ontology_prefix": "RDF",
    "short_form": "RDF_value",
    "type": "Property"
}


class RDFWriter(Writer):
    suffix = '.ttl'
    mimetype = 'application/rdf+xml'
    _namespace = 'https://chemotion.net/chemotion/#'
    _namespace_name = 'chemotion'

    def __init__(self, converter):
        super().__init__(converter)
        self._rdf_graph = Graph()
        self.namespaces = set()
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

    def _add_object(self, subject, predicate, instance_name, instance_type, namespace_objects):
        instance_obj = self._get_type_from_namespace_and_typename(namespace_objects[self._namespace],
                                                                  instance_name)
        self._rdf_graph.add(
            (instance_obj, RDF.type,
             self._get_type_from_namespace_and_ontology(namespace_objects, instance_type)))
        predicate_ont = next(p for p in self.predicates if p['id'] == predicate)
        self._rdf_graph.add(
            (subject, self._get_type_from_namespace_and_ontology(namespace_objects, predicate_ont),
             instance_obj))
        return instance_obj

    def process(self):
        identifiers = self._preprocess()

        namespace_objects = {}
        for ns in self.namespaces:
            ns_obj = Namespace(ns[0])
            self._rdf_graph.bind(ns[1], ns_obj)
            namespace_objects[ns[0]] = ns_obj

        root_subject_instance = self._get_type_from_namespace_and_typename(namespace_objects[self._namespace],
                                                                           self._prepare_name(
                                                                               self._converter.profile.as_dict[
                                                                                   'title']))

        identifiers_without_subject = [i for i in identifiers if i.get('subject') is None]

        self._add_props_to_subject(identifiers_without_subject, root_subject_instance, namespace_objects)

        self._rdf_graph.add(
            (root_subject_instance, RDF.type,
             self._get_type_from_namespace_and_ontology(namespace_objects, self.root_ontology)))

        for subject_id, instance_details in self.instances.items():
            instance_ont = next((s for s in self.subjects if s['id'] == subject_id), None)
            if instance_ont is not None:
                for instance_dict in instance_details:
                    instance_obj = self._add_object(root_subject_instance,
                                     predicate=instance_dict['predicate'],
                                     instance_name=instance_dict['name'],
                                     instance_type=instance_ont,
                                     namespace_objects=namespace_objects)

                    identifiers_without_subject = [i for i in identifiers if
                                                   self._check_subject(i, subject_id, instance_dict['name'])]

                    self._add_props_to_subject(identifiers_without_subject, instance_obj, namespace_objects)

        for identifier in self._converter.profile.data['identifiers']:
            if identifier['optional']:
                if identifier['subject']:
                    self.subjects.append(identifier['subject'])

    def _add_props_to_subject(self, identifiers_for_subject, instance_obj, namespace_objects):
        for i in identifiers_for_subject:
            predicate_ont = next((p for p in self.predicates if self._check_predicate(i, p)), None)
            object_out = next((p for p in self.objects if self._check_object(i, p)), None)

            if object_out is None:
                return
            if i.get('datatype') is not None:
                datatype_ont = next((d for d in self.datatypes if self._check_datatype(i, d)))
                value_literal = Literal(i['value'],
                                 datatype=self._get_type_from_namespace_and_ontology(namespace_objects,
                                                                                     datatype_ont))
            else:
                value_literal = Literal(i['value'])

            if predicate_ont is not None:
                item = self._add_object(instance_obj, predicate=i.get('predicate', {}).get('id'), instance_name=f'{object_out['label']}_instance', instance_type=object_out, namespace_objects=namespace_objects)


                self._rdf_graph.add(
                    (item, self._get_type_from_namespace_and_ontology(namespace_objects, default_value_predicate),
                     value_literal))
            else:
                self._rdf_graph.add(
                    (instance_obj, self._get_type_from_namespace_and_ontology(namespace_objects, object_out),
                     value_literal))

    def _preprocess(self):
        profile = self._converter.profile.as_dict
        self.namespaces = {(self._namespace, self._namespace_name)}
        self.root_ontology = profile['rootOntology']
        self.subjects += profile['subjects']
        self.predicates += profile['predicates']
        self.datatypes += profile['datatypes']
        self.objects += profile['objects']
        self.instances.update(profile['subjectInstances'])
        identifiers = [i['identifier'] | i['result'] for i in self._converter.matches if i['result']]
        if any(x.get('predicate', False) for x in identifiers):
            self.predicates.append(default_value_predicate)
        for element in [self.root_ontology] + self.subjects + self.predicates + self.datatypes + self.objects:
            self.namespaces.add((element['namespace'], element['ontology_name']))

        return identifiers

    def write(self):
        return self._rdf_graph.serialize(format="turtle").encode()
