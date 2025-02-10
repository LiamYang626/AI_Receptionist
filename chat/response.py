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


def pretty_print(voice_tts, message, enable_tts: bool = False):
    """
    Prints the last assistant message. If enable_tts is True,
    uses macOS 'say' command for TTS (adjust if on another OS).
    """
    if not message:
        return
    role = message.role
    content = message.content[0].text.value

    print(f"{role}: {content}")

    if enable_tts and role == "assistant":
        os.system(f'say -v "{voice_tts}" "{content}"')
