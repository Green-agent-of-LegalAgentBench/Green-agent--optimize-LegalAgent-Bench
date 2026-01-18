from zhipuai import ZhipuAI
import json
import re
import os
import src.config as config
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置智谱 AI
zhipuai_api_key = os.getenv("ZHIPUAI_API_KEY", "your_api_key")

def LLM(query, model_name):
    """
    统一的 LLM 调用接口，使用智谱 AI
    """
    # 如果传入的是其他模型名，统一使用 glm-4-flash
    if model_name.find('glm') == -1:
        model_name = "glm-4-flash"
    
    # 使用智谱 AI
    client = ZhipuAI(api_key=zhipuai_api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": query},
        ],
        stream=False,
        max_tokens=2000,
        temperature=0,
        do_sample=False,
    )

    # 记录 token 消耗数
    input_token = response.usage.prompt_tokens
    output_token = response.usage.completion_tokens
    used_token = response.usage.total_tokens

    config.this_question_input_token += input_token
    config.this_question_output_token += output_token
    config.this_question_total_token += used_token
    config.total_token += used_token

    return response.choices[0].message.content.strip()
    

import json
import re

def parse_json_from_response(rsp: str):
    """
    强壮的 JSON 解析函数：能处理 Markdown、纯文本以及包含废话的回答
    """
    print(f"DEBUG: LLM Raw Response:\n{rsp}\n----------------") # 关键调试信息
    
    json_str = None
    
    # 策略 1: 尝试提取 Markdown 代码块 (无论是否标记为 json)
    # 匹配 ```json ... ``` 或 ``` ... ```
    pattern = r"```(?:json|JSON)?(.*?)```"
    match = re.search(pattern, rsp, re.DOTALL)
    
    if match:
        json_str = match.group(1).strip()
    else:
        # 策略 2: 没找到代码块？尝试寻找最外层的 {}
        # 这能处理："Here is the result: { ... } Hope it helps."
        start = rsp.find('{')
        end = rsp.rfind('}')
        if start != -1 and end != -1:
            json_str = rsp[start:end+1]
        else:
            # 策略 3: 死马当活马医，尝试解析整个字符串
            json_str = rsp.strip()

    # 统一的数据清洗（处理中文括号等常见问题）
    # 注意：直接把 ' 换成 " 有风险（如果内容里有 don't），但在报错重试里做是可以的
    
    try:
        # 尝试 1: 直接解析提取出的字符串
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # 尝试 2: 清洗数据后再解析
            # 替换中文括号，处理 Python 风格的单引号字典
            cleaned_str = json_str.replace('(', '（').replace(')', '）').replace("'", '"')
            return json.loads(cleaned_str)
        except json.JSONDecodeError as e:
            # 尝试 3: 处理常见的列表/字典截断问题（你的旧逻辑）
            try:
                match = re.search(r"\{(.*?)\}", json_str, re.DOTALL)
                if match:
                    content = "[{" + match.group(1) + "}]"
                    return json.loads(content)
            except:
                pass
            
            # 彻底失败，打印报错
            print(f"ERROR: JSON Parsing Failed completely.\nExtracted String: {json_str}")
            # 抛出异常，让上层知道这题没分
            raise e
    

from .generated_tools import *
from .prompt import *
try:
    from schema import *
except ImportError:
    pass

# Define TABLE_PROMPT for table selection
TABLE_PROMPT = """根据用户问题选择需要使用的数据表。

问题: {question}

数据库结构:
{database_schema}

请返回一个JSON格式的响应，包含"名称"字段，值为需要使用的表名列表。
"""

def filter_table_and_tool(query, model_name):
    for attempt in range(3):
        try:
            # Use database_schema if available, otherwise empty string
            db_schema = database_schema if 'database_schema' in globals() else ""
            table_prompt = TABLE_PROMPT.format(question=query, database_schema=db_schema)
            table_answer = LLM(table_prompt, model_name)
            table_response = parse_json_from_response(table_answer)
            table = table_response["名称"]
            break
        except:
            table = [
                "CompanyInfo",
                "CompanyRegister",
                "SubCompanyInfo",
                "LegalDoc",
                "CourtInfo",
                "CourtCode",
                "LawfirmInfo",
                "LawfirmLog",
                "AddrInfo",
                "LegalAbstract",
                "RestrictionCase",
                "FinalizedCase",
                "DishonestyCase",
                "AdministrativeCase"
            ]
    print(f"用到的table: {table}")
    if "CompanyInfo" not in table:
        table.append("CompanyInfo")
    if "AddrInfo" not in table:
        table.append("AddrInfo")

    table_used_prompt = ""
    used_tools = []
    for i in table:
        emun = table_map[i]
        one_prompt = f"""
{i}表格有下列字段:
{build_enum_list(emun)}
-------------------------------------
"""
        table_used_prompt += one_prompt + "\n"
        used_tools.extend(Tools_map[i])

    return used_tools, table_used_prompt

from termcolor import colored

def print_colored(text, color=None):
    """
    打印彩色字符串。

    参数：
    - text: 要打印的文本
    - color: 文本颜色（如 red, green, blue, yellow, cyan, magenta, white）
    """
    try:
        print('\n\n\n')
        print(colored(text, color=color))
        print('\n\n\n')
    except Exception as e:
        print(f"错误: {e}")
