import sys
sys.path.append("./")
from DiShIn import ssm
ssm.semantic_base("DiShIn/hp.db")

hpo_ids = list(ssm.connection.execute("SELECT id FROM entry"))
with open("hpo_pop", 'w') as f:
    for cid in hpo_ids:
        name = ssm.get_name(cid[0]).replace("_", ':')
        if name.startswith("HP"):
            ic = ssm.information_content_intrinsic(cid[0])
            if ic != 0:
                ic = 1/ic
            f.write("url:{}\t{}\n".format(name.replace("HP", "http"), ic))


