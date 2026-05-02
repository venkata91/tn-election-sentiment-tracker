from storage.db import init_db
from scheduler import run_full_ingest, run_aggregation

init_db()
run_full_ingest()
run_aggregation()
print('Done')
