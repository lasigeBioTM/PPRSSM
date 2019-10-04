from math import log
import os, sys
sys.path.append("./")


def build_extrinsic_information_content_dict(annotations):
    """Dict with extrinsic information content (Resnik's) for each term in a corpus """ 

    term_counts, extrinsic_ic = {}, {}
   
    #Get the number of times each term appear in corpus
    for document in annotations: 
        
        for annotation in annotations[document]:
            term_id = annotation[0]
            
            if term_id not in term_counts.keys():
                term_counts[term_id] = 1
            else:
                term_counts[term_id] += 1
            
    max_freq = max(term_counts.values()) #Frequency of the most frequent term in dataset
    
    for term_id in term_counts:
        
        term_frequency = term_counts[term_id] 
   
        term_probability = (term_frequency + 1)/(max_freq + 1)
    
        information_content = -log(term_probability) + 1
        
        extrinsic_ic[term_id] = information_content + 1
             
    return extrinsic_ic


def generate_pop_file(target_ontology, annotations):
    """Generate pop file for target ontology with information content of all entities referred in candidates file"""

    ontology_pop_string = ''
    temp_ic = []
    candidates_dir = "candidates/" + target_ontology + "/"
    ic_dict = build_extrinsic_information_content_dict(annotations) 

    for file in os.listdir(candidates_dir): 
        data = ''
        path = candidates_dir + file
        candidate_file = open(path, 'r', errors="ignore")
        data = candidate_file.read()
        candidate_file.close()
        
        for line in data.split('\n'):
            url = ""
            
            if line[0:6] == "ENTITY":   
                url = line.split('\t')[8].split('url:')[1]
                predicted_type = line.split('\t')[3][14:]
            
            elif line[0:9] == "CANDIDATE":
                url = line.split('\t')[5].split('url:')[1]
                predicted_type = line.split('\t')[9][14:]     
            
            if url in temp_ic or predicted_type in temp_ic: #To prevent duplicate entries in dbpedia_pop file
                
                continue
            
            else:
                
                if url != "":
                    
                    if target_ontology == "GO_BP" or target_ontology == "GO_CC" or target_ontology == "GO_MF" or target_ontology == "CL" or target_ontology == "UB":
                            
                        if url in ic_dict.keys():
                            ic = ic_dict[url]
                        
                        else:
                            ic = 1.0
                        
                        ontology_pop_string += url + '\t' + str(ic) + '\n'
                        temp_ic.append(url)
                 
    #Create file ontology_pop with information content for all entities in candidates file
    output_file_name = target_ontology + "_pop"
    
    with open(output_file_name, 'w') as ontology_pop:
        ontology_pop.write(ontology_pop_string)
        ontology_pop.close()
