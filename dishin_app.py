from flask import Flask
from flask import request
from flask import g
from SPARQLWrapper import SPARQLWrapper, JSON
import sqlite3
from io import StringIO

# http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
# This is a flask app to run DiShIn as a service and cache results to a in-memory database
import ssmpy as ssm

# from dishin import calculate_terms_similarity

app = Flask(__name__)


DATABASE = "./cache.db"
ssm.semantic_base("chebi.db")

# https://stackoverflow.com/a/10856450
def init_sqlite_db(app):
    # Read database to tempfile
    con = sqlite3.connect(DATABASE)
    tempfile = StringIO()
    for line in con.iterdump():
        tempfile.write("%s\n" % line)
    con.close()
    tempfile.seek(0)

    # Create a database in memory and import from tempfile
    app.sqlite = sqlite3.connect(":memory:")
    app.sqlite.cursor().executescript(tempfile.read())
    app.sqlite.commit()
    app.sqlite.row_factory = sqlite3.Row


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    # tempfile = StringIO()
    # for line in db.iterdump():
    #    tempfile.write('%s\n' % line)
    # db.close()
    # tempfile.seek(0)
    # db = sqlite3.connect(":memory:")
    # db.cursor().executescript(tempfile.read())
    # db.commit()
    # db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    get_db().commit()
    # print(cur.lastrowid)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/dishin/")
def hello():
    entry1 = request.args.get("entry1")
    entry2 = request.args.get("entry2")
    measure = request.args.get("measure")
    ontology = request.args.get("ontology")

    # print(entry1, entry2, measure, ontology)
    score = calculate_terms_similarity(entry1, entry2, measure, ontology)
    return "{} \t {} ".format(measure, score)


@app.route("/dishin/ancestors/")
def entity_ancestors():
    entry1 = request.args.get("entry1")
    ontology = request.args.get("ontology")
    ssm.semantic_base(ontology)
    return ssm.get_ancestors(entry1)
    # print(entry1, entry2, measure, ontology)
    # score = ssm.
    # return "{} \t {} ".format(measure, score)


def calculate_terms_similarity(name1, name2, measure, sb_file):
    print(name1, name2)
    e1 = ssm.get_id(name1)
    e2 = ssm.get_id(name2)
    if e1 > e2:
        e1, e2 = e2, e1
        name1, name2 = name2, name1
    if (e1 > 0 and e2 > 0) or (e1 > 0 and e2 == 0):

        t = (name1, name2, measure)
        res = query_db(
            "SELECT value FROM cache WHERE id1=? AND id2=? AND measure=?", t, one=True
        )
        score = res
        print("getting pair...", name1, name2, score)
        if score is None or len(score) == 0:

            # ssm.intrinsic = True

            # ontology with multiple inheritance
            if measure == "resnik_dishin":
                if not (
                    sb_file.endswith("wordnet.db") or sb_file.endswith("radlex.db")
                ):
                    ssm.mica = False
                    score = ssm.ssm_resnik(e1, e2)
                    # print("Resnik \t DiShIn \t intrinsic \t" + str(score))
            elif measure == "resnik_mica":
                ssm.mica = True
                score = ssm.ssm_resnik(e1, e2)
                # print("Resnik \t MICA \t intrinsic \t" + str(score))

            elif measure == "lin_dishin":
                if not (
                    sb_file.endswith("wordnet.db") or sb_file.endswith("radlex.db")
                ):
                    ssm.mica = False
                    score = ssm.ssm_lin(e1, e2)
                    # print("Lin \t DiShIn \t intrinsic \t" + str(score))
            elif measure == "lin_mica":
                ssm.mica = True
                score = ssm.ssm_lin(e1, e2)
                # print("Lin \t MICA \t intrinsic \t" + str(score))
            elif measure == "jc_dishin":
                if not (
                    sb_file.endswith("wordnet.db") or sb_file.endswith("radlex.db")
                ):
                    ssm.mica = False
                    score = ssm.ssm_jiang_conrath(e1, e2)
                    # print("JC \t DiShIn \t intrinsic \t" + str(score))
            elif measure == "jc_mica":
                ssm.mica = True
                score = ssm.ssm_jiang_conrath(e1, e2)
                # print("JC \t MICA \t intrinsic \t" + str(score))

            elif measure == "commonancestors":
                score = ",".join([str(x) for x in ssm.common_ancestors(e1, e2)])
                # print(score)
            elif measure == "ancestors":
                score = ",".join([str(x) for x in ssm.get_ancestors(e1)])

            res = query_db(
                "INSERT INTO cache VALUES (?,?,?,?)", (name1, name2, measure, score)
            )
            # res = query_db('SELECT value FROM cache WHERE id1=? AND id2=? AND measure=?', t, one=True)
            print("new pair", score, res, flush=True)
        else:
            print("cached pair", name1, name2, score, flush=True)
            score = score[0]
        return score
    else:

        print("Error: entry unknown", e1, e2, flush=True)
        return -1
