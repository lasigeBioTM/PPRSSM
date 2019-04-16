import os
import logging
import pickle
import atexit

import obonet
import networkx
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import sys
sys.path.append("./")
from DiShIn import ssm
ssm.semantic_base("DiShIn/hp.db", to_memory=False)

hpo_cache_file = "temp/hpo_cache.pickle"


perfect_matches, partial_matches = 0, 0

# store string-> chebi ID
if os.path.isfile(hpo_cache_file):
    logging.info("loading hpo...")
    hpo_cache = pickle.load(open(hpo_cache_file, "rb"))
    loadedchebi = True
    logging.info("loaded hpo dictionary with %s entries", str(len(hpo_cache)))
else:
    hpo_cache = {}
    loadedchebi = False
    logging.info("new hpo dictionary")


def exit_handler():
    print('Saving hpo dictionary...!')
    pickle.dump(hpo_cache, open(hpo_cache_file, "wb"))

atexit.register(exit_handler)



def load_hpo(path="http://purl.obolibrary.org/obo/hp.obo"):
    print("loading hpo graph...")
    graph = obonet.read_obo(path)
    #sys.exit()
    graph = graph.to_directed()
    is_a_graph=networkx.MultiDiGraph([(u,v,d) for u,v,d in graph.edges(data=True) if d['edgetype'] == "is_a"] )
    #print(networkx.is_directed_acyclic_graph(is_a_graph))
    id_to_name = {id_: data['name'].lower() for id_, data in graph.nodes(data=True)}
    name_to_id = {data['name'].lower(): id_ for id_, data in graph.nodes(data=True)}
    id_to_index = {e: i+1 for i, e in enumerate(graph.nodes())} # ids should start on 1 and not 0
    id_to_index[""] = 0
    synonym_to_id = {}
    alt_id_to_id = {}
    for n in graph.nodes(data=True):
        # print(n[1].get("synonym"))
        for syn in n[1].get("synonym", []):
            syn_name = syn.split('"')
            if len(syn_name) > 2:
                syn_name = syn.split('"')[1]
                synonym_to_id.setdefault(syn_name, []).append(n[0])
            #else:
            #    print("not a synonym:", syn.split('"'))
        for alt in n[1].get("alt_id", []):
            alt_id_to_id[alt] = n[0]


    #print(synonym_to_id)
    print("done.", "# of concepts", len(name_to_id), "# of synonyms", len(synonym_to_id))
    return is_a_graph, name_to_id, synonym_to_id, id_to_name, id_to_index, alt_id_to_id




def map_to_hpo(text, name_to_id, synonym_to_id):
    """
    Get best HPO name for text
    :param text: input text
    :param name_to_id:
    :param synonym_to_id:
    :return:
    """
    global hpo_cache
    #if text in name_to_id or text in synonym_to_id:
    #    drugs = [text]
    if text in hpo_cache:
        terms = hpo_cache[text]
    else:
        terms = process.extract(text.lower(), name_to_id.keys(),
                                scorer=fuzz.token_sort_ratio, limit=10)
        #print("best names of ", text, ":", drugs)
        if terms[0][1] == 100:
            terms = [terms[0]]
        if terms[0][1] < 70:
            term_syns = process.extract(text.lower(),synonym_to_id.keys(),
                                        limit=10, scorer=fuzz.token_sort_ratio)

            #print("best synonyms of ", text, ":", drug_syns)
            for term_syn in term_syns:
                if term_syn[1] > terms[0][1]:
                    terms.append(term_syn)
        hpo_cache[text] = terms
    matches = []
    for t in terms:
        #print(d)
        match = {"cid": name_to_id.get(t[0], synonym_to_id.get(t[0], ["NIL"])[0]),
                 "cname": t[0],
                 "match_score": t[1]/100}
        matches.append(match)
    #print(matches)
    return matches


