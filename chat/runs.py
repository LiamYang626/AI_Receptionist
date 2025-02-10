import time


def wait_on_run(client, run, thread):
    """
    Polls run status until it is no longer 'queued' or 'in_progress'.
    """
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            print("Run failed:", run_status.last_error)
            break
        time.sleep(2)
