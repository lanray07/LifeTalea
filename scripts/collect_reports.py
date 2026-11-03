"""Retired bootstrap: its hardcoded evidence mapping predates current QA.

Historical acceptance files are retained unchanged in scope. Current packaging
reads actual build/test/capture provenance through prepare_amazon_submission.py.
"""

def main():
    raise SystemExit('Historical report generator retired. Run inspect_amazon_apk.py and prepare_amazon_submission.py after current build/device/capture checks; do not infer an updated acceptance percentage from old logs.')

if __name__ == '__main__': main()
