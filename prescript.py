###################################################################################################
# Copyright (c) 2020-2022 Centre national de la recherche scientifique (CNRS)
# Copyright (c) 2020-2022 Commissariat a l'énergie atomique et aux énergies alternatives (CEA)
# Copyright (c) 2020-2022 Institut national de recherche en informatique et en automatique (Inria)
# Copyright (c) 2020-2022 Université Paris-Saclay
# Copyright (c) 2020-2022 Université de Versailles Saint-Quentin-en-Yvelines
#
# SPDX-License-Identifier: MIT
#
###################################################################################################

import yaml
import sys

# sys.argv[1] = 10 # global_size.height
# sys.argv[2] = 10 # global_size.width
# sys.argv[3] = 2 # parallelism.height
# sys.argv[4] = 2 # parallelism.width
# sys.argv[5] = 1 # generation 
# sys.argv[6] = 1 # nworkers

with open('config.yml', 'w') as file:
    data = {"global_size":   {"height": int(sys.argv[1]), "width": int(sys.argv[2])},
            "parallelism":  {"height": int(sys.argv[3]), "width": int(sys.argv[4])},
            "MaxtimeSteps": int(sys.argv[5]),
            "workers":   int(sys.argv[6])}
if data:
    with open('config.yml', 'w') as file:
        yaml.safe_dump(data, file)
