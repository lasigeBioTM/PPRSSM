import glob
import os
import sys
import time
sys.path.append("./")
from DiShIn import ssm

from hpo_ssm import load_hpo, map_to_hpo
#from dishin_ssm import get_n_ancestors, get_n_descendants, get_dist
from generate_candidates import update_entity_list, write_candidates, entity_string, generate_candidates_for_entity

candidate_string = "CANDIDATE\tid:{0}\tinCount:{1}\toutCount:{2}\tlinks:{3}\t"
candidate_string += "url:{4}\tname:{5}\tnormalName:{5}\tnormalWikiTitle:{5}\tpredictedType:{6}\n"




def get_hpo_documents(corpus="GSCplus/", min_match_score=0, mapto="hpo"):
    entities_wo_text = 0
    updated_id = 0
    ref_nils = 0
    no_solution = 0
    perfect_matches_correct = 0
    perfect_matches_incorrect = 0
    total_entities = 0  # not NIL, with text
    solution_is_first_count = 0
    label_not_found = 0
    used_entities = 0
    corpus_dir, annotations_dir = ("{}/documents/".format(corpus), "{}/annotations/".format(corpus))
    if mapto == "hpo":
        is_a_graph, name_to_id, synonym_to_id, id_to_name, id_to_index, alt_id_to_id = load_hpo("hp.obo")
    docs_list = os.listdir(corpus_dir)
    documents_entity_list = {}  # docID -> entity_list
    for i in glob.glob("candidates/{}/*".format(corpus)):
        os.remove(i)
    docs_list = docs_list[:]
    for idoc, file in enumerate(docs_list):
        if idoc > 50:
            break
        start_time = time.time()
        entity_list = {}  # entity -> candidate({name:,  id:, incount, outcount, links, etc}
        #candidates_file = open("candidates/{}/{}".format(corpus, file), 'w')
        #print(file, idoc, len(docs_list))
        document_entities = set()
        #with open(corpus_dir + file) as f:
        #   text = f.readlines()[0]
        with open(annotations_dir + file) as f:
            for line in f:
                values = line.split("\t")
                hpid, etext = values[1].strip().split(" | ")
                hpid = hpid.replace("_", ":")
                if hpid in alt_id_to_id:
                    hpid = alt_id_to_id[hpid]
                    updated_id += 1

                normalized_text = etext.lower()
                if normalized_text.endswith("s"):
                    normalized_text = normalized_text[:-1]
                if normalized_text in document_entities:
                    continue
                document_entities.add(normalized_text)
                #print(etext, len(hpnames), hpid, hpnames[0])
                total_entities += 1
                this_entity = entity_string.format(etext, normalized_text, "HPO",
                                                   idoc, file, hpid)
                entity_list[this_entity], solution_is_first,\
                                           entity_perfect_matches_correct,\
                                           entity_perfect_matches_incorrect = generate_candidates_for_entity(normalized_text, hpid,
                                                                                             mapto, name_to_id,
                                                                                             synonym_to_id,
                                                                                             min_match_score)
                if solution_is_first:
                    solution_is_first_count += 1
                if entity_perfect_matches_correct:
                    perfect_matches_correct += 1
                if entity_perfect_matches_incorrect:
                    perfect_matches_incorrect += 1
                if not entity_list[this_entity]:
                    # do not consider this entity if no candidate was found
                    del entity_list[this_entity]
                    no_solution += 1
        documents_entity_list[file] = entity_list
        used_entities += len(document_entities)
    print("valid entities:", total_entities, "nils:", ref_nils, "no text", entities_wo_text)
    print("used entities", used_entities)
    print("ids updated:", updated_id)
    print("no solution found (ignored)", no_solution)
    # print("matches with score less than min", less_than_min_score)
    #print("solution is perfect match", perfect_matches)
    print("solution is first candidate", solution_is_first_count)
    if total_entities - no_solution > 0:
        print("baseline accuracy", solution_is_first_count/(total_entities-no_solution))
        average_correct_match_score = []
        for d in documents_entity_list:
            for e in documents_entity_list[d]:
                if len(documents_entity_list[d][e]) > 0:
                    average_correct_match_score.append(documents_entity_list[d][e][0]["score"])
                    #print(documents_entity_list[d][e][0]["score"])
        print("average_correct_match_score", sum(average_correct_match_score)/len(average_correct_match_score))
    print("perfect match is solution", perfect_matches_correct)
    print("solution label is not a perfect match", perfect_matches_incorrect)
    # print("entities with incorrect perfect matches", entities_with_incorrect_perfect_matches)
    # print("average number of candidates", sum(ncandidates) / len(ncandidates))
    # print("max number of candidates", max(ncandidates))
    return documents_entity_list


print("load semantic base")
ssm.semantic_base("DiShIn/hp.db")
max_dist = int(sys.argv[1])
min_match_score = float(sys.argv[2])
corpus_dir = sys.argv[3]
#documents_entity_list = get_hpo_documents(corpus=("HPOtest/documents/", "HPOtest/annotations/"), min_match_score=min_match_score)
print("get hpo documents")
documents_entity_list = get_hpo_documents(corpus=corpus_dir, min_match_score=min_match_score)
print("generate candidates")
for d in documents_entity_list:
    candidates_filename = "candidates/{}/{}".format(corpus_dir, d)
    write_candidates(documents_entity_list[d], candidates_filename, max_dist, "hpo")
