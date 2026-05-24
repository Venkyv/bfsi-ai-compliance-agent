import os, sys
sys.path.insert(0, '.')
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('OPENROUTER_API_KEY', '')
print('Key loaded:', key[:20] + '...' if key else 'NOT FOUND')

client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=key)
r = client.chat.completions.create(
    model='meta-llama/llama-3.3-70b-instruct:free',
    max_tokens=50,
    messages=[{'role': 'user', 'content': 'Reply with: OK'}]
)
print('Response:', r.choices[0].message.content)