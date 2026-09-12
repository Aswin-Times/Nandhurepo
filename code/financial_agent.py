"""Model-directed client-tool loop with bounded work and explicit safe fallback."""
import json
from agent_prompts import SYSTEM_PROMPT

MAX_AGENT_STEPS = 12

def run_agent_loop(model, tools, request, fallback, max_steps=MAX_AGENT_STEPS):
    messages=[dict(role='user',content='<input trust="untrusted">'+json.dumps(request,ensure_ascii=False)+'</input>')]
    usage=dict(input_tokens=0,output_tokens=0,model_calls=0)
    trace=[]
    finish_failures=0
    for step in range(max_steps):
        try:
            response=model.complete(SYSTEM_PROMPT,messages,tools.definitions)
        except Exception:
            # Provider exceptions can contain sensitive HTTP details; never persist them.
            return dict(row=fallback('model provider unavailable; evidence insufficient'),usage=usage,trace=trace)
        usage['model_calls']+=1
        for key in ('input_tokens','output_tokens'):
            usage[key]+=int(response.get('usage',{}).get(key,0))
        content=response.get('content',[])
        messages.append(dict(role='assistant',content=content))
        calls=[b for b in content if b.get('type')=='tool_use']
        if not calls:
            messages.append(dict(role='user',content='Use finish_decision to emit a verified row. Text alone is not a valid result.'))
            continue
        results=[]
        finished=None
        for call in calls:
            try:
                result=tools.dispatch(call['name'],call.get('input',{}))
            except (ValueError,KeyError,TypeError) as exc:
                result=dict(error=dict(code='invalid_tool_arguments',message=str(exc),
                                       recovery='Correct arguments using retrieved evidence; do not guess.'))
                if call['name']=='finish_decision':
                    finish_failures+=1
            except Exception:
                result=dict(error=dict(code='internal_tool_error',message='Tool failed; no financial result accepted',
                                       recovery='Retry or finish with explicit uncertainty'))
            image=result.pop('_model_image',None)
            trace.append(dict(step=step,tool=call['name'],arguments=call.get('input',{}),result=result))
            tool_content=json.dumps(result,ensure_ascii=False)
            if image:
                tool_content=[dict(type='text',text=tool_content),image]
            results.append(dict(type='tool_result',tool_use_id=call['id'],
                                content=tool_content,is_error='error' in result))
            if 'row' in result:
                finished=result['row']
        if finished is not None:
            return dict(row=finished,usage=usage,trace=trace)
        if finish_failures>=2:
            return dict(row=fallback('output validation failed after one repair; evidence insufficient'),usage=usage,trace=trace)
        messages.append(dict(role='user',content=results))
    return dict(row=fallback('agent step cap reached; evidence insufficient'),usage=usage,trace=trace)
