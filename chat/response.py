import os


def get_response(client, thread):
    """
    Returns the newest list of messages from the thread.
    """
    new_messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        order="desc",
        limit=1    # Change it to 2 if you want the user message also
    )
    messages_list = list(new_messages)
    if not messages_list:
        return None
    return messages_list[0]


def get_full_response(client, thread):
    """
    Returns the full list of messages (in ascending order) from the thread.
    """
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

