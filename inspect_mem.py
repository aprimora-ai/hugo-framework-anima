
# Verificar assinatura real de SourceRecord
import sys
sys.path.insert(0, r'C:\Users\ohiod\Projects\ANIMA')
from src.memory.source_memory import SourceRecord, Source
import inspect
print(inspect.signature(SourceRecord.__init__))
print()
# Ver campos de SourceMemory
from src.memory.source_memory import SourceMemory
m = SourceMemory(session_id=1)
print(dir(m))
print()
print(inspect.getsource(SourceMemory.add))
