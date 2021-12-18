import os
from hako.boxes import List, Dict, Tuple

HIER_CANDIDATES = [
    [Tuple],
    [List],
    [Dict],
    [Dict, List],
    [Tuple, List],
    [Dict["foo", "bar"]],
    [List, Dict],
    [List, Dict["foo"], Dict["bar"], Tuple[None]],
    [List, Dict["foo"], Dict, Dict["bar"], Tuple[None]],
]

N_TEST_TIMES = int(os.getenv("N_TEST_TIMES", 1))
