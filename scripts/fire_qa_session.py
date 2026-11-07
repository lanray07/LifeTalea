"""Keep an already-unlocked, connected QA tablet awake; restore its exact power setting."""
from contextlib import contextmanager
import subprocess

@contextmanager
def awake_device(adb):
    def shell(*args):
        return subprocess.check_output([str(adb),'shell',*args],text=True,encoding='utf-8',errors='replace',timeout=30).strip()
    if 'isStatusBarKeyguard=true' in shell('dumpsys','window','policy'):
        raise RuntimeError('Unlock the connected QA tablet on the device, then rerun. Never send or script its PIN.')
    original=shell('settings','get','global','stay_on_while_plugged_in')
    if original!='null' and original not in [str(n) for n in range(8)]:
        raise RuntimeError('Unknown device power setting; refusing to change it')
    state={'originalStayAwakeWhilePluggedIn':original,'restored':False}
    try:
        shell('settings','put','global','stay_on_while_plugged_in','7')
        yield state
    finally:
        if original=='null': shell('settings','delete','global','stay_on_while_plugged_in')
        else: shell('settings','put','global','stay_on_while_plugged_in',original)
        state['restored']=shell('settings','get','global','stay_on_while_plugged_in')==original
        if not state['restored']: raise RuntimeError('QA tablet power setting was not restored; restore it before continuing')

@contextmanager
def landscape_device(adb):
    def shell(*args): return subprocess.check_output([str(adb),'shell',*args],text=True,timeout=30).strip()
    original={key:shell('settings','get','system',key) for key in ['accelerometer_rotation','user_rotation']}
    state={'original':original,'restored':False}
    try:
        shell('settings','put','system','accelerometer_rotation','0');shell('settings','put','system','user_rotation','1')
        yield state
    finally:
        for key in ['user_rotation','accelerometer_rotation']:
            if original[key]=='null':shell('settings','delete','system',key)
            else:shell('settings','put','system',key,original[key])
        state['restored']=all(shell('settings','get','system',key)==value for key,value in original.items())
        if not state['restored']:raise RuntimeError('QA tablet rotation settings were not restored')
