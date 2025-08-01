class ChatCompletion:
    """Simplistic stub for openai.ChatCompletion.

    Returns a placeholder response when the real ``openai`` package is
    unavailable.
    """

    @staticmethod
    def create(*args, **kwargs):
        return {"choices": [{"message": {"content": "stub response"}}]}
