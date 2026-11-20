"""Round 2 transport through the shared scheduler and Stage A quota ledger."""
import json
import time
from hashlib import sha256

from app.extraction.document_authorization import DocumentStageARecord
from app.extraction.llm_provider import GroqProviderError
from app.extraction.organization_extraction import _BoundProvider
from app.extraction.organization_scheduler import (
    Identity, LocalQuotaAdmission, OrganizationScheduler, SchedulerHold, configuration_fingerprint,
    digest, load_organizations,
)
from app.extraction.stage_a_bridge import LocalCredentialApproval, StageAAuthorization, verify_local_credential
from app.extraction.token_budget import TokenBudget
from run_authorized_java import check_stage_capacity, save

SLOTS = (6, 7, 8, 9, 10)


def prepare_approvals(manifest, inventory, config):
    identities = [Identity.model_validate({key: row[key] for key in Identity.model_fields})
                  for row in inventory]
    if (not identities or len({i.slot for i in identities}) != len(identities)
            or not {i.slot for i in identities} <= set(SLOTS)):
        raise SchedulerHold('Supply reviewed inventory for distinct slots within 6–10')
    authorization = 'Operator-authorized Round 2 analysis of the exact prepared notes manifest'
    requests = {}
    for request in manifest['requests']:
        if 'skipped' in request:
            continue
        request_id = request['request_id']
        requests[request_id] = {}
        for identity, row in zip(identities, inventory):
            if not identity.valid_at(time.time()):
                raise SchedulerHold(f'Inventory review for slot {identity.slot} is expired or future-dated')
            common = dict(stage='A', provider='Groq', model=config.model, run_id=request_id,
                operator='requesting operator', authorization=authorization,
                request_sha256=digest(request['payload']), organization=identity.organization,
                project=identity.project, credential_id=identity.credential_id,
                credential_sha256=identity.credential_sha256)
            limits = tuple({'scope': 'organization', 'metric': key, 'limit': value}
                           for key, value in row['configured_provider_limits'].items())
            record = DocumentStageARecord(**common, source_id='DOCUMENT', decision='PASS', limits=limits)
            approval = LocalCredentialApproval(**common, evidence_kind=row['verification_method'],
                ownership_evidence=identity.ownership_evidence, verified_by=identity.verified_by,
                verified_at=identity.verified_at, expires_at=identity.expires_at,
                authorization_evidence=authorization)
            requests[request_id][str(identity.slot)] = dict(record=record.model_dump(mode='json'),
                credential_approval=approval.model_dump(mode='json'))
    verified_inventory = [identity.model_dump(mode='json') for identity in identities]
    return dict(manifest_sha256=digest(manifest), inventory=verified_inventory, requests=requests,
        configuration_review=dict(target_sha256=configuration_fingerprint(config), evidence=authorization))


class Round2Authorization(StageAAuthorization):
    def __init__(self, approved, request):
        super().__init__(DocumentStageARecord.model_validate_json(
            json.dumps(approved['record'])), approved['credential_approval'])
        self.request = request

    def local_record_type(self):
        return DocumentStageARecord

    def permits_registry(self, scheduler):
        return scheduler.rotation_slots == SLOTS and set(scheduler.organizations.enabled) <= set(SLOTS)

    def expected_payload(self, request_id):
        if request_id != self.request['request_id']:
            raise SchedulerHold('Round 2 request binding mismatch')
        return self.request['payload']


def open_scheduler(root, inventory, environment, config, review):
    identities = [Identity.model_validate({key: row[key] for key in Identity.model_fields})
                  for row in inventory]
    if not identities or not {identity.slot for identity in identities} <= set(SLOTS):
        raise SchedulerHold('Round 2 requires verified organization inventory for slots 6–10')
    environment = dict(environment)
    for identity in identities:
        key = environment.get(f'GROQ_ORG_{identity.slot}_API_KEY') or environment.get(
            f'GROQ_API_KEY_{identity.slot}')
        if not key or sha256(key.encode()).hexdigest() != identity.credential_sha256:
            raise SchedulerHold(f'Configured key does not match reviewed slot {identity.slot}')
        environment.setdefault(f'GROQ_ORG_{identity.slot}_ID', identity.organization)
        environment.setdefault(f'GROQ_ORG_{identity.slot}_ENABLED', 'true')
        environment[f'GROQ_ORG_{identity.slot}_API_KEY'] = key
    organizations = load_organizations(identities, environment, slots=SLOTS)
    return OrganizationScheduler(root / 'data/live_state/organization.sqlite',
        organizations, config, configuration_review=review, rotation_slots=SLOTS)


def dispatch(scheduler, request, approvals, output, validate):
    request_id, payload = request['request_id'], request['payload']
    budget = TokenBudget(**request['budget'])
    gates, admissions = {}, {}
    for identity in scheduler.organizations.identities:
        approved = approvals.get(str(identity.slot))
        if not approved or identity.slot not in scheduler.organizations.enabled:
            continue
        gate = Round2Authorization(approved, request)
        record = gate.record
        verify_local_credential(record, LocalCredentialApproval.model_validate(approved['credential_approval']),
                                scheduler.organizations.key(identity), time.time())
        admission = LocalQuotaAdmission(organization=identity.organization, project=identity.project,
            credential_id=identity.credential_id, credential_sha256=identity.credential_sha256,
            request_id=request_id, request_sha256=digest(payload), configuration_sha256=scheduler.config_hash,
            authorization=record.authorization, windows=record.limits)
        if record.run_id != request_id or record.request_sha256 != admission.request_sha256:
            raise SchedulerHold('Round 2 approval does not bind the current request')
        if (record.organization, record.project, record.credential_id) != (
                identity.organization, identity.project, identity.credential_id):
            raise SchedulerHold('Round 2 approval identity mismatch')
        try:
            check_stage_capacity(identity, admission, budget, dict(zip(
                ('RPM', 'RPD', 'TPM', 'TPD'), scheduler.configuration.scheduler_ceilings)))
        except SchedulerHold:
            continue
        gates[identity.organization] = gate
        admissions[identity.organization] = admission
    scheduler.organizations.check_metadata(payload)
    identity, admission = scheduler.claim(request_id, digest(payload), budget.input_tokens,
                                         budget.max_output_tokens, admissions)
    gate = gates[identity.organization]
    claimed = False
    try:
        gate.claim(scheduler, identity, admission, request_id, payload, budget)
        claimed = True
        provider = _BoundProvider(scheduler, identity, admission, request_id, payload, budget, None,
            lambda receipt: save(output / (request_id + '.receipt.json'), receipt))
        system, user = payload['messages']
        content = provider.generate(user['content'], system=system['content'],
            temperature=payload['temperature'], max_tokens=payload['max_tokens'])
        result = validate(content)
        scheduler.organizations.check_metadata(result)
        save(output / (request_id + '.result.json'), result)
        scheduler.finish(request_id, 'success')
        return result
    except Exception as error:
        with scheduler.transaction() as db:
            state = db.execute('SELECT state FROM operations WHERE id=?', (request_id,)).fetchone()[0]
        if state == 'claimed':
            scheduler.finish(request_id, 'uncertain' if isinstance(error, OSError) and claimed
                             else 'validation_failed')
        if isinstance(error, GroqProviderError):
            raise
        raise SchedulerHold('Round 2 request failed authorization or validation') from None
    finally:
        if claimed:
            gate.reconcile_local(scheduler, request_id)
