from fuzzywuzzy import fuzz, process
import networkx as nx, obonet, sys
import atexit, logging, json, os, pickle

sys.path.append("./")

#### Check if ancestor_descendant_cache_file exists; if it doesn't create new file
ancestor_descendant_cache_file = "temp/ancestors_descendants_cache.pickle"

if os.path.exists(ancestor_descendant_cache_file):
    logging.info("loading ancestors_descendants...")
    ancestor_descendant_cache = pickle.load(open(ancestor_descendant_cache_file, "rb"))
    loaded_ancestor_descendant = True
    logging.info("loaded ancestor_descendants dictionary with %s entries", str(len(ancestor_descendant_cache)))

else:
    ancestor_descendant_cache = {}
    loaded_ancestor_descendant = False
    logging.info("new ancestors_descendants dictionary")

def exit_handler():
    print('Saving ancestors_descendants dictionary...!')
    pickle.dump(ancestor_descendant_cache, open(ancestor_descendant_cache_file, "wb"))

atexit.register(exit_handler)


def map_to_GO(entity_name, entity_id, is_graph, name_to_id, synonym_to_id, ontology_name, min_match_score):
    """Find best GO matches (edit distance) in name_to_id and synonym_id dicts for given entity

    :param entity_name: (str) for example "apoptosis"
    :param entity_id: (str) for example "GO_0006915"
    :param is_graph: ontology "is-a" relationships expressed in a MultiDiGraph object (see networkx documentation)
    :param name_to_id: (dict) ontology term names (keys) and ontology ids (values)
    :param synonym_to_id: (dict) ontology synonyms (keys) and ontology ids (values)
    :param ontology_name: (str) "GO_BP", "GO_CC", "GO_MF"
    
    :return structured_match: (list with one dict element) if an exact match is found, otherwise structured_matches
        (list with more than one element) with best matches for given entity
    """

    exact_match, ambiguous_matches = False, False
    
    #Extract the most textual similar ontology terms 
    entity_matches = process.extract(entity_name.lower(), name_to_id.keys(), scorer=fuzz.token_sort_ratio, limit=5)

    #Retrieve match ontology id for each match
    entity_matches_updated, synonym_matches_updated = [], []
    
    for match in entity_matches: 
        match_id = name_to_id[match[0]].replace(":","_")
        updated_match = (match[0], match_id, match[1])
        entity_matches_updated.append(updated_match)
       
    #Check for exact matches 
    if entity_matches_updated[0][2] == 100 and entity_matches_updated[0][1] == entity_id: 
        #The first match is the exact match for entity 
        structured_match = structure_matches(entity_matches_updated[0], ontology_name, is_graph, min_match_score)
        exact_match = True
        
        return structured_match, exact_match

    #If no exact match found previously, check if there is an exact match at synonyms list
    else: 
        synonym_matches = process.extract(entity_name.lower(), synonym_to_id.keys(), limit=5, scorer=fuzz.token_sort_ratio)
            
        for synonym in synonym_matches:
            synonym_id = synonym_to_id[synonym[0]]
            synonym_updated = (synonym[0], synonym_id.replace(":","_"), synonym[1])
            synonym_matches_updated.append(synonym_updated)
                
            if synonym_updated[2] == 100 and synonym_updated[1] == entity_id: #There is a synonym match for entity
                structured_match = structure_matches(synonym_updated, ontology_name, is_graph, min_match_score)
                exact_match = True
                
                return structured_match, exact_match

        #If no exact matches so far -> add the retrieved synonyms to candidate list and structure all candidates
        if exact_match == False:
            ambiguous_matches = True
            entity_matches_updated.extend(synonym_matches_updated)
            structured_matches = structure_matches(entity_matches_updated, ontology_name, is_graph, min_match_score)
            
            return structured_matches, exact_match
            
           
def structure_matches(matches, ontology_name, is_graph, min_match_score):
    """Get properties of retrieved matches"""
  
    global ancestor_descendant_cache

    structured_matches = []
    
    if len(matches) == 0:
        
        return structure_matches
    
    else:

        if type(matches) == tuple:  
            temp_matches =  [matches]
        
        elif type(matches) == list:
            temp_matches = matches

        for match in temp_matches:
            match_url = match[1]
            match_score = match[2]/100    
            
            if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
                match_id = match[1].split("GO_")[1]
            
            if match_score >= min_match_score: 
                
                if match_url in ancestor_descendant_cache.keys():
                    in_count = ancestor_descendant_cache[match_url][0]
                    out_count = ancestor_descendant_cache[match_url][1] 
                
                else:
                    in_count = len(is_graph.out_edges(match[1].replace("_",":")))
                    out_count = len(is_graph.in_edges(match[1].replace("_",":")))
                    ancestor_descendant_cache[match_url] = (in_count, out_count)

                structured_match =  {"url": match_url , "name": match[0],"matchScore": match_score , "predictedType":ontology_name, 
                                        "normalName":match[0].lower(), "normalWikiTitle":match[0].lower(), "inCount": in_count,
                                        "outCount":out_count, "id": match_id}
                
                structured_matches.append(structured_match)
        
        if len(structured_matches) > 0:
            structured_matches = sorted(structured_matches, key=lambda match: match["matchScore"], reverse=True)

    return structured_matches    

