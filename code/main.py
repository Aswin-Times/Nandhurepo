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

ROOT=Path(__file__).resolve().parents[1]

def fingerprint(dataset,config):
    digest=hashlib.sha256(json.dumps(config,sort_keys=True).encode())
    for path in sorted(Path(dataset).rglob('*')):
        if path.is_file():digest.update(path.relative_to(dataset).as_posix().encode());digest.update(path.read_bytes())
    for path in sorted((ROOT/'code').glob('*.py')):
        digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def run(dataset,output,checkpoint,provider='offline',model='',samples=False):
    repository=DatasetRepository(dataset)
    media=ImageEvidence(dataset,ROOT/'.cache'/'ocr')
    hosted=AnthropicModel(model) if provider=='anthropic' else None
    requests=repository.tables['sample_requests' if samples else 'requests']
    config=dict(provider=provider,model=model,samples=samples)
    signature=fingerprint(Path(dataset),config)
    def solve(request):
        tools=FinancialTools(repository,request,media)
        if hosted:return run_agent_loop(hosted,tools,request,tools.fallback)
        tools.dispatch('retrieve_evidence',{})
        for image in tools.context['images']:tools.dispatch('inspect_image',{'image_id':image['image_id']})
        tools.dispatch('reconstruct_finances',{})
        tools.dispatch('evaluate_payment_plans',{})
        result=tools.dispatch('finish_decision',{})
        if tools.context['messages']:
            result['row']['decision_explanation']+=' Offline baseline: message amendments are not interpreted.'
        return dict(row=result['row'],usage=dict(model_calls=0,input_tokens=0,output_tokens=0),trace=[])
    records=execute_batch(requests,solve,lambda r,why:FinancialTools(repository,r,media).fallback(why),
                          output,checkpoint,signature)
    usage={key:sum(r['usage'].get(key,0) for r in records) for key in ('model_calls','input_tokens','output_tokens')}
    report=dict(provider=provider,model=model or 'none',request_count=len(records),fingerprint=signature,
                output_sha256=hashlib.sha256(Path(output).read_bytes()).hexdigest(),usage=usage,
                fallback_rows=sum('insufficient evidence' in r['row']['decision_explanation'].lower() for r in records))
    Path(str(output)+'.manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
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
    args=parser.parse_args()
    if args.provider=='anthropic' and not args.model:parser.error('--model is required for hosted inference')
    run(args.dataset,args.output,args.checkpoint,args.provider,args.model,args.samples)
