import sys
import time
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Add backend directory to sys.path
backend_root = Path(__file__).resolve().parent
sys.path.append(str(backend_root))

from app.services.redis_client import redis_client
from app.services.queue_service import WORKFLOW_QUEUE_NAME
from app.services.workflow_platform_service import workflow_platform_service, PauseIteration

def _utc_now():
    return datetime.now(timezone.utc).isoformat()

def main():
    print(f"Starting Upstash Redis queue worker. Listening on '{WORKFLOW_QUEUE_NAME}'...")
    while True:
        try:
            # Poll using rpop (non-blocking in Redis, we provide blocking by sleeping)
            job = redis_client.rpop(WORKFLOW_QUEUE_NAME)
            if not job:
                time.sleep(1)
                continue
            
            # The job could be a string or already parsed dict depending on upstash-redis version
            if isinstance(job, str):
                job_data = json.loads(job)
            else:
                job_data = job

            run_id = job_data["run_id"]
            workflow_id = job_data["workflow_id"]
            snapshot = job_data["snapshot"]
            context = job_data["context"]
            mode = job_data.get("mode", "manual")
            debug = job_data.get("debug", False)
            
            print(f"Processing workflow run: {run_id}")
            
            try:
                final_output = workflow_platform_service._execute_snapshot(run_id, workflow_id, snapshot, context, mode, debug)
                with workflow_platform_service._connect() as connection:
                    connection.execute(
                        """
                        UPDATE workflow_runs
                        SET status = ?, final_output = ?, context_snapshot = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        ("completed", json.dumps(final_output), json.dumps(context), _utc_now(), run_id),
                    )
                print(f"Successfully completed run {run_id}")
            except PauseIteration as paused:
                print(f"Run {run_id} paused waiting for approval")
                with workflow_platform_service._connect() as connection:
                    connection.execute(
                        """
                        UPDATE workflow_runs
                        SET status = ?, context_snapshot = ?, final_output = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        ("waiting_approval", json.dumps(context), json.dumps(paused.payload), _utc_now(), run_id),
                    )
            except Exception as exc:
                print(f"Run {run_id} failed with error: {exc}")
                traceback.print_exc()
                with workflow_platform_service._connect() as connection:
                    connection.execute(
                        """
                        UPDATE workflow_runs
                        SET status = ?, error_message = ?, context_snapshot = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        ("failed", str(exc), json.dumps(context), _utc_now(), run_id),
                    )

        except Exception as queue_exc:
            print(f"Worker queue polling error: {queue_exc}")
            traceback.print_exc()
            time.sleep(2)

if __name__ == '__main__':
    main()
