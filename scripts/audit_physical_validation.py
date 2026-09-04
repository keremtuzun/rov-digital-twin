import argparse
import json
from pathlib import Path

from rov_dt.physical_evidence import audit_dossier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only validation evidence audit")
    parser.add_argument("dossier", type=Path)
    args = parser.parse_args()
    result = audit_dossier(args.dossier)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["dossier_complete"] else 2)
