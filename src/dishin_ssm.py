import pickle
import logging
import os
import atexit
import requests
import networkx as nx

# from DiShIn import ssm
import ssmpy as ssm

ssm_cache_file = "temp/ssm_cache.pickle"
from chebi_src.chebi_ssm import load_chebi

chebi_graph, name_to_id, synonym_to_id, id_to_name, id_to_index = load_chebi(
    "chebi.obo"
)
chebi_graph.to_undirected()
from hpo_src.hpo_ssm import load_hpo

hpo_graph, name_to_id, synonym_to_id, id_to_name, id_to_index, alt_id_to_id = load_hpo(
    "hp.obo"
)
hpo_graph.to_undirected()

# store string-> chebi ID
if os.path.isfile(ssm_cache_file):
    logging.info("loading ssm cache...")
    ssm_cache = pickle.load(open(ssm_cache_file, "rb"))
    loadedcache = True
    logging.info("loaded ssm dictionary with %s entries", str(len(ssm_cache)))
else:
    ssm_cache = {}
    loadedcache = False
    logging.info("new ssm dictionary")


def exit_handler():
    print("Saving ssm dictionary...!")
    print("opening pickle...")
    if loadedcache:
        new_ssm_cache = pickle.load(open(ssm_cache_file, "rb"))
        ssm_cache.update(new_ssm_cache)
    pickle.dump(ssm_cache, open(ssm_cache_file, "wb"))


atexit.register(exit_handler)


def get_n_ancestors(cid):
    global ssm_cache
    if str(cid) + "_anc" in ssm_cache:
        return ssm_cache[cid + "_anc"]
    else:
        rows = ssm.run_query(
            """
        SELECT COUNT(*)
        FROM transitive r, entry e
        WHERE r.entry2=e.id and e.name = ?
        """,
            (cid,),
        ).fetchone()
        ssm_cache[cid + "_anc"] = rows[0]
        return rows[0]


def get_n_descendants(cid):
    global ssm_cache
    if cid in ssm_cache:
        return ssm_cache[cid]
    else:
        rows = ssm.run_query(
            """
        SELECT COUNT(*)
        FROM transitive r, entry e
        WHERE r.entry1=e.id and e.name = ?
        """,
            (cid,),
        ).fetchone()
        ssm_cache[cid] = rows[0]
        return rows[0]


def get_ssm(cid1, cid2, measure="resnik_mica"):
    # e1 = ssm.get_id(cid1.replace(":", "_"))
    # e2 = ssm.get_id(cid2.replace(":", "_"))
    r = requests.get(
        "http://127.0.0.1:5000/dishin/",
        params={
            "entry1": cid1.replace(":", "_"),
            "entry2": cid2.replace(":", "_"),
            "ontology": "chebi.db",
            "measure": measure,
        },
    )
    score = float(r.text.strip().split("\t")[-1].strip())

    return score


def call_dishin_api(ontology, entry1, entry2, measure):
    base_url = "http://127.0.0.1:5000/dishin/"
    args = {
        "ontology": ontology,
        "entry1": entry1,
        "entry2": entry2,
        "measure": measure,
    }
    r = requests.get(base_url, params=args)
    return r.text


def get_dist(cid1, cid2, ontology="chebi.db", max_dist=100):
    global ssm_cache

    # print("getting dist between", cid1, cid2)
    if (cid1, cid2, "v4") in ssm_cache:
        logging.debug(
            "dist cached {} {} {} {}".format(
                cid1, cid2, ssm_cache[(cid1, cid2, "v4")], len(ssm_cache)
            )
        )
        return ssm_cache[(cid1, cid2, "v4")]
    elif (cid2, cid1, "v4") in ssm_cache:
        logging.debug(
            "dist cached {} {} {} {}".format(
                cid1, cid2, ssm_cache[(cid2, cid1, "v4")], len(ssm_cache)
            )
        )
        return ssm_cache[(cid2, cid1, "v4")]

    # e1 = ssm.get_id(cid1.replace(":", "_"))
    # e2 = ssm.get_id(cid2.replace(":", "_"))
    e1 = cid1.replace(":", "_")
    e2 = cid2.replace(":", "_")
    ca = ssm.common_ancestors(e1, e2)
    # ca = call_dishin_api(ontology, e1, e2, "commonancestors").split(",")
    # e1_ancestors = call_dishin_api(ontology, e1, "ancestors", "ancestors").split(",")
    # e2_ancestors = call_dishin_api(ontology, e2, "ancestors", "ancestors").split(",")
    # print(e1, e2, ca)
    d = len(set(e1_ancestors) ^ set(e2_ancestors))
    # d1 = len(e1_ancestors) - len(ca)
    # d2 = len(e2_ancestors) - len(ca)

    # if d1 is None:
    #    ssm_cache[(cid1, cid2)] = -1
    #    return -1
    # else:
    # ssm_cache[(cid1, cid2)] = d1 + d2
    # logging.debug("new dist {} {} {} {}".format(cid1, cid2, d1+d2, len(ssm_cache)))
    ssm_cache[(cid1, cid2, "v4")] = d
    return d


def path_traversing_root_handler(is_graph, node_1, node_2, ontology_name):
    if ontology_name == "chebi":
        root_node = "CHEBI:00000"
    elif ontology_name == "hpo":
        root_node = "HP:0000001"
    try:
        # Reverse the order of the nodes
        distance = nx.shortest_path_length(is_graph, source=node_2, target=node_1)

    except nx.exception.NetworkXNoPath:
        # the path between the two terms maybe include the sub-ontology root
        #    distance = no_path_handler(is_graph, node_1, node_2, ontology_name)
        # distance = -1
        distance = nx.shortest_path_length(is_graph, source=node_1, target=root_node)
        distance += nx.shortest_path_length(is_graph, source=node_2, target=root_node)

    return distance


def get_dist_network(cid1, cid2, ontology):
    if ontology == "hpo":
        is_graph = hpo_graph
    elif ontology == "chebi":
        is_graph = chebi_graph
        # print("CHEBI:3015" in is_graph)
    try:
        distance = nx.shortest_path_length(is_graph, source=cid1, target=cid2)

    except nx.exception.NetworkXNoPath:
        distance = path_traversing_root_handler(is_graph, cid1, cid2, ontology)
    except nx.exception.NodeNotFound:
        print(cid1, cid1 in is_graph)
        print(cid2, cid2 in is_graph)
        distance = -1

    return distance


def get_dist_direct(cid1, cid2, max_dist=100):
    global ssm_cache
    # print("getting dist between", cid1, cid2)
    if (cid1, cid2) in ssm_cache:
        # print("cached")
        return ssm_cache[(cid1, cid2)]
    # else:
    # print("newdist")
    # rows = ssm.connection.execute("""
    #    SELECT MAX(distance)
    #    FROM transitive t, entry e1, entry e2
    #     WHERE ((t.entry1=e1.id and t.entry2=e2.id) or
    #          (t.entry1=e2.id and t.entry2=e1.id))
    #           and e1.name = ? and e2.name = ?
    #    """, (cid1, cid2,)).fetchone()
    # if rows[0] is None:
    #    dist = 0
    # else:
    #    dist = rows[0]
    # if dist > 0:
    #    print(cid1, cid2, dist)
    e1 = ssm.get_id(cid1.replace(":", "_"))
    e2 = ssm.get_id(cid2.replace(":", "_"))
    # ca = ssm.common_ancestors(e1, e2)
    # print(e1, e2, ca)
    d1 = ssm.run_query(
        """
        SELECT distance
        FROM transitive t, entry e1, entry e2
         WHERE t.distance < ? and ((t.entry1=e1.id and t.entry2=e2.id) or
              (t.entry1=e2.id and t.entry2=e1.id))
               and e1.id = ? and e2.id = ?
        """,
        (max_dist, e1, e2),
    ).fetchone()
    # d2 = ssm.connection.execute("""
    #            SELECT distance
    #            FROM transitive t, entry e1, entry e2
    #             WHERE ((t.entry1=e1.id and t.entry2=e2.id) or
    #                  (t.entry1=e2.id and t.entry2=e1.id))
    #                   and e1.name = ? and e2.id = ?
    #            """, (cid2, ca[0],)).fetchone()
    # d1 = len(ssm.common_ancestors(e1, e1)) - len(ca)
    # d2 = len(ssm.common_ancestors(e2, e2)) - len(ca)

    if d1 is None:
        ssm_cache[(cid1, cid2)] = -1
        return -1
    else:
        ssm_cache[(cid1, cid2)] = d1[0]
        return d1[0]
