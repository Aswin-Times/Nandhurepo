"""Measured API usage reconciliation and conservative request-budget reservation."""
import json
from decimal import Decimal as D
from pathlib import Path

def aggregate_usage(records):
    keys=('model_calls','input_tokens','output_tokens','http_attempts','usage_missing_calls','cost_reported_calls')
    result={k:sum(r['usage'].get(k,0) for r in records) for k in keys}
    result['reported_cost_usd']=float(sum((D(str(r['usage'].get('reported_cost_usd',0))) for r in records),D(0)))
    result['budget_cost_usd']=float(sum((D(str(r['usage'].get('budget_cost_usd',0))) for r in records),D(0)))
    models={}
    for record in records:
        for model,count in record['usage'].get('models',{}).items():models[model]=models.get(model,0)+count
    result['models']=models
    return result

def reconciled_cost(usage,input_price,output_price):
    # Estimate unreported calls only; never add an estimate on top of a measured charge.
    if 'budget_cost_usd' in usage:return D(str(usage['budget_cost_usd']))
    if usage.get('cost_reported_calls')==usage.get('model_calls',1):
        return D(str(usage.get('reported_cost_usd',0)))
    return (D(usage.get('input_tokens',0))*D(str(input_price))+D(usage.get('output_tokens',0))*D(str(output_price)))/1000000

class BudgetedModel:
    def __init__(self,provider,budget,input_price,output_price,used=0):
        self.provider=provider;self.budget=D(str(budget));self.used=D(str(used))
        self.input_price=D(str(input_price));self.output_price=D(str(output_price))
    def complete(self,system,messages,tools):
        # UTF-8 bytes upper-bound raw tokenizer units; add room for protocol framing.
        envelope=len(json.dumps([system,messages,tools],ensure_ascii=False).encode('utf-8'))+2000
        reservation=(D(envelope)*self.input_price+D(2400)*self.output_price)/1000000*getattr(self.provider,'max_http_attempts',3)
        if self.used+reservation>self.budget:raise RuntimeError('Configured model budget exhausted before request')
        try:result=self.provider.complete(system,messages,tools)
        except Exception as error:
            usage=getattr(error,'usage',{})
            if usage.get('http_attempts'):
                charge=D(str(usage['reported_cost_usd'])) if usage.get('cost_reported_calls') else reservation
                self.used+=charge;usage['budget_cost_usd']=float(charge)
            raise
        usage=result.get('usage',{})
        charge=(D(usage.get('input_tokens',0))*self.input_price+D(usage.get('output_tokens',0))*self.output_price)/1000000
        if usage.get('cost_reported_calls'):charge=D(str(usage['reported_cost_usd']))
        elif usage.get('usage_missing_calls'):charge=reservation
        self.used+=charge;usage['budget_cost_usd']=float(charge)
        return result

def write_usage_report(path,records,provider,model,input_price,output_price,fingerprint,output_hash):
    usage=aggregate_usage(records)
    total=usage['input_tokens']+usage['output_tokens'];count=len(records)
    cost=(D(usage['input_tokens'])*D(str(input_price))+D(usage['output_tokens'])*D(str(output_price)))/1000000
    result=dict(**usage,total_tokens=total,average_tokens_per_request=total/count if count else 0,
                estimated_cost_usd=float(cost),average_cost_usd=float(cost)/count if count else 0,
                usage_complete=not usage['usage_missing_calls'])
    events=[e for r in records for e in r.get('http_events',[])]
    statuses={};phases={};logical={}
    for e in events:
        status=str(e['status']) if e.get('status') is not None else 'NETWORK/NO_HTTP'
        statuses[status]=statuses.get(status,0)+1
        phase=e['key_phase'];phases[phase]=phases.get(phase,0)+1
        logical.setdefault((e.get('request_id'),e.get('logical_call')),[]).append(e)
    http=dict(attempts=len(events),statuses=statuses,key_phases=phases,
              fallback_activations=sum(any(e['key_phase']=='fallback' for e in group) for group in logical.values()),
              fallback_recoveries=sum(any(e['key_phase']=='fallback' and e.get('status')==200 for e in group) for group in logical.values()),
              missing_attempt_usage=sum(e.get('input_tokens') is None or e.get('output_tokens') is None for e in events),
              measured_input_tokens=sum(e.get('input_tokens') or 0 for e in events),
              measured_output_tokens=sum(e.get('output_tokens') or 0 for e in events),
              measured_total_tokens=sum(e.get('total_tokens') or 0 for e in events),
              reported_cost_attempts=sum(e.get('reported_cost_usd') is not None for e in events))
    result['http_diagnostics']=http
    if http['missing_attempt_usage']:result['usage_complete']=False
    text=(f"# Model usage report\n\nProvider: {provider}. Model: {model or 'none'}. Requests: {count}.\n\n"
          f"| Calls | Input tokens | Output tokens | Total tokens | Average tokens/request |\n|---|---|---|---|---|\n"
          f"| {usage['model_calls']} | {usage['input_tokens']} | {usage['output_tokens']} | {total} | {result['average_tokens_per_request']:.2f} |\n\n"
          f"Estimated total cost: USD {cost:.6f}. Average per request: USD {result['average_cost_usd']:.6f}.\n"
          f"Configured USD/million input tokens: {input_price}; output: {output_price}.\n\n"
          f"Provider-reported charge: USD {usage['reported_cost_usd']:.6f}; available for {usage['cost_reported_calls']}/{usage['model_calls']} calls. This is not the configured-price estimate.\n"
          f"Usage completeness: {'INCOMPLETE' if usage['usage_missing_calls'] else 'complete'}; calls missing token usage: {usage['usage_missing_calls']}. Token totals cover only measured responses.\n"
          f"HTTP attempts: {usage['http_attempts']}. Returned models (calls): {json.dumps(usage['models'],sort_keys=True)}.\n\n"
          f"Input/config fingerprint: `{fingerprint}`. Output SHA-256: `{output_hash}`.\n\n"
          "Usage is summed from the row checkpoints of this run, including resumed rows. Hosted calls are measured from provider usage, not guessed from text length. "
          "Failed HTTP requests without returned usage cannot be reconciled from the API response. Retry attempts without returned usage may incur unmeasured charges; configured-price estimates exclude such charges. Development-chat tokens are not the submitted runtime's model usage.\n")
    if events:
        text+=('\n## Per-attempt reconciliation\n\n'
               f"HTTP/network attempts observed: {http['attempts']}; statuses: {json.dumps(statuses,sort_keys=True)}.\n"
               f"Key phases: {json.dumps(phases,sort_keys=True)}; fallback activations: {http['fallback_activations']}; recoveries: {http['fallback_recoveries']}.\n"
               f"Attempts without token usage: {http['missing_attempt_usage']}; attempts with reported cost: {http['reported_cost_attempts']}.\n"
               f"HTTP usage completeness: {'INCOMPLETE' if http['missing_attempt_usage'] else 'complete'}. "
               'Tokens and provider charges above are measured-response subtotals; total cost UNKNOWN when any attempt has no returned cost.\n')
    if provider=='offline':text+='\nThis is an OFFLINE BASELINE, not a hosted-agent evaluation. No paid model calls occurred.\n'
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return result
