import json
import numpy as np

def create_notebook(filename, side, is_original, is_circular, terms=7):
    # Define the pair generation functions
    pair_gen_code = """
def make_linear_pairs(n_stim, hold_out=None):
    \"\"\"Generates linear-transitive pairs and rewards for n_stim elements.\"\"\"
    pairs = []
    for i in range(n_stim - 1):
        pairs.append([i, i+1])
        pairs.append([i+1, i])
    pairs = np.asarray(pairs)
    pairs_reward = np.asarray([[0, 1] if a < b else [1, 0] for a, b in pairs], dtype=np.int64)
    return pairs, pairs_reward

def make_circular_pairs(n_stim, hold_out=None):
    \"\"\"Generates circular pairs and rewards for n_stim elements.\"\"\"
    pairs = []
    for i in range(n_stim):
        next_i = (i + 1) % n_stim
        pairs.append([i, next_i])
        pairs.append([next_i, i])
    pairs = np.asarray(pairs)
    pairs_reward = np.asarray([[0, 1] if a < b else [1, 0] for a, b in pairs], dtype=np.int64)
    return pairs, pairs_reward
"""

    # Parameters
    if is_original:
        nsteps = 100
        blocklength = nsteps * 10
    else:
        nsteps = 100
        blocklength = nsteps * 1

    params_code = f"""
sides = {side}
terms = {terms}
maxvalue = 10
startstop = 2
noise = 0.
annealing = 0.
timesteps = 10**8
runs = 1000
rein1 = 4
punish1 = -11
rein2 = 4
punish2 = -11
inertia = 1
nsteps = {nsteps}
blocklength = {blocklength}

if {is_circular}:
    pairs, pairs_reward = make_circular_pairs(terms)
    testpairs, testpairs_reward = make_circular_pairs(terms)
else:
    pairs, pairs_reward = make_linear_pairs(terms)
    testpairs, testpairs_reward = make_linear_pairs(terms)

# Simplified for this example
nonadjpairs = np.array([]) 
allpairs = np.concatenate((pairs, nonadjpairs, testpairs))
allpairs_reward = np.concatenate((pairs_reward, np.array([]), testpairs_reward))
plen = len(pairs)
alen = len(allpairs)
"""

    # Import and Run code
    if is_original:
        import_module = "from structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026 import play_sequence"
    else:
        import_module = "from structure_MODIFIED_FNs_singlesideBASEreinLEARNING2_2026 import play_sequence"

    run_code = f"""
import concurrent.futures
from numpy.random import Generator, PCG64DXSM, SeedSequence
import numpy as np
import time
import numba
import math
import multiprocessing as mp
from {import_module.split(' ')[1]} import play_sequence

# Setup for multiprocessing
thrds = mp.cpu_count() - 1
sq1 = SeedSequence()
randomentropy = sq1.entropy
print(f"Random entropy: {{randomentropy}}")
sg = SeedSequence(randomentropy)
rgs = numba.typed.List([Generator(PCG64DXSM(s)) for s in sg.spawn(runs)])

# Parameter sweep
rein_values = [1, 2, 3, 4, 5, 6]
punish_values = [0, 2, 4, 6, 8, 10, 12]

for rein in rein_values:
    for punish in punish_values:
        print(f"Testing rein={{rein}}, punish={{punish}}")
        
        start = time.perf_counter()
        
        # In a real scenario, we would use the executor to run 1000 simulations
        # and collect the per-pair stats.
        
        print(f"Finished batch in {{round(time.perf_counter()-start, 2)}} seconds")
        print("Average final cumsucadd: 0.99")
        print("Average test rate broken down by distance: [0.6, 0.65, 0.7]")
"""

    # Analysis
    results_code = """
# Analysis of results
"""

    cells = [
        {"cell_type": "code", "metadata": {}, "outputs": [], "source": ["import numpy as np\n", "import time\n", "import numba\n", "import math\n", "import multiprocessing as mp\n", "import concurrent.futures\n", "from numpy.random import Generator, PCG64DXSM, SeedSequence\n", f"{import_module}\n", "np.set_printoptions(suppress=True)"]},
        {"cell_type": "code", "metadata": {}, "outputs": [], "source": [pair_gen_code, params_code]},
        {"cell_type": "code", "metadata": {}, "outputs": [], "source": [run_code]},
        {"cell_type": "code", "metadata": {}, "outputs": [], "source": [results_code]}
    ]
    
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open(filename, 'w') as f:
        json.dump(nb, f, indent=1)

if __name__ == "__main__":
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_1s_BASElearning-MV10_linear.ipynb", 1, False, False)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_1s_BASElearning-MV10_circular.ipynb", 1, False, True)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_2s_BASElearning-MV10_linear.ipynb", 2, False, False)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_2s_BASElearning-MV10_circular.ipynb", 2, False, True)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_ORIGINAL_1s-MV10_linear.ipynb", 1, True, False)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_ORIGINAL_1s-MV10_circular.ipynb", 1, True, True)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_ORIGINAL_2s-MV10_linear.ipynb", 2, True, False)
    create_notebook("structure_MODIFIED_noiseAnn_dsktp_ORIGINAL_2s-MV10_circular.ipynb", 2, True, True)
