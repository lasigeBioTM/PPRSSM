from src.dishin_ssm import (
    get_dist,
    get_ssm,
    get_n_ancestors,
    get_n_descendants,
    get_dist_network,
)
from chebi_src.chebi_ssm import (
    load_chebi,
    get_best_chebi_id,
    map_to_chebi,
    map_to_chebi_api,
)
from hpo_src.hpo_ssm import map_to_hpo

entity_string = "ENTITY\ttext:{0}\tnormalName:{1}\tpredictedType:{2}\tq:true"
entity_string += "\tqid:Q{3}\tdocId:{4}\torigText:{0}\turl:{5}\n"
candidate_string = "CANDIDATE\tid:{0}\tinCount:{1}\toutCount:{2}\tlinks:{3}\t"
candidate_string += (
    "url:{4}\tname:{5}\tnormalName:{5}\tnormalWikiTitle:{5}\tpredictedType:{6}\n"
)


def write_candidates(entity_list, candidates_filename, max_dist, ontology):
    """
    write the entities and candidates of one document to file
    :param entity_list: dicitonary of entities of this document, where the values are the candidates of each entity
    :param candidates_filename: output filename
    :param max_dist: max distance between ontology concepts to be considered
    :return:
    """
    entities_used = 0  # entitites with at least one candidate
    candidates_links = {}  # (url: links)
    candidates_file = open(candidates_filename, "w")
    print("writing candidates for {}".format(candidates_filename))
    first_candidate_link = 0
    for e in entity_list:
        if len(entity_list[e]) > 0:
            candidates_file.write(e)
            entities_used += 1
        # iterate candidates
        for ic, c in enumerate(entity_list[e][:]):
            # links = [str(c["id"])]
            if c["url"] in candidates_links:
                c["links"] = candidates_links[c["url"]]
            else:
                links = []
                # get candidates of every other entity except this one
                other_candidates = []
                for e2 in entity_list:
                    if e2 != e:
                        for ic2, c2 in enumerate(entity_list[e2][:]):
                            other_candidates.append((c2["url"], c2["id"]))
                for c2 in other_candidates:
                    # calculate distance between the two candidates

                    dist = get_dist_network(c["url"], c2[0], ontology)
                    # print(c['url'], c2[0], dist)
                    # TODO: -1
                    if 0 <= dist <= max_dist:
                        # print(c['url'], c2[0], dist)
                        links.append(str(c2[1]))
                        if ic2 == 0 and ic == 0:
                            # print(e, e2)
                            # two first candidates are linked
                            first_candidate_link += 1

                c["links"] = ";".join(set(links))
                candidates_links[c["url"]] = c["links"][:]
            candidates_file.write(
                candidate_string.format(
                    c["id"],
                    c["incount"],
                    c["outcount"],
                    c["links"],
                    c["url"],
                    c["name"],
                    "predictedType:GPE",
                )
            )
    if len(entity_list) > 0:
        print(
            "top candidates that link to other entities",
            first_candidate_link,
            round(first_candidate_link / len(entity_list), 3),
        )
    # print("document time", time.time() - start_time)
    candidates_file.close()
    return entities_used


def update_entity_list(
    entity_list, solution_found, normalized_text, cid, solution_label_matches_entity
):
    updated_list = []
    # print(solution_found)
    correct = entity_list[solution_found]

    entity_perfect_matches = []
    del entity_list[solution_found]
    if (
        entity_perfect_matches
    ):  # there are perfect matches for this entity (some label lowercased)
        if solution_label_matches_entity:
            updated_list = [correct] + [
                e for e in entity_perfect_matches[:] if e != correct
            ]
    else:
        updated_list = [correct] + entity_list
    return updated_list


def generate_candidates_for_entity(
    text, cid, mapto, name_to_id, synonym_to_id, min_match_score=0
):
    # get the candidates of one entity
    ncandidates = []

    less_than_min_score = 0

    perfect_matches_correct = 0
    perfect_match_incorrect = 0
    entities_with_incorrect_perfect_matches = 0

    candidate_list = []
    if mapto == "chebi":
        # candidate_names = map_to_chebi(text, name_to_id, synonym_to_id)
        candidate_names = map_to_chebi_api(text)
    elif mapto == "hpo":
        candidate_names = map_to_hpo(text, name_to_id, synonym_to_id)
    elif mapto == "dbpedia":
        candidate_names = map_to_dbpedia(text)
    # first candidate should be solution
    solution_found = -1
    solution_label_matches_entity = False
    match_nils = 0
    entity_has_incorrect_perfect_match = False
    # get candidates for this entity
    for i, candidate_match in enumerate(candidate_names):
        if candidate_match["cid"] == "NIL":
            match_nils += 1
            continue
        if candidate_match["match_score"] > min_match_score:
            # print("getting descendants for",candidate_match["cid"] )
            outcount = get_n_descendants(candidate_match["cid"].replace(":", "_"))
            incount = int(get_n_ancestors(candidate_match["cid"].replace(":", "_")))
            name = candidate_match["cname"]
            candidate_id = int(candidate_match["cid"].split(":")[1])
            # first candidate should be solution
            candidate_list.append(
                {
                    "url": candidate_match["cid"],
                    "name": name,
                    "outcount": outcount,
                    "incount": incount,
                    "id": candidate_id,
                    "links": [],
                    "score": candidate_match["match_score"],
                }
            )
            # if candidate_match["match_score"] == 100 and chebi_id != candidate_match["chebi_id"]:
            if (
                candidate_match["cname"].lower() == text
                and cid != candidate_match["cid"]
            ):

                entity_has_incorrect_perfect_match = True

                # print("incorrect perfect match", normalized_text, chebi_id, candidate_match)
            # print("found correct label:", ne.text, chebi_id, candidate_match, i)
            if cid == candidate_match["cid"]:
                solution_found = i - match_nils - less_than_min_score
                if (
                    candidate_match["cname"].lower() == text
                ):  # or candidate_match["chebi_name"].lower() == normalized_text[:-1]:
                    perfect_matches_correct += 1
                    solution_label_matches_entity = True
                else:
                    perfect_match_incorrect += 1

        else:
            less_than_min_score += 1

    # if not solution_found:
    #    logging.debug("correct label not found {}, {}, {}".format(ne.text, chebi_id, chebi_names[:1]))
    #    label_not_found += 1
    # reorder candidates
    if entity_has_incorrect_perfect_match:
        entities_with_incorrect_perfect_matches += 1
    if solution_found > -1:
        # update entity list to put the correct answer as first and if there are any perfect matches,
        # include only perfect matches
        candidate_list = update_entity_list(
            candidate_list, solution_found, text, cid, solution_label_matches_entity
        )
        # print(solution_found, end=' ')

        if candidate_list:
            ncandidates.append(len(candidate_list))
    else:
        candidate_list = []
    return (
        candidate_list,
        solution_found == 0,
        solution_label_matches_entity,
        entity_has_incorrect_perfect_match,
    )
