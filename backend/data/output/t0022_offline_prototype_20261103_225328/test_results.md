# Offline validation

Run from the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider data/output/t0022_offline_prototype_20261103_225328/test_prototype.py
```

**21 passed in 0.66s.** These include contiguous quotation, canonical ID, unsupported claim/scope, reference and schema failures, omission, duplicate rejection, both length finishes, atomic publication, the scoped T0022 success and all eight category shapes.

The comparison script also completed successfully with local mocks. It checked equivalent final content and evidence metadata before saving its estimates.

```powershell
@'
import runpy, sys
sys.path.insert(0, 'data/output/t0022_offline_prototype_20261103_225328')
runpy.run_path('data/output/t0022_offline_prototype_20261103_225328/compare.py', run_name='__main__')
'@ | .\.venv\Scripts\python.exe -B -
```

The comparison writes its fixture snapshots with exclusive creation. Reproduce in a fresh copy of the prototype directory if these snapshots already exist.
