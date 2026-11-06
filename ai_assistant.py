"""AI is opt-in and only returns suggestions; never modifies campaign data."""

SYSTEM_INSTRUCTIONS = """You are a creative consultant to a tabletop RPG Dungeon Master.
The user's existing campaign data is CANON: preserve names, established facts and tone.
Never claim an invented detail is established canon. Label new ideas as suggestions.
If a reference contradicts the user's campaign, call that out before proposing fixes.
Be inventive but concise and actionable. Don't reproduce copyrighted sourcebooks.
Do not automatically decide outcomes for the DM. Write polished, natural paragraphs rather than excessive headings or bullet points. Use a heading only when it genuinely improves clarity. Do not output raw formatting instructions or code fences. Your suggestions should be straightforward to paste into a campaign document."""


def make_context(data, include_refs=False):
    parts = [f"TITLE: {data.get('title','')}", f"GAME SYSTEM: {data.get('system','')}",
             f"LEVELS: {data.get('levels','')}", f"TONE: {data.get('tone','')}",
             f"PREMISE: {data.get('pitch','')}", f"SETTING: {data.get('setting','')}",
             f"STORY ARC: {data.get('story_arc','')}"]
    for e in data.get("entries", [])[:55]:
        parts.append(f"{e.get('category')}: {e.get('title')}\n{e.get('content','')[:1400]}")
    if include_refs:
        for r in data.get("references", [])[:8]:
            parts.append(f"SUPPORTING MATERIAL ({r['name']}):\n{r.get('text', '')[:4500]}")
    return "\n\n".join(parts)[:32000]


def consult_ai(data, question, key, model="gpt-4.1-mini", include_refs=False,
               field_target=None, source_context="", source_text="",
               source_grounded=False, discussion=False, history=None):
    if not key.strip():
        raise ValueError("Enter an OpenAI API key to enable the AI consultant.")
    if not question.strip():
        raise ValueError("Write a question for your AI consultant.")
    from openai import OpenAI
    from oracle_grounding import SOURCE_RULES, history_messages, verify_grounded_draft, verify_new_names
    client = OpenAI(api_key=key.strip(), timeout=65)
    targeted=bool(field_target and not discussion)
    verify_quote=False
    if targeted:
        from oracle_field import field_request_messages, clean_field_revision
        messages=field_request_messages(data,question,field_target,include_refs,
                   source_context=source_context,source_grounded=source_grounded)
        instructions=messages[0]['content']
        provider_input=messages[1]['content']
        verify_quote=bool(source_grounded and not str(field_target.get('baseline') or '').strip())
        if verify_quote:
            instructions+=('\nReturn ONLY JSON object with draft and evidence; evidence is an '
                           'array containing an exact quotation from the source excerpts (12+ chars). '
                           'Never introduce unsupported named characters or organizations.')
    else:
        instructions=SYSTEM_INSTRUCTIONS + ('\n'+SOURCE_RULES if source_grounded else '')
        if source_grounded:
            context=('CAMPAIGN: '+str(data.get('title') or '')[:160]+'\n'
                     'PREMISE: '+str(data.get('pitch') or '')[:650]+'\n'
                     'SETTING: '+str(data.get('setting') or '')[:650]+'\n'
                     'USER-UPLOADED SOURCE EXCERPTS:\n'+(source_context or '[No source available]'))
        else:
            context=make_context(data,include_refs)
        provider_input=[{'role':'user','content':'CAMPAIGN CONTEXT (reference only):\n'+context}]
        provider_input+=history_messages(history)
        provider_input.append({'role':'user','content':question})
    response=client.responses.create(
        model=model.strip() or 'gpt-4.1-mini',instructions=instructions,
        input=provider_input,max_output_tokens=1400)
    raw=response.output_text or ''
    if targeted:
        from oracle_field import validate_field_scope, clean_field_revision
        result=verify_grounded_draft(raw,source_text) if verify_quote else clean_field_revision(raw)
        if source_grounded and not verify_quote:
            verify_new_names(result,source_text+'\n'+str(field_target.get('baseline') or ''))
        return validate_field_scope(result,field_target,question)
    return raw
