"""loomq_lib：LoomQ 量子电路工具包（尺子 + 三后端执行 + 电路库）。

公共 API：
    from loomq_lib import (run_circuit, verify_all_targets, validate_qasm,
                           reference_distribution, transpile, run,
                           get_qasm, get_info, list_circuits, WHITELIST_GATES)
"""

from .semantics import (
    reference_distribution,
    Circuit,
    WHITELIST_GATES,
)
from .backends import (
    SUPPORTED_TARGETS,
    run,
    transpile,
)
from .circuits import (
    get_qasm,
    get_info,
    list_circuits,
    ALL_IDS,
)
from .runner import (
    run_circuit,
    verify_all_targets,
    validate_qasm,
    hellinger,
)

__version__ = "0.1.0"
