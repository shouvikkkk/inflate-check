"""inflate-check — detect constraint inflation in compacted agent summaries.

A compaction summary can keep an instruction while making it broader or
stronger than the user meant: a preference becomes a requirement, a one-off
becomes a standing rule, a narrow scope becomes "all", or a replaced value
is kept as current. This package compares an original instruction set
against its compacted summary and flags exactly those changes.
"""

__version__ = "0.1.0"
