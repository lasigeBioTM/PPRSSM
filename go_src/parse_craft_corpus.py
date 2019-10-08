import sys, time
import pathlib
from build_candidates_files import (
    structure_candidates_for_entity,
    write_candidates_file,
)
from corpus_statistics import create_corpus_statistics_file
from ontology import load_GO, get_ontology_type
from parse_annotations import parse_CRAFT_corpus
from strings import entity_string
from generate_pop_file import generate_pop_file

sys.path.append("./")


def pre_processing(
    max_distance=int(sys.argv[1]),
    min_match_score=float(sys.argv[2]),
    ontology_name=str(sys.argv[3]),
):
    """Pre-processing of annotation files to apply Personalized PageRank

    :param ontology_name: (str) "GO_BP", "GO_CC", "GO_MF"
    :param max_distance: (int) maximum distance allowed between concepts in a given ontology to calculate the links between candidates
    :param min_match_score: (float) minimum matching score, the threeshold (edit distance) to include candidates in candidate 
        list for a given entity 
    """

    # Parse annotations files in corpus
    annotations = {}

    if ontology_name == "GO_BP" or ontology_name == "GO_CC" or ontology_name == "GO_MF":
        annotations = parse_CRAFT_corpus(ontology_name)
        is_graph, name_to_id, synonym_to_id = load_GO(ontology_name)

    else:
        raise Exception("Invalid ontology")

    document_count, corpus_statistics = 0, []
    pathlib.Path("candidates/{}".format(ontology_name)).mkdir(
        parents=True, exist_ok=True
    )
    for document in annotations:  # Iterate through each document in corpus
        document_count += 1
        print(
            "==========================================\nPROCESSING",
            document,
            "\t",
            time.strftime("%X %x"),
            "\nDOCUMENT COUNT:",
            document_count,
            "\n",
        )
        structured_entities_in_document = {}
        valid_entities_count, invalid_annotations_count, entities_with_candidates_count, entitities_with_solution_count, first_solution_count = (
            0,
            0,
            0,
            0,
            0,
        )

        for annotation in annotations[
            document
        ]:  # Iterate through each annotation in current document

            if annotation[1] != "NIL" or annotation[0] != "" or annotation[1] != "":
                valid_entities_count += 1

                entity_name, normalized_text, q, qid, entity_url = (
                    annotation[1],
                    annotation[1].lower(),
                    "true",
                    "Q" + str(document_count),
                    annotation[0],
                )

                predicted_type = get_ontology_type(entity_url, ontology_name)

                formatted_entity = entity_string.format(
                    entity_name,
                    normalized_text,
                    predicted_type,
                    q,
                    qid,
                    document_count,
                    entity_name,
                    entity_url,
                )

                candidates_for_entity, entity_has_candidates, entity_solution = structure_candidates_for_entity(
                    entity_name,
                    entity_url,
                    is_graph,
                    name_to_id,
                    synonym_to_id,
                    min_match_score,
                    ontology_name,
                )

                if entity_has_candidates:
                    entities_with_candidates_count += 1

                if entity_solution > -1:
                    entitities_with_solution_count += 1

                    entity_designation = normalized_text + "_" + entity_url
                    structured_entities_in_document[entity_designation] = (
                        formatted_entity,
                        candidates_for_entity,
                        entity_solution,
                    )

            else:
                invalid_annotations_count += 1

        # Generate statistics for document and build candidates file
        document_statistics = (
            valid_entities_count,
            invalid_annotations_count,
            entities_with_candidates_count,
            entitities_with_solution_count,
        )
        corpus_statistics.append((structured_entities_in_document, document_statistics))
        write_candidates_file(
            document,
            structured_entities_in_document,
            ontology_name,
            is_graph,
            max_distance,
            min_match_score,
        )

    # Generate statistics for corpus and build file with information content for each entity in candidates file
    create_corpus_statistics_file(
        ontology_name, document_count, corpus_statistics, min_match_score
    )
    generate_pop_file(ontology_name, annotations)


if __name__ == "__main__":
    pre_processing()
