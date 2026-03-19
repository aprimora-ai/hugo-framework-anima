import sys; sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
import inspect
from chat_anima import SpontaneousThread, SharedState, HUGOField
from src.superego import HUGOBroker
from src.ego.llm_ego import LLMEgo
from src.lei.lei_channel import EchoEmbedStub
from src.memory.source_memory import SourceMemory

src_gate = inspect.getsource(SpontaneousThread._opportunity_available)
src_voc  = inspect.getsource(SpontaneousThread._vocalize)

print('=== SpontaneousThread: gate minimal, policy do LLM ===')
print('  sem theta no gate:        ', 'theta' not in src_gate)
print('  sem seek no gate:         ', 'seek' not in src_gate.lower())
print('  obligated na vocalize:    ', 'obligated' in src_voc)
print('  NULL check na vocalize:   ', 'NULL' in src_voc)

ego   = LLMEgo(backend='stub')
sga   = HUGOBroker(ego=ego, echo_embed=EchoEmbedStub())
shared= SharedState(2.0)
field = HUGOField(seed=42)
mem   = SourceMemory(session_id=1)
spont = SpontaneousThread(shared=shared, field=field, sga=sga, memory=mem,
                          tick_s=2.0, check_every=8, min_silence_ticks=3)

print()
print('  check_every:      ', spont.check_every)
print('  min_silence_ticks:', spont.min_silence_ticks)
print('  sem theta_spont:  ', not hasattr(spont, 'theta_spont'))
print('  sem silence_ticks:', not hasattr(spont, 'silence_ticks'))
print()
print('=== OK: vocalizacao espontanea e comportamento emergente ===')
