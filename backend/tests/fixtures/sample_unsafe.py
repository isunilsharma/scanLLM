# Prompt injection risk
user_input = request.get("query")
prompt = f"You are a helpful assistant. Answer: {user_input}"

# eval on LLM output
result = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hello"}])
eval(result.choices[0].message.content)

# Missing max_tokens
client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hello"}])

# Hardcoded API key
api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdefgh"
