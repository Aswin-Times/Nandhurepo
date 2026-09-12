"""Package only a reconciled full hosted-agent run; never include local secrets."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from independent_validation import validate_artifacts

def validate_manifest_freshness(root,manifest):
    from main import fingerprint
    root=Path(root)
    if 'config' not in manifest or fingerprint(root/'dataset',manifest['config'],root/'code')!=manifest['fingerprint']:
        raise ValueError('Final-run artifact is stale for current dataset/code/configuration')

def package_submission(root,output,usage_report,manifest,destination):
    root=Path(root);output=Path(output);usage_report=Path(usage_report)
    actual=hashlib.sha256(output.read_bytes()).hexdigest()
    if actual!=manifest.get('output_sha256'):raise ValueError('Output does not match final-run manifest')
    if manifest.get('request_count')!=250:raise ValueError('Manifest is not a full evaluation run')
    if manifest.get('provider')=='offline' or not manifest.get('usage',{}).get('model_calls'):
        raise ValueError('Offline baseline cannot be certified as hosted-agent submission')
    if manifest.get('fallback_rows',0):raise ValueError('Unresolved fallback rows require review before release')
    text=usage_report.read_text(encoding='utf-8')
    if actual not in text or manifest.get('fingerprint','missing') not in text:
        raise ValueError('Usage report does not correspond to output/configuration')
    entries=[(p,'code/'+p.name) for p in sorted((root/'code').glob('*.py'))]
    entries.extend((p,'tests/'+p.name) for p in sorted((root/'tests').glob('*.py')))
    entries.extend((root/name,name) for name in ('requirements.txt','SPEC.md','CONSTANTS.md','INTERVIEW.md','EXPERIMENTS.md') if (root/name).is_file())
    entries.append((root/'SOLUTION_README.md','README.md'))
    entries.append((usage_report,'evaluation/usage_report.md'))
    if (root/'evaluation'/'offline_golden.sha256').is_file():
        entries.append((root/'evaluation'/'offline_golden.sha256','evaluation/offline_golden.sha256'))
    destination=Path(destination)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for path,name in entries:archive.write(path,name)
    return dict(zip_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),files=len(entries))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('output.csv'))
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--usage-report',type=Path,default=Path('code/evaluation/usage_report.md'))
    parser.add_argument('--zip',type=Path,default=Path('code.zip'))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    validation=validate_artifacts(root/'dataset',args.output,args.checkpoint)
    if validation['failures']:raise SystemExit(json.dumps(validation,indent=2))
    manifest=json.loads(Path(str(args.output)+'.manifest.json').read_text(encoding='utf-8'))
    validate_manifest_freshness(root,manifest)
    print(json.dumps(package_submission(root,args.output,args.usage_report,manifest,args.zip),indent=2))
