import json
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL


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

    rdf_json_path = Path(__file__).parent / 'rdf_terms_info.json'
    with open(rdf_json_path, 'w') as fp:
        json.dump(terms_info, fp)
    return rdf_json_path