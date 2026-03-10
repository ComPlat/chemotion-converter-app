import json

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS
from converter_app.utils import get_app_root


import requests
import xml.etree.ElementTree as ET

def prepare_entry(st, ontology_prefix):
    name = st.attrib.get("name")
    ontology_prefix_upper = ontology_prefix.upper()
    if name:
        namespace = 'http://www.w3.org/2001/XMLSchema#'
        iri = f"{namespace}{name}"
        entry = {
            "id": f'{ontology_prefix_upper}:property:{iri}',
            "iri": iri,
            "ontology_name": ontology_prefix,
            "namespace": namespace,
            "ontology_prefix": ontology_prefix_upper,
            "short_form": f'{ontology_prefix_upper}_{name}',
            "description": [f"The XML Schema datatype '{name}'."],
            "label": name,
            "obo_id": f'{ontology_prefix_upper}:{name}',
            "type": "property"
        }
        return entry
    raise ValueError("No entry found")

def get_xml_property_list():
    url = "https://www.w3.org/2001/XMLSchema.xsd"
    response = requests.get(url)
    response.raise_for_status()

    # Parse XML
    root = ET.fromstring(response.content)

    # Namespace used in the XSD file
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

    ontology_prefix = "xsd"

    entries = []
    seen = set()

    # Find all simpleType and built-in types
    for st in root.findall("xs:simpleType", ns):
        try:
            entry = prepare_entry(st, ontology_prefix)
            if entry['id'] not in seen:
                seen.add(entry['id'])
                entries.append(entry)
        except ValueError:
            pass

    # Add built-in types defined as <xs:complexType> if needed
    for ct in root.findall("xs:complexType", ns):
        try:
            entry = prepare_entry(ct, ontology_prefix)
            if entry['id'] not in seen:
                seen.add(entry['id'])
                entries.append(entry)
        except ValueError:
            pass

    return entries


def refresh_rdf_summery():
    # Load RDF vocabulary
    urls = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns.rdf",
        "http://www.w3.org/2000/01/rdf-schema.rdf"
    ]

    g = Graph()
    for url in urls:
        g.parse(url, format="xml")

    def split_namespace(uri):
        uri = str(uri)
        if "#" in uri:
            return uri.rsplit("#", 1)
        else:
            return uri.rsplit("/", 1)

    terms_info = []
    seen = set()

    for s in g.subjects():
        if isinstance(s, Namespace):
            continue

        label = g.value(s, RDFS.label)
        comment = g.value(s, RDFS.comment)
        types = [str(t).split("#")[-1] for t in g.objects(s, RDF.type)]

        ns, local = split_namespace(s)
        prefix =  "rdf" if "rdf-syntax" in ns else "rdfs"
        label = str(label) if label else None
        id = f"{prefix.upper()}:property:{str(s)}"
        if id not in seen:
            info = {
                "id": id ,
                "iri": str(s),
                "label": label,
                "description": [str(comment)] if comment else [],
                "namespace": ns + ("#" if "#" in str(s) else "/"),
                "obo_id": f"{prefix.upper()}:{local}",  # only relevant for OBO ontologies
                "ontology_name": prefix,
                "ontology_prefix": prefix.upper(),
                "short_form": f"{prefix.upper()}_{local}",
                "type": types[0]
            }
            terms_info.append(info)
            seen.add(id)
    terms_info += get_xml_property_list()

    rdf_json_path = get_app_root() / 'converter_app/rdf/rdf_terms_info.json'
    with open(rdf_json_path, 'w') as fp:
        json.dump(terms_info, fp)
    return rdf_json_path