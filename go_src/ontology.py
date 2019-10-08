import networkx as nx, nltk, obonet, sys
import atexit, logging, json, os, pickle

sys.path.append("\.")


def load_GO(ontology_name):
    """Loads ontology infromation from .obo file into a graph object and dicts

    :param ontology_name: (str) "GO_BP", "GO_MF", "GO_CC"
    
    :return is_graph: ontology "is-a" relationships expressed in a MultiDiGraph object (see networkx documentation)
    :return name_to_id: (dict) ontology term names (keys) and ontology ids (values)
    :return synonym_to_id: (dict) ontology synonyms (keys) and ontology ids (values)
    """
    extended_ontology_name = ""

    if ontology_name[:2] == "GO":
        ontology_path = "go-basic.obo"

        if ontology_name == "GO_BP":
            extended_ontology_name = "biological_process"
        elif ontology_name == "GO_CC":
            extended_ontology_name = "cellular_component"
        elif ontology_name == "GO_MF":
            extended_ontology_name = "molecular_function"

    else:
        raise Exception("Ontology is not valid")

    # Loading the ontology into graph object
    print("======== Loading {} into graph ========".format(ontology_name))
    graph = obonet.read_obo(ontology_path)
    graph = graph.to_directed()

    # Create mappings
    name_to_id, synonym_to_id, alt_id_to_id, edge_list = {}, {}, {}, []

    for node in graph.nodes(data=True):
        if node[1]["namespace"] == extended_ontology_name:
            node_id, node_name = node[0], node[1]["name"]
            name_to_id[node_name] = node_id

            if (
                "is_a" in node[1].keys()
            ):  # The root node of the ontology does not have is_a relationships
                for related_node in node[1]["is_a"]:
                    relationship = (node[0], related_node)
                    edge_list.append(
                        relationship
                    )  # Build the edge_list with only is_a relationships

            if "synonym" in node[1].keys():  # Check for synonyms for node
                for synonym in node[1]["synonym"]:
                    synonym_name = synonym.split('"')[1]
                    synonym_to_id[synonym_name] = node_id

            if "alt_id" in node[1].keys():
                for alternative_id in node[1]["alt_id"]:
                    alt_id_to_id[alternative_id] = node_id

    is_graph = nx.MultiDiGraph([edge for edge in edge_list])
    assert nx.is_directed_acyclic_graph(
        is_graph
    ), "The loaded ontology is not a directed acyclic graph"

    return is_graph, name_to_id, synonym_to_id


######################################################################
# Check if distance_cache_file exists; if it doesn't create new file
distance_cache_file = "temp/distance_cache.pickle"

if os.path.exists(distance_cache_file):
    logging.info("loading distances...")
    distance_cache = pickle.load(open(distance_cache_file, "rb"))
    loaded_distance = True
    logging.info(
        "loaded distances dictionary with %s entries", str(len(distance_cache))
    )

else:
    distance_cache = {}
    loaded_distance = False
    logging.info("new distances dictionary")


def exit_handler():
    print("Saving distances dictionary...!")
    pickle.dump(distance_cache, open(distance_cache_file, "wb"))


atexit.register(exit_handler)


# Get distances between ontology terms using networkx


def no_path_handler(is_graph, node_1, node_2, ontology_name):

    try:

        if ontology_name == "GO_BP":
            root_id = "GO:0008150"

        elif ontology_name == "GO_CC":
            root_id = "GO:0005575"

        elif ontology_name == "GO_MF":
            root_id = "GO:0003674"

        distance_to_root_1 = nx.shortest_path_length(
            is_graph, source=node_1, target=root_id
        )
        distance_to_root_2 = nx.shortest_path_length(
            is_graph, source=node_2, target=root_id
        )
        distance = distance_to_root_1 + distance_to_root_2

    except:
        # There is no path between the nodes; there may be a path between the nodes, but it's not an "is_a" relationship
        distance = -1

    return distance


def path_traversing_root_handler(is_graph, node_1, node_2, ontology_name):

    try:
        # Reverse the order of the nodes
        distance = nx.shortest_path_length(is_graph, source=node_2, target=node_1)

    except:
        # the path between the two terms can include the sub-ontology root node
        distance = no_path_handler(is_graph, node_1, node_2, ontology_name)

    return distance


def get_ontology_distance(is_graph, node_1, node_2, ontology_name):

    global distance_cache

    key1 = node_1 + "_" + node_2
    key2 = node_2 + "_" + node_1

    if key1 in distance_cache.keys():
        distance = distance_cache[key1]

        return distance

    elif key2 in distance_cache.keys():
        distance = distance_cache[key2]

        return distance

    else:

        try:
            distance = nx.shortest_path_length(is_graph, source=node_1, target=node_2)

        except:
            distance = path_traversing_root_handler(
                is_graph, node_1, node_2, ontology_name
            )

        key = node_1 + "_" + node_2
        distance_cache[key] = distance

        return distance


######################################################################


def get_ontology_type(entity_url, ontology_name):

    predicted_type = ""

    if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
        predicted_type = ontology_name

        return predicted_type

    else:
        raise Exception("Invalid ontology")
