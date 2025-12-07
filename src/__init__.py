# 将 src 目录标记为 Python Package
# 并暴露核心组件以方便导入

# 1. 导出我们需要的新 Green Agent 组件
from .green_rag_engine import GreenRAGEngine
from .traffic_light_eval import TrafficLightAuditor

# 2. 导出主办方提供的基础组件 (如果有需要的话，可选)
# 使用 try-except 是为了防止如果 agents.py 缺少某些依赖时导致整个包无法导入
try:
    from .agents import ReactAgent, PSAgent, PEAgent
except ImportError:
    pass

try:
    from .generated_tools import Tools_map
except ImportError:
    pass

# 定义包的公共接口
__all__ = [
    "GreenRAGEngine",
    "TrafficLightAuditor",
    "ReactAgent",
    "PSAgent",
    "PEAgent",
    "Tools_map"
]