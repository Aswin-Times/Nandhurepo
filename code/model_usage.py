"""Measured API usage reconciliation and conservative request-budget reservation."""
import json
from decimal import Decimal as D
from pathlib import Path

class BudgetedModel:
    def __init__(self,provider,budget,input_price,output_price,used=0):
        self.provider=provider;self.budget=D(str(budget));self.used=D(str(used))
        self.input_price=D(str(input_price));self.output_price=D(str(output_price))
    def complete(self,system,messages,tools):
        # UTF-8 bytes upper-bound raw tokenizer units; add room for protocol framing.
        envelope=len(json.dumps([system,messages,tools],ensure_ascii=False).encode('utf-8'))+2000
        reservation=(D(envelope)*self.input_price+D(2400)*self.output_price)/1000000
        if self.used+reservation>self.budget:raise RuntimeError('Configured model budget exhausted before request')
        result=self.provider.complete(system,messages,tools)
        usage=result.get('usage',{})
        self.used+=(D(usage.get('input_tokens',0))*self.input_price+D(usage.get('output_tokens',0))*self.output_price)/1000000
        return result

def write_usage_report(path,records,provider,model,input_price,output_price,fingerprint,output_hash):
    usage={k:sum(r['usage'].get(k,0) for r in records) for k in ('model_calls','input_tokens','output_tokens')}
    total=usage['input_tokens']+usage['output_tokens'];count=len(records)
    cost=(D(usage['input_tokens'])*D(str(input_price))+D(usage['output_tokens'])*D(str(output_price)))/1000000
    result=dict(**usage,total_tokens=total,average_tokens_per_request=total/count if count else 0,
                estimated_cost_usd=float(cost),average_cost_usd=float(cost)/count if count else 0)
    text=(f"# Model usage report\n\nProvider: {provider}. Model: {model or 'none'}. Requests: {count}.\n\n"
          f"| Calls | Input tokens | Output tokens | Total tokens | Average tokens/request |\n|---|---|---|---|---|\n"
          f"| {usage['model_calls']} | {usage['input_tokens']} | {usage['output_tokens']} | {total} | {result['average_tokens_per_request']:.2f} |\n\n"
          f"Estimated total cost: USD {cost:.6f}. Average per request: USD {result['average_cost_usd']:.6f}.\n"
          f"Configured USD/million input tokens: {input_price}; output: {output_price}.\n\n"
          f"Input/config fingerprint: `{fingerprint}`. Output SHA-256: `{output_hash}`.\n\n"
          "Usage is summed from the row checkpoints of this run, including resumed rows. Hosted calls are measured from provider usage, not guessed from text length. "
          "Failed HTTP requests without returned usage cannot be reconciled from the API response. Development-chat tokens are not the submitted runtime's model usage.\n")
    if provider=='offline':text+='\nThis is an OFFLINE BASELINE, not a hosted-agent evaluation. No paid model calls occurred.\n'
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return result
