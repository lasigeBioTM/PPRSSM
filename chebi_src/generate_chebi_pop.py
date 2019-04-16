import os
import xml.etree.ElementTree as ET
from chebi_ssm import get_best_chebi_id
import sys
sys.path.append("./")

from DiShIn import ssm
ssm.semantic_base("DiShIn/chebi.db")



chebi_ids = list(ssm.connection.execute("SELECT id FROM entry"))
with open("chebi_pop", 'w') as f:
    for cid in chebi_ids:
        name = ssm.get_name(cid[0]).replace("_", ':')
        if name.startswith("CHEBI"):

            ic = ssm.information_content_extrinsic(cid[0])
            #ic = ssm.information_content_intrinsic(cid[0])
            if ic != 0:
                ic = 1/ic
            f.write("url:{}\t{}\n".format(name.replace("CHEBI", "http"), ic))


