# Entity string
entity_string = "ENTITY\ttext:{0}\tnormalName:{1}\tpredictedType:{2}\tq:{3}"
entity_string += "\tqid:{4}\tdocId:{5}\torigText:{6}\turl:{7}\n"

# Candidate string
candidate_string = "CANDIDATE\tid:{0}\tinCount:{1}\toutCount:{2}\tlinks:{3}\t"
candidate_string += "url:{4}\tname:{5}\tnormalName:{6}\tnormalWikiTitle:{7}\tpredictedType:{8}\n"

# Corpus statistics string
statistics_string = "STATISTICS FOR {0} CORPUS\n"
statistics_string  += "Number of documents: {1}\nInvalid Annotations: {2}\nTotal entities: {3}\nNamed entities/document: {4}\n"
statistics_string  += "Entities with candidates: {5}\nEntities with candidates/Total named entities: {6}\n"
statistics_string  += "Entities with solution: {7}\nEntities with solution/Entities with candidates: {8}\n"
statistics_string  += "Entities with solution/document: {9}\n"
statistics_string  += "\nConsidering only unique entities in each document:\n"
statistics_string  += "Unique entities (in document) with solution: {10}\nUnique entities/Document: {11}\n"
statistics_string  += "Correctly disambiguated (unique) entities: {12}\nBaseline accuracy: {13}\n"

