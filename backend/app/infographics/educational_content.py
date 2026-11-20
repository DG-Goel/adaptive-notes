"""Schema-aware word counting, independent of lossless transport accounting."""
import json

STORAGE={'id','note_id','videoId','sourceBlockId','source_id','source_ids','source_segment_ids',
 'body_start','body_end','anchor','position','timing','source_gaps','unresolved','visuals',
 'updatedAt','createdAt','version','status','isDemonstration','meta','visualArtifacts',
 'unplacedArtifacts','startSeconds','endSeconds','order','sequence','image','url','src',
 'type','level','language','displayMode','format','direction','align','render_status'}


def educational_text(index):
    if index.snapshot.media_type!='application/json': return index.text
    value=json.loads(index.text)
    def collect(item):
        if isinstance(item,str): return [item]
        if isinstance(item,(int,float)) and not isinstance(item,bool): return [str(item)]
        if isinstance(item,list): return [text for child in item for text in collect(child)]
        if isinstance(item,dict):
            return [text for key,child in item.items() if key not in STORAGE for text in collect(child)]
        return []
    # Unknown fields retain their values conservatively; only established storage
    # fields are excluded. Known derived visual copies are not counted twice.
    return '\n'.join(collect(value))
