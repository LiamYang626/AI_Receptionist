def submit_message(client, assistant_id: str, thread, user_message: str):
    """
    Submits a user message to the specified thread and starts a run.
    Returns the newly created run.
    """
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
