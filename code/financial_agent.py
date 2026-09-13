"""Model-directed client-tool loop with bounded work and explicit safe fallback."""
import json
from agent_prompts import SYSTEM_PROMPT
from model_usage import aggregate_usage

MAX_AGENT_STEPS = 12

REQUEST_INPUT_FIELDS=('request_id','user_id','request_date','request_type','requested_amount',
                      'desired_completion_date','allows_partial_payment','request_text')

def request_input(request):
    """Project the specified input schema; sample answers stay evaluator-only."""
    return {key:request[key] for key in REQUEST_INPUT_FIELDS if key in request}

def run_agent_loop(model, tools, request, fallback, max_steps=MAX_AGENT_STEPS):
    messages=[dict(role='user',content='<input trust="untrusted">'+json.dumps(request_input(request),ensure_ascii=False)+'</input>')]
    usage=dict(input_tokens=0,output_tokens=0,model_calls=0)
    trace=[]
    finish_failures=0
    for step in range(max_steps):
        try:
            response=model.complete(SYSTEM_PROMPT,messages,tools.definitions)
        except Exception as error:
            # Provider exceptions can contain sensitive HTTP details; never persist them.
            failed=getattr(error,'usage',{})
            if failed.get('http_attempts'):
                usage=aggregate_usage([{'usage':usage},{'usage':dict(failed,model_calls=1)}])
            return dict(row=fallback('model provider unavailable; evidence insufficient'),usage=usage,trace=trace)
        current=dict(response.get('usage',{}),model_calls=1)
        if response.get('model'):current['models']={response['model']:1}
        usage=aggregate_usage([{'usage':usage},{'usage':current}])
        content=response.get('content',[])
        messages.append(dict(role='assistant',content=content,continuation=response.get('continuation',{})))
        calls=[b for b in content if b.get('type')=='tool_use']
        if not calls:
            messages.append(dict(role='user',content='Use finish_decision to emit a verified row. Text alone is not a valid result.'))
            continue
        results=[]
        finished=None
        for call in calls:
            try:
                if call.get('argument_error'):raise ValueError(call['argument_error'])
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
