#!/usr/bin/env python3
"""Use HA 2026.10.4's real schemas/templates, with no running owner HA."""
import asyncio
from copy import deepcopy
from pathlib import Path
import tempfile
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA,PLATFORM_SCHEMA
from homeassistant.components.blueprint.models import Blueprint
from homeassistant.components.homeassistant.triggers import state,event
from homeassistant.components.template import trigger as template_trigger
from homeassistant.components.mobile_app.device_action import ACTION_SCHEMA
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.util import yaml

ROOT=Path(__file__).resolve().parents[1]

async def main():
    raw=yaml.load_yaml(str(ROOT/'homeassistant/ltm-status.yaml'))
    blueprint=Blueprint(deepcopy(raw),schema=AUTOMATION_BLUEPRINT_SCHEMA,expected_domain='automation')
    assert not blueprint.validate()
    defaults={key:item['default'] for key,item in blueprint.inputs.items() if 'default' in item}
    with tempfile.TemporaryDirectory(prefix='ltm-fictional-ha-') as root:
        hass=HomeAssistant(root)
        for entity in ('sensor.ltm_beta_drift','sensor.ltm_stable_drift'):
            inputs={**defaults,'phone':'f'*32,'status_entity':entity}
            filled=yaml.substitute(raw,inputs);filled.pop('blueprint')
            config=PLATFORM_SCHEMA(filled)
            for index,trigger in enumerate(config['triggers']):
                schemas={'state':state.TRIGGER_STATE_SCHEMA,'template':template_trigger.TRIGGER_SCHEMA,'event':event.TRIGGER_SCHEMA}
                config['triggers'][index]=schemas[trigger['platform']](trigger)
            action=ACTION_SCHEMA(config['actions'][0])
            for kind in ('error','pressure','offline','recovery','test'):
                variables={**inputs,'watched':entity,'kind':kind}
                for field in ('title','message'):
                    value=Template(action[field].template,hass)
                    rendered=value.async_render(variables)
                    assert rendered and 'PRIVATE' not in rendered
                variables['test_note']='Fiktiv note {{ 7 * 7 }}'
                if kind=='test':
                    value=Template(action['message'].template,hass)
                    assert 'Fiktiv note {{ 7 * 7 }}' in value.async_render(variables)
            heartbeat=next(t for t in config['triggers'] if t['id']=='offline')['value_template']
            heartbeat.hass=hass
            assert heartbeat.async_render({'watched':entity}) is True
            from datetime import datetime,timezone
            hass.states.async_set(entity,'waiting',{'updated_at':datetime.now(timezone.utc).isoformat()})
            assert heartbeat.async_render({'watched':entity}) is False
            hass.states.async_set(entity,'unknown',{'updated_at':datetime.now(timezone.utc).isoformat()})
            assert heartbeat.async_render({'watched':entity}) is False
            hass.states.async_set(entity,'waiting',{'updated_at':'2000-01-01T00:00:00+00:00'})
            assert heartbeat.async_render({'watched':entity}) is True
            hass.states.async_set(entity,'stopped')
            assert heartbeat.async_render({'watched':entity}) is True
        await hass.async_stop()
    print('HA schemas, both channels, all notification texts, literal notes and heartbeat templates passed.')

if __name__=='__main__':asyncio.run(main())
