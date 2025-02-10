from chat.messages import submit_message


def create_thread_and_run(client, assistant_id, user_input: str):
    """
    Creates a new thread, submits the user message, and returns (thread, run).
    """
    thread = client.beta.threads.create()
    run = submit_message(client, assistant_id, thread, user_input)
    return thread, run


def continue_thread_and_run(client, assistant_id, thread, user_input: str):
    """
    Submits a user message to an existing thread and returns the run.
    """
    return submit_message(client, assistant_id, thread, user_input)

