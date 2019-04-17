from strings import statistics_string

def create_corpus_statistics_file(target_ontology, document_count, corpus_statistics, min_match_score):
    """Creates a .txt file with statistics for the desginated corpus
    
    :param target_ontology: (str) "GO_BP", "GO_CC", "GO_MF"
    :param document_count: (int)
    :param corpus_statistics: tuple, where tuple[0] is structured entities (dict) and tuple[1] is document_statistics (tuple)
    :param min_match_score: (float) minimum matching score, the threeshold (edit distance) to include candidates in candidate 
        list for a given entity 
    """
    
    total_entities, invalid_annotations, entities_with_candidates, entities_with_solution, first_solution_count, \
        total_unique_entities_with_solution, first_solution_count_unique = 0, 0, 0, 0, 0, 0, 0

    #Iterate through documents and retrieve document statistics
    for document in corpus_statistics: 
        total_entities += document[1][0]
        invalid_annotations += document[1][1] 
        entities_with_candidates += document[1][2]
        entities_with_solution += document[1][3]
       
       #Iterate through unique entities in document and retrieve entity statistics
        for value in (document[0].values()): 
            total_unique_entities_with_solution += 1
            
            if value[2] == 0:
                first_solution_count_unique += 1
    
    #Statistics related with all entities present in document
    entities_candidates_Document = entities_with_candidates/document_count
    entities_with_solution_Entities_with_candidates =   entities_with_solution/entities_with_candidates
    entities_with_candidates_Total_entities = entities_with_candidates/total_entities
    entities_solution_Document = entities_with_solution/document_count

    #The baseline accuracy of unique entities 
    unique_entities_Document = total_unique_entities_with_solution/document_count
    baseline_accuracy_unique = first_solution_count_unique/total_unique_entities_with_solution


    #Generate the complete statistics string and write it in a new file
    statistics_output = statistics_string.format(target_ontology, document_count, invalid_annotations, total_entities, entities_candidates_Document, 
        entities_with_candidates, entities_with_candidates_Total_entities, entities_with_solution, entities_with_solution_Entities_with_candidates,
        entities_solution_Document, total_unique_entities_with_solution, unique_entities_Document, first_solution_count_unique, baseline_accuracy_unique)
    
    file_name = "results/" + target_ontology + "/corpus_statistics_" + str(min_match_score)
    
    with open(file_name, "w") as statistics_file:
        statistics_file.write(statistics_output)
        statistics_file.close()
    
