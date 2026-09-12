"""Minimal Anthropic Messages client; credentials exist only in environment."""
import json
import os
import time
import urllib.error
import urllib.request

class AnthropicModel:
    def __init__(self,model):
        self.model=model
        self.key=os.environ.get('ANTHROPIC_API_KEY')
        if not self.key: raise ValueError('ANTHROPIC_API_KEY is not configured')

    def complete(self,system,messages,tools):
        payload=dict(model=self.model,max_tokens=2400,temperature=0,system=system,messages=messages,tools=tools)
        request=urllib.request.Request('https://api.anthropic.com/v1/messages',
            data=json.dumps(payload).encode('utf-8'),method='POST',
            headers={'Content-Type':'application/json','x-api-key':self.key,'anthropic-version':'2023-06-01'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if exc.code not in {429,500,502,503,529} or attempt==2:
                    raise RuntimeError('Model request failed with HTTP '+str(exc.code)) from None
            except urllib.error.URLError:
                if attempt==2: raise RuntimeError('Model connection failed') from None
            time.sleep(2**attempt)
        raise RuntimeError('Model retries exhausted')
