import os, sys

sys.path.append("./")


def parse_CRAFT_corpus(ontology_name):
    """
    :param ontology_name: (str) "GO_BP", "GO_CC", "GO_MF"
    
    :return annotations_in_corpus: (dict), keys are the document and values are annotation tuples (entity_id, entity_name)
    """

    corpus_directory = "CRAFT/{}/".format(ontology_name)

    annotations_in_corpus = {}

    for annotations_file in os.listdir(corpus_directory):

        if annotations_file.endswith(".ann"):
            file_name = annotations_file[:-4]
            file_path = corpus_directory + "/" + annotations_file
            annotations_in_file = []

            with open(file_path, "r") as file_data:

                for line in file_data.readlines():
                    entity_id = line.split()[1]
                    entity_name = line.split("\t")[2][:-1]
                    annotations_in_file.append((entity_id, entity_name))

                file_data.close()
                annotations_in_corpus[file_name] = annotations_in_file

    return annotations_in_corpus
