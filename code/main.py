"""Terminal entry point: offline baseline or hosted model-directed evidence agent."""
import argparse
import hashlib
import json
from pathlib import Path
from batch_execution import execute_batch
from dataset_repository import DatasetRepository
from evidence_media import ImageEvidence
from financial_agent import run_agent_loop
from financial_tools import FinancialTools
from model_provider import AnthropicModel
from model_usage import BudgetedModel,write_usage_report

ROOT=Path(__file__).resolve().parents[1]

def fingerprint(dataset,config,code_root=None):
    digest=hashlib.sha256(json.dumps(config,sort_keys=True).encode())
    for path in sorted(Path(dataset).rglob('*')):
        if path.is_file():digest.update(path.relative_to(dataset).as_posix().encode());digest.update(path.read_bytes())
    for path in sorted((Path(code_root) if code_root else ROOT/'code').glob('*.py')):
        digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def run(dataset,output,checkpoint,provider='offline',model='',samples=False,budget=10,input_price=0,output_price=0,usage_report=None):
    repository=DatasetRepository(dataset)
    media=ImageEvidence(dataset,ROOT/'.cache'/'ocr')
    requests=repository.tables['sample_requests' if samples else 'requests']
    config=dict(provider=provider,model=model,samples=samples,budget=budget,input_price=input_price,output_price=output_price)
    signature=fingerprint(Path(dataset),config)
    prior=[]
    if Path(checkpoint).is_file():
        prior=[json.loads(line) for line in Path(checkpoint).read_text(encoding='utf-8').splitlines()]
        if any(r['fingerprint']!=signature for r in prior):raise ValueError('Use a new checkpoint for changed inputs/configuration')
    used=sum((r['usage'].get('input_tokens',0)*input_price+r['usage'].get('output_tokens',0)*output_price)/1000000 for r in prior)
    hosted=BudgetedModel(AnthropicModel(model),budget,input_price,output_price,used) if provider=='anthropic' else None
    def add_proof(result,tools):
        if tools.state is not None and tools.plan_ledger is not None:
            def flows(ledger):return [dict(date=f.day,amount=str(f.amount),evidence_id=f.evidence_id) for f in ledger.flows]
            result['proof']=dict(opening=str(tools.state.ledger.opening),minimum=str(tools.state.ledger.minimum),
                                 baseline_flows=flows(tools.state.ledger),plan_flows=flows(tools.plan_ledger))
        return result
    def solve(request):
        tools=FinancialTools(repository,request,media)
        if hosted:return add_proof(run_agent_loop(hosted,tools,request,tools.fallback),tools)
        tools.dispatch('retrieve_evidence',{})
        for image in tools.context['images']:tools.dispatch('inspect_image',{'image_id':image['image_id']})
        tools.dispatch('reconstruct_finances',{})
        tools.dispatch('evaluate_payment_plans',{})
        result=tools.dispatch('finish_decision',{})
        if tools.context['messages']:
            result['row']['decision_explanation']+=' Offline baseline: message amendments are not interpreted.'
        return add_proof(dict(row=result['row'],usage=dict(model_calls=0,input_tokens=0,output_tokens=0),trace=[]),tools)
    records=execute_batch(requests,solve,lambda r,why:FinancialTools(repository,r,media).fallback(why),
                          output,checkpoint,signature)
    usage={key:sum(r['usage'].get(key,0) for r in records) for key in ('model_calls','input_tokens','output_tokens')}
    report=dict(provider=provider,model=model or 'none',request_count=len(records),fingerprint=signature,
                config=config,
                output_sha256=hashlib.sha256(Path(output).read_bytes()).hexdigest(),usage=usage,
                fallback_rows=sum('insufficient evidence' in r['row']['decision_explanation'].lower() for r in records))
    Path(str(output)+'.manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if usage_report:
        report['usage_report']=write_usage_report(usage_report,records,provider,model,input_price,output_price,
                                                 signature,report['output_sha256'])
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=ROOT/'dataset')
    parser.add_argument('--output',type=Path,default=ROOT/'output.csv')
    parser.add_argument('--checkpoint',type=Path,default=ROOT/'runs'/'checkpoint.jsonl')
    parser.add_argument('--provider',choices=['offline','anthropic'],default='offline')
    parser.add_argument('--model',default='')
    parser.add_argument('--samples',action='store_true')
    parser.add_argument('--budget-usd',type=float,default=10)
    parser.add_argument('--input-price',type=float,default=None,help='USD per million input tokens; required for hosted run')
    parser.add_argument('--output-price',type=float,default=None,help='USD per million output tokens; required for hosted run')
    parser.add_argument('--usage-report',type=Path)
    args=parser.parse_args()
    if args.provider=='anthropic' and not args.model:parser.error('--model is required for hosted inference')
    if args.provider=='anthropic' and (args.input_price is None or args.output_price is None):
        parser.error('--input-price and --output-price are required for hosted cost accounting')
    report=args.usage_report or (args.output.parent/('sample_usage_report.md' if args.samples else 'usage_report.md'))
    run(args.dataset,args.output,args.checkpoint,args.provider,args.model,args.samples,args.budget_usd,
        args.input_price or 0,args.output_price or 0,report)
