from anthropic import Anthropic

client = Anthropic()

def chat(user_message):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}]
    )
    return message.content[0].text
