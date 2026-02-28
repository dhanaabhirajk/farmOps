import os
from mistralai import Mistral

api_key = "19342269-873E-4A96-A43A-B7139702E619"
# api_key = "WEOdoOmQ0W7BFMfg9noGhDOkoY0HPF7P"
model = "ministral-3b-2512"

client = Mistral(api_key=api_key)

chat_response = client.chat.complete(
    model = model,
    messages = [
        {
            "role": "user",
            "content": "hi",
        },
    ]
)
print(chat_response.choices[0].message.content)