import os
import logging
import pickle
import atexit

import obonet
import networkx
import sys
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import xml.etree.ElementTree as ET

# sys.path.append("./")
import ssmpy as ssm

ssm.semantic_base("chebi.db")  # , to_memory=False)

chebi_cache_file = "temp/chebi_cache.pickle"

perfect_matches, partial_matches = 0, 0

chebi_api_base = "https://www.ebi.ac.uk/webservices/chebi/2.0/test/getLiteEntity"


# store string-> chebi ID
if os.path.isfile(chebi_cache_file):
    logging.info("loading chebi...")
    chebi_cache = pickle.load(open(chebi_cache_file, "rb"))
    loadedchebi = True
    logging.info("loaded chebi dictionary with %s entries", str(len(chebi_cache)))
    if "dbpedia" not in chebi_cache:
        chebi_cache["dbpedia"] = {}
    if "fuzzyratio" not in chebi_cache:
        chebi_cache["fuzzyratio"] = {}
else:
    chebi_cache = {}
    chebi_cache["dbpedia"] = {}
    chebi_cache["fuzzyratio"] = {}
    loadedchebi = False
    logging.info("new chebi dictionary")


def exit_handler():
    print("Saving chebi dictionary...!")
    pickle.dump(chebi_cache, open(chebi_cache_file, "wb"))


atexit.register(exit_handler)


def map_to_chebi_mer(text):
    global chebi_cache
    # print(text)
    args = ["./MER/link_entities.sh", "./MER/data/chebi.txt", text]
    # mer1 = Popen(["echo", text], stdout=PIPE)
    # print(mer1.stdout)
    mer = Popen(" ".join(args), stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    mer_result = mer.communicate()
    # mer1.wait()
    # mer_result = mer2.communicate(text)
    # mer_result = mer_result[0]
    # print(mer_result)
    # mer_result = mer.stdout
    chebi_ids = mer_result.split("\n")
    chebi_ids = [x.split("\t")[0].split("/")[-1] for x in chebi_ids]
    # print(chebi_ids)
    return chebi_ids


chemical_entity = "CHEBI:24431"
role = "CHEBI:50906"
subatomic_particle = "CHEBI:36342"
application = "CHEBI:33232"
root_concept = "CHEBI:00000"


def load_chebi(path="ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo"):
    print("loading chebi...")
    # graph = obonet.read_obo("data/chebi.obo")
    graph = obonet.read_obo(path)
    graph.add_node(root_concept, name="ROOT")
    graph.add_edge(chemical_entity, root_concept, edgetype="is_a")
    graph.add_edge(role, root_concept, edgetype="is_a")
    graph.add_edge(subatomic_particle, root_concept, edgetype="is_a")
    graph.add_edge(application, root_concept, edgetype="is_a")
    # print([dir(d) for u,v,d in graph.edges(data=True)])
    # sys.exit()
    graph = graph.to_directed()
    is_a_graph = networkx.MultiDiGraph(
        [(u, v, d) for u, v, d in graph.edges(data=True) if d["edgetype"] == "is_a"]
    )
    # print(networkx.is_directed_acyclic_graph(is_a_graph))
    id_to_name = {id_: data["name"] for id_, data in graph.nodes(data=True)}
    name_to_id = {data["name"]: id_ for id_, data in graph.nodes(data=True)}
    id_to_index = {
        e: i + 1 for i, e in enumerate(graph.nodes())
    }  # ids should start on 1 and not 0
    id_to_index[""] = 0
    synonym_to_id = {}
    for n in graph.nodes(data=True):
        # print(n[1].get("synonym"))
        for syn in n[1].get("synonym", []):
            syn_name = syn.split('"')
            if len(syn_name) > 2:
                syn_name = syn.split('"')[1]
                synonym_to_id.setdefault(syn_name, []).append(n[0])
            # else:
            # print("not a synonym:", syn.split('"'))

    # print(synonym_to_id)
    print("done.", len(name_to_id), len(synonym_to_id))
    return is_a_graph, name_to_id, synonym_to_id, id_to_name, id_to_index


def map_to_chebi(text, name_to_id, synonym_to_id):
    """
    Get best ChEBI name for text
    :param text: input text
    :param name_to_id:
    :param synonym_to_id:
    :return:
    """
    # if text in name_to_id or text in synonym_to_id:
    #    drugs = [text]
    if text.endswith("s") and text[:-1] in chebi_cache["fuzzyratio"]:
        # print("plural: ", text)
        drugs = chebi_cache["fuzzyratio"][text[:-1]]
    elif text in chebi_cache["fuzzyratio"]:
        drugs = chebi_cache["fuzzyratio"][text]

    else:
        drugs = process.extract(
            text, name_to_id.keys()
        )  # , scorer=fuzz.token_sort_ratio)
        # print("best names of ", text, ":", drugs)
        if drugs[0][1] == 100:
            drugs = [drugs[0]]
        if drugs[0][1] < 70:
            drug_syns = process.extract(
                text, synonym_to_id.keys(), limit=10
            )  # , scorer=fuzz.token_sort_ratio)

            # print("best synonyms of ", text, ":", drug_syns)
            for drug_syn in drug_syns:
                if drug_syn[1] > drugs[0][1]:
                    drugs.append(drug_syn)
        chebi_cache["fuzzyratio"][text] = drugs
    matches = []
    for d in drugs:
        # print(d)
        match = {
            "cid": name_to_id.get(d[0], "NIL"),
            "cname": d[0],
            "match_score": d[1] / 100,
        }
        matches.append(match)
    # print(matches)
    # if text.startswith("tocopherols"):
    #    print(text, chebi_cache[text], chebi_cache[text[:-1]])
    #    print(matches)
    #    sys.exit()
    return matches


def map_to_chebi_api(text):
    ns = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "a": "https://www.ebi.ac.uk/webservices/chebi",
    }
    if text in chebi_cache:
        drugs = chebi_cache[text]
        # print("from cache", text, chebi_cache[text])
    else:
        matches = []
        payload = {
            "search": text,
            "searchCategory": "CHEBI+NAME",
            "maximumResults": 20,
            "starsCategory": "ALL",
        }
        r = requests.get(chebi_api_base, params=payload)
        results = ET.fromstring(r.text)
        for r in results.findall(".//a:ListElement", ns):
            # print(r)
            match = {
                "cid": r.find("a:chebiId", ns).text,
                "cname": r.find("a:chebiAsciiName", ns).text,
                "match_score": float(r.find("a:searchScore", ns).text),
            }
            matches.append(match)
        chebi_cache[text] = matches[:]
        drugs = matches
    # print(text, drugs)
    return drugs


def get_disambiguation_pages(uri):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(
        """
                    PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dbr: <http://dbpedia.org/resource/>
                PREFIX dbp: <http://dbpedia.org/property/>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?d
                WHERE {{ ?page dbo:wikiPageDisambiguates ?d .
                 FILTER (?page in (<{}>)) }}""".format(
            uri
        )
    )
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    print("disambiguation results", results)
    urls = [p["d"]["value"] for p in results["results"]["bindings"]]
    return urls


def get_chebi_from_wikipedia(matches):
    chebi_ids = []
    for m in matches:
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(
            """
                            PREFIX dbo: <http://dbpedia.org/ontology/>
                        PREFIX dbr: <http://dbpedia.org/resource/>
                        PREFIX dbp: <http://dbpedia.org/property/>
                        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
                        SELECT ?d ?l
                        WHERE {{ ?page dbp:chebi|dbo:chEBI ?d .
                                 ?page rdfs:label ?l .
                        FILTER (lang(?l) = 'en')
                         FILTER (?page in (<{}>))}}""".format(
                m
            )
        )
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        print(m, "chebi query results", results)
        # for p in results["results"]["bindings"]:
        #    print(p['d']['value'])
        for b in results["results"]["bindings"]:
            match = {
                "cid": "CHEBI:" + b["d"]["value"],
                "cname": b["l"]["value"],
                "match_score": 1,
            }
            chebi_ids.append(match)
    return chebi_ids


def get_best_chebi_id(chebi_id):
    m = map_to_chebi_api(chebi_id)
    if len(m) > 1:
        print("multiple matches:", chebi_id, m)
    if len(m) == 0:
        print("id not found:", chebi_id)
        # sys.exit()
        return chebi_id
    # print(m)
    new_chebi_id = m[0]["cid"]
    # if new_chebi_id != chebi_id:
    # print("new chebi id", chebi_id, "->", new_chebi_id)
    return new_chebi_id


if __name__ == "__main__":
    entities = ["Paracetamol", "Caffeine", "oxygen", "Panthenol"]
    for e in entities:
        map_to_dbpedia(e)
