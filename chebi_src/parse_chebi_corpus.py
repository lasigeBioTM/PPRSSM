import glob
import os
import xml.etree.ElementTree as ET
import sys
import time
import multiprocessing as mp
import logging
import pathlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger = logging.getLogger("urllib3")
logger.setLevel(logging.INFO)
sys.path.append("./")
from chebi_ssm import load_chebi, get_best_chebi_id, map_to_chebi, map_to_chebi_api
from src.generate_candidates import (
    update_entity_list,
    write_candidates,
    entity_string,
    generate_candidates_for_entity,
)

sys.path.append("./")
# from DiShIn import ssm
import ssmpy as ssm


def get_chebi_patents(corpus_dir, min_match_score, mapto):
    # get candidate lists of entities of documents
    entities_wo_text = 0
    updated_id = 0
    ref_nils = 0
    no_solution = 0
    # perfect_matches = 0
    perfect_matches_correct = 0
    perfect_matches_incorrect = 0
    total_entities = 0  # not NIL, with text
    total_unique_entities = 0
    total_unique_entities_match = 0
    solution_is_first_count = 0
    label_not_found = 0
    # if mapto == "chebi":
    is_a_graph, name_to_id, synonym_to_id, id_to_name, id_to_index = load_chebi(
        "chebi.obo"
    )
    # name_to_id, synonym_to_id = None, None
    docs_list = os.listdir(corpus_dir)
    # docs_list = [d for d in docs_list if d in ("WO2007045478", "WO2007045867", "WO2007048709")]
    # docs_list = [d for d in docs_list if d in ("WO2007000651", "WO2007045478", "WO2007045867", "WO2007048709")]

    documents_entity_list = {}  # docID -> entity_list
    # delete candidate files
    # for i in glob.glob("candidates/chebi/*"): - not necessary
    #    os.remove(i)
    for idoc, file in enumerate(docs_list):
        document_entities = set()
        document_entities_match = set()
        start_time = time.time()
        # print(file, str(idoc) + "/"  + str(len(docs_list)))
        tree = ET.parse(corpus_dir + "/" + file + "/scrapbook.xml")
        root = tree.getroot()
        file_id = int(file[2:])
        # print(root)

        entity_list = (
            {}
        )  # entity -> candidate({name:,  id:, incount, outcount, links, etc}

        for s in root.iter("snippet"):
            # print(p)
            # get entities in this snippet
            # sid = s.get("id")
            sid = file
            # snum = int(sid[1:])
            snum = idoc
            # get named entities
            for ne in s.findall("ne"):
                # entity has no text
                if ne.text is None:
                    print("entity has no text: {}".format(str(ne)))
                    entities_wo_text += 1
                    continue

                # normalize text (lower and remove plural)
                normalized_text = ne.text.lower()
                if normalized_text.endswith("s"):
                    normalized_text = normalized_text[:-1]
                # note: normalName should be retrieved from chebi

                # repeated instances of same entity are not necessary
                if normalized_text in document_entities:
                    continue

                # entity is not mapped to CHEBI
                if (
                    not ne.get("chebi-id")
                    or ne.get("chebi-id").startswith("WO")
                    or "," in ne.get("chebi-id")
                ):
                    chebi_id = "NIL"
                    ref_nils += 1
                    continue
                else:
                    # get the chebi on the original corpus or a more recent one, using their API
                    chebi_id = get_best_chebi_id(ne.get("chebi-id"))  # find a better ID
                    if chebi_id != ne.get("chebi-id"):
                        updated_id += 1

                document_entities.add(normalized_text)
                total_entities += 1
                # candidates_file.write(entity_string.format(ne.text, chebi_name, ne.get("type"),
                #                           snum, file_id, chebi_id))
                # this_entity = entity_string.format(ne.text, chebi_name, ne.get("type"),
                #                           snum, file_id, chebi_id)

                # generate entity string line
                this_entity = entity_string.format(
                    ne.text, normalized_text, ne.get("type"), snum, file_id, chebi_id
                )

                # get candidates for entity
                logging.debug("generating candidates for {}".format(normalized_text))
                entity_list[
                    this_entity
                ], solution_is_first, entity_perfect_matches_correct, entity_perfect_matches_incorrect = generate_candidates_for_entity(
                    normalized_text,
                    chebi_id,
                    mapto,
                    name_to_id,
                    synonym_to_id,
                    min_match_score,
                )
                if solution_is_first:
                    solution_is_first_count += 1
                    document_entities_match.add(normalized_text)
                if entity_perfect_matches_correct:
                    perfect_matches_correct += 1
                if entity_perfect_matches_incorrect:
                    perfect_matches_incorrect += 1
                if not entity_list[this_entity] or len(entity_list[this_entity]) == 0:
                    # do not consider this entity if no candidate was found
                    # del entity_list[this_entity]
                    no_solution += 1
        documents_entity_list[file] = entity_list
        total_unique_entities += len(document_entities)
        total_unique_entities_match += len(document_entities_match)

    print(
        "valid entities:",
        total_entities,
        "nils:",
        ref_nils,
        "no text",
        entities_wo_text,
    )
    print("used entities:", total_unique_entities)
    print("ids updated:", updated_id)
    print("no solution found (ignored)", no_solution)
    # print("matches with score less than min", less_than_min_score)
    # print("solution is perfect match", perfect_matches)
    print("solution is first candidate", solution_is_first_count)
    if total_entities - no_solution > 0:
        # print("baseline accuracy", solution_is_first_count/(total_entities-no_solution))
        print(
            "baseline accuracy",
            total_unique_entities_match / (total_unique_entities - no_solution),
        )
        average_correct_match_score = []
        for d in documents_entity_list:
            for e in documents_entity_list[d]:
                if len(documents_entity_list[d][e]) > 0:
                    average_correct_match_score.append(
                        documents_entity_list[d][e][0]["score"]
                    )
                    # print(documents_entity_list[d][e][0]["score"])
        print(
            "average_correct_match_score",
            sum(average_correct_match_score) / len(average_correct_match_score),
        )
    print("perfect match is solution", perfect_matches_correct)
    print("solution label is not a perfect match", perfect_matches_incorrect)
    # print("perfect match is solution", perfect_matches_correct)
    # print("solution label is not a perfect match", perfect_match_incorrect)
    # print("entities with incorrect perfect matches", entities_with_incorrect_perfect_matches)
    # print("average number of candidates", sum(ncandidates) / len(ncandidates))
    # print("max number of candidates", max(ncandidates))
    return documents_entity_list
    # print(""perfect matches:", perfect_matches,
    #      "partial matches:", partial_matches,
    #      "label not found", label_not_found)


def write_candidates_file(entities, d, max_dist, corpus="ChebiPatents"):
    candidates_filename = "candidates/{}/{}".format(corpus, d)
    writen = write_candidates(entities, candidates_filename, max_dist, "chebi")
    output.put(writen)


# first argument: max distance between linked concepts
# second argument: min similarity between entity text and candidate match
ssm.semantic_base("chebi.db")  # , to_memory=False)
max_dist = int(sys.argv[1])
min_match_score = float(sys.argv[2])
# corpus_dir = "ChebiPatents"
# corpus_dir  = "ChebiTest"
corpus_dir = sys.argv[3]
start_time = time.time()
documents_entity_list = get_chebi_patents(
    corpus_dir, min_match_score=min_match_score, mapto="chebi"
)
print("parsing and get entities time:", time.time() - start_time)
# documents_entity_list = get_chebi_patents(corpus_dir, mapto="dbpedia")
entities_writen = 0
output = mp.Queue()
"""
processes = [mp.Process(target=write_candidates_file, args=(documents_entity_list[d], d, max_dist)) for d in documents_entity_list]
print(processes)
# Run processes
for p in processes:
    p.start()

# Exit the completed processes
for p in processes:
    p.join()
print(processes)
# Get process results from the output queue
results = [output.get() for p in processes]
"""
pathlib.Path("candidates/{}".format(corpus_dir)).mkdir(parents=True, exist_ok=True)
for d in documents_entity_list:
    write_candidates_file(documents_entity_list[d], d, max_dist, corpus_dir)
# print("used {} entities".format(sum(results)))
print("total time:", time.time() - start_time)
