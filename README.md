# PPRSSM

Personalized PageRank using Semantic Similarity Measures


## Getting started

This is the code used to run our experiments for the paper "PPR-SSM: Personalized PageRank and Semantic Similarity Measures for Entity Linking".

The code has three steps:

1. Generating candidates file
2. Running PPR algorithm 
3. Analyze results

The code for each gold standard is organized on its separate directoy (hpo_src, chebi_src, and go_src).
The main script of each gold standard are ones starting with "parse".
The others have helper functions to generate and process data. 

## Docker image

You can build a docker image using the Dockerfile provided on this repository or download it from dockerhub:
*docker pull andrelamurias/pprssm*

## Data

We used the following corpora:

1. HPO GSC+ (https://github.com/lasigeBioTM/IHP/raw/master/GSC%2B.rar)
2. ChEBI patents corpus (provided with this repo)
3. CRAFT (https://github.com/UCDenver-ccp/CRAFT)

And the following ontologies:

1. HPO
2. ChEBI
3. Gene Ontology

For each ontology, it is necessary a OBO file and a .db file processed by DiShIn. These can be obtained with the *get_data.sh* script.

## Usage

### Generate candidates for corpus
First run *dishin_app.py* with flask:
```bash
export FLASK_APP=dishin_app.py
export DISHIN_DB=chebi.db
flask run &
```
Args:

1. min distance
2. min similarity
3. corpus dir (or ontology name for Gene Ontology entities in CRAFT corpus: "GO_BP" for GO Biological Process entities, "GO_CC" for GO Cellular Component entities) 

Example:
```bash
python chebi_src/parse_chebi_corpus.py 1 0.5 ChebiPatents/
```

### Run PPR algorithm

Run the PPRforNED script:
```bash
javac ppr_for_ned_chebi.java
java ppr_for_ned_chebi resnik_dishin
```

For GO entities in CRAFT corpus change to the desired subontology in the ppr_for_ned_go.java script
 
### Calculate metrics

Process the results to get more results than what is given by PPRforNED:
```bash
python src/process_results.py chebi
```

Example output:
```
one candidate 431
correct 909
wrong 105
total 1014
accuracy: 0.8964497041420119
accuracy (multiple candidates): 0.8198970840480274
```