"""Independent derived-field recomputation before restoring any ownership."""
from types import SimpleNamespace
import json
from .segmentation_schema import parse_response
from .segmentation_budget import words
from .source_index import digest


class CheckpointIntegrityError(ValueError): pass


def validate_checkpoint(job,value,record):
    try:
        index=job.reading.index
        expected=job.reading.checkpoint_payload()
        for key in ('source_artifact_id','source_sha256','source_index_version','index_fingerprint',
                    'window_configuration','token_budget_configuration','configuration_sha256'):
            if value[key]!=expected[key]: raise ValueError(key)
        if value['prompt_version']!='master-segmentation-v1' or value['prompt_hash']!=job.prompt_hash or value['model']!=job.planner.config.model:
            raise ValueError('prompt/model')
        cursor=0; starts=[]; group=None
        fields={'start','end','category','title','focus','density','estimated_items','boundary_reason','supplementary_ids','supports_start'}
        for segment in value['manifest']:
            expected_fields=fields|{'id','source_artifact_id','source_sha256','source_start','source_end',
                'start_position','end_position','continuation_group','source_tokens','source_token_kind','source_words'}
            if set(segment)!=expected_fields: raise ValueError('segment field set')
            end=segment['end_position']
            if type(end) is not int or segment['start_position']!=cursor or not cursor<=end<len(index.units): raise ValueError('positions')
            blocks=index.units[cursor:end+1]
            row={k:segment[k] for k in fields}
            forced=segment['boundary_reason']=='context_limit'
            # A sentinel next block allows the normal forced-boundary validator.
            source=blocks+(index.units[end+1:end+2] if forced else ())
            pending=source[-1].id if forced and len(source)>len(blocks) else None
            window=SimpleNamespace(source=source,final_document_window=end==len(index.units)-1)
            parse_response(json.dumps(dict(segments=[row],pending_from=pending)),window,forced=forced,previous_starts=starts)
            derived=dict(start=blocks[0].id,end=blocks[-1].id,source_start=blocks[0].source_start,
                source_end=blocks[-1].source_end,source_artifact_id=index.snapshot.source_id,source_sha256=index.snapshot.sha256,
                id='S'+digest((index.fingerprint+blocks[0].id+blocks[-1].id).encode())[:24],
                source_tokens=sum(b.token_count for b in blocks),source_words=words(''.join(b.text for b in blocks)),source_token_kind='estimated')
            if any(segment[k]!=v for k,v in derived.items()): raise ValueError('derived fields')
            if forced and group is None: group='CG'+digest((index.fingerprint+blocks[0].id).encode())[:24]
            if segment['continuation_group']!=group: raise ValueError('continuation group')
            if not forced: group=None
            starts.append(segment['start']); cursor=end+1
        if value['continuation']!=group or value['state']['cursor']!=cursor: raise ValueError('cursor/continuation')
        if (value['processing_status']=='complete')!=(cursor==len(index.units)):
            raise ValueError('completion status')
        if value['visualization_budget']!=job.visual_budget: raise ValueError('visualization budget')
    except (KeyError,TypeError,ValueError,IndexError) as error:
        raise CheckpointIntegrityError('Checkpoint manifest integrity: '+str(error)[:120]) from None
