from ontology import get_ontology_distance
from map_to_ontology import map_to_GO
from strings import entity_string, candidate_string
import networkx as nx, sys
sys.path.append("./")


def structure_candidates_for_entity(entity_name, url, is_graph, name_to_id, synonym_to_id, min_match_score, ontology_name):
    """For a given entity, structure the respective candidate list and look for a disambiguation solution in it

    :param entity_name: (str) for example "regulation
    :param url: (str) for example "GO_0065007"
    :param is_graph: ontology "is-a" relationships expressed in a MultiDiGraph object (see networkx documentation)
    :param name_to_id: (dict) ontology term names (keys) and ontology ids (values)
    :param synonym_to_id: (dict) ontology synonyms (keys) and ontology ids (values)
    :param min_match_score:(float) minimum matching score, the threeshold (edit distance) to include candidates in candidate 
        list for a given entity 
    :param ontology_name: (str) "GO_BP", "GO_CC", "GO_MF"
    
    :return candidates_for_entity: list with the candidates generated for entity; each candidate is a dict
    :return solution_found: (int); is 0 if entity has an exact match in candidates list; is >= 1 if entity has correct disambiguation
        in candidate list, but it's not an exact match (int is correct candidate index in list); is -1 if the entity has not the 
        correct disambiguation in candidates list
    :return entity_has_candidates: bool, True if given entity has one or more candidates, False otherwise
    """

    candidates_for_entity, retrieved_candidates = [], [] 
    entity_has_candidates = False
    solution_found = -1

    #Retrieve ontology candidates
    if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
        retrieved_candidates, exact_match = map_to_GO(entity_name, url, is_graph, name_to_id, synonym_to_id, ontology_name, 
            min_match_score)
    
    else:
        raise Exception("Invalid ontology")

    #Check if given entity has its solution in retrieved candidates list;
    if retrieved_candidates != []:
        entity_has_candidates = True
    
    if exact_match:
        solution_found = 0
        candidates_for_entity = retrieved_candidates
        
        return candidates_for_entity, entity_has_candidates, solution_found

    else: 
       
        for i, candidate in enumerate(retrieved_candidates):
            
            if candidate["url"] == url: # The candidate is the correct match for entity
                solution_found = i      
                             
        if solution_found > -1: # Update candidates list for entity to put the correct answer as first 
            candidates_for_entity = update_candidates_for_entity(retrieved_candidates, solution_found)

        return candidates_for_entity, entity_has_candidates, solution_found


def update_candidates_for_entity(candidates_for_entity, solution_found):
    "Put the candidate that correctly disambiguates entity in first position in candidates list (only if there is a solution)"
    
    candidates_for_entity_updated = []
    
    correct_candidate = candidates_for_entity[solution_found]
    del candidates_for_entity[solution_found]
    
    candidates_for_entity_updated = [correct_candidate] + [candidate for candidate in candidates_for_entity[:] if candidate != correct_candidate]
        
    return candidates_for_entity_updated


def write_candidates_file(document_name, structured_entities_in_document, ontology_name, is_graph, max_distance, min_match_score):
    """Write document with valid structured candidates for each entity in a given annotation file

    :param document_name: (str) for example "11532192"
    :param structured_entities_in_document: (dict), key is concatenation normalName_id, values[0] is solution found (int), 
        values[1] is candidates list for entity (list)(returned by "structure_candidates_for_entity" function)
    :param ontology_name: (str) see "structure_candidates_for_entity" function
    :param is_graph (MultiDiGraph object): see "structure_candidates_for_entity" function
    :param max_distance: (int) maximum distance allowed between concepts in a given ontology to calculate the links between candidates
    """

    entities_used = 0
    path = "candidates/{}/{}".format(ontology_name,  document_name)
    candidates_file = open(path, 'w')
    print("Writing candidates for {}".format(document_name))
    
    for entity1 in structured_entities_in_document:
        candidates_file.write(structured_entities_in_document[entity1][0]) #Add entity string to file
        entities_used += 1

        for ic1, candidate1 in enumerate(structured_entities_in_document[entity1][1]):  # Iterate through the candidates of current entity
            links = []
            candidate1_class = ""
            
            if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
                candidate1_class = candidate1["url"].replace("_", ":")

            for entity2 in structured_entities_in_document: 
                
                if entity1 != entity2: #A link can only occur between candidates for different entities

                    for ic2, candidate2 in enumerate(structured_entities_in_document[entity2][1]): # Iterate through the candidates of second entity
                        candidate2_class = ""

                        if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
                            candidate2_class = candidate2["url"].replace("_", ":")
                        
                        distance = get_ontology_distance(is_graph, candidate1_class, candidate2_class, ontology_name)
                        
                        if 0 <= distance <= max_distance: #There is a link between the two candidates
                            links.append(str(candidate2["id"]))

            candidate1["links"] = ";".join(set(links))
            
            candidates_file.write(candidate_string.format(candidate1["id"], candidate1["inCount"], candidate1["outCount"], 
                candidate1["links"], candidate1["url"], candidate1["name"], candidate1["normalName"], candidate1["normalWikiTitle"], 
                candidate1["predictedType"]))
        
    candidates_file.close()
    print("entities used:", entities_used)