"""
豆包大模型 Prompt 模板
- 简历解析: 将简历文本结构化为 JSON
- 职位解析: 将职位描述结构化为 JSON
- 匹配重排: 对候选对进行语义精排
"""
from typing import Any


# ===== 简历解析 Prompt =====
RESUME_SYSTEM_PROMPT = """你是专业的人力资源简历解析专家。请将用户提供的简历文本解析为结构化 JSON 数据。

要求:
1. 严格输出 JSON 格式, 不要包含任何解释性文字或 markdown 标记
2. 字段缺失时填 null, 不要臆造
3. 技能列表需归一化 (如 "js" -> "JavaScript")
4. 工作经历按时间倒序排列

输出 JSON 字段说明:
{
  "name": "姓名",
  "gender": "性别(男/女)",
  "age": "年龄(整数)",
  "phone": "手机号",
  "email": "邮箱",
  "current_city": "当前居住城市",
  "intention_cities": ["意向城市数组"],
  "education": "最高学历(博士/硕士/本科/大专/高中)",
  "school": "毕业院校",
  "major": "专业",
  "work_years": "工作年限(整数)",
  "expected_salary_min": "期望薪资下限(整数, K)",
  "expected_salary_max": "期望薪资上限(整数, K)",
  "self_evaluation": "自我评价",
  "skills": [{"name": "技能名", "level": "精通/熟练/掌握/了解"}],
  "work_experience": [{"company": "公司", "position": "职位", "duration": "时长", "description": "工作内容"}],
  "projects": [{"name": "项目名", "role": "角色", "description": "项目描述"}]
}"""


RESUME_USER_TEMPLATE = """请解析以下简历文本:

---
{resume_text}
---

请输出结构化 JSON:"""


# ===== 职位解析 Prompt =====
JOB_SYSTEM_PROMPT = """你是专业的招聘需求解析专家。请将用户提供的职位描述文本解析为结构化 JSON 数据。

要求:
1. 严格输出 JSON 格式, 不要包含任何解释性文字或 markdown 标记
2. 字段缺失时填 null, 不要臆造
3. 技能要求需归一化

输出 JSON 字段说明:
{
  "title": "职位名称",
  "company": "公司名称",
  "department": "部门",
  "job_type": "工作性质(全职/兼职/实习)",
  "salary_min": "薪资下限(整数, K)",
  "salary_max": "薪资上限(整数, K)",
  "work_city": "工作城市",
  "experience_required": "经验要求(如 3-5年)",
  "education_required": "学历要求",
  "headcount": "招聘人数(整数)",
  "description": "职位详细描述",
  "requirements": [{"skill_name": "技能名", "skill_level": "要求水平", "req_type": "必须/优先"}]
}"""


JOB_USER_TEMPLATE = """请解析以下职位描述:

---
{job_text}
---

请输出结构化 JSON:"""


# ===== 匹配重排 Prompt =====
RERANK_SYSTEM_PROMPT = """你是资深的人力资源匹配专家。请根据简历与职位信息, 评估匹配度并给出自然语言依据。

要求:
1. 严格输出 JSON 格式
2. score 为 0-100 的整数, 表示综合匹配度
3. reason 用 2-3 句中文说明匹配亮点与差距

输出格式:
{
  "score": 85,
  "reason": "候选人具备 5 年 Java 开发经验, 满足职位要求的 3 年以上; 熟悉 Spring 框架, 与职位技术栈高度匹配; 但期望薪资略高于岗位预算。"
}"""


RERANK_USER_TEMPLATE = """职位信息:
{job_json}

候选人简历摘要:
{resume_json}

请评估匹配度:"""


# ===== 批量匹配重排 Prompt (一次评估多个候选, 大幅降低 LLM 调用次数) =====
BATCH_RERANK_SYSTEM_PROMPT = """你是资深的人力资源匹配专家。请根据候选人简历与多个候选职位信息, 一次性评估每个职位的匹配度。

要求:
1. 严格输出 JSON 数组格式, 不要包含任何解释性文字或 markdown 标记
2. 数组长度必须与输入的职位数量一致, 顺序一致
3. 每个元素包含 idx(职位序号, 从0开始)、score(0-100 整数)、reason(1句中文说明匹配亮点与差距)

输出格式:
[
  {"idx": 0, "score": 85, "reason": "候选人具备5年Java开发经验, 满足职位3年要求; 熟悉Spring框架, 技术栈高度匹配; 但期望薪资略高。"},
  {"idx": 1, "score": 72, "reason": "候选人技术栈为Java, 与职位要求的Python方向不符; 但工作经验和学历满足要求。"}
]"""


BATCH_RERANK_USER_TEMPLATE = """候选人简历摘要:
{resume_json}

候选职位列表:
{jobs_json}

请逐一评估每个职位的匹配度, 输出 JSON 数组:"""


# ===== Prompt 构造函数 =====
def build_resume_messages(resume_text: str) -> list[dict[str, str]]:
    """构造简历解析消息列表"""
    return [
        {"role": "system", "content": RESUME_SYSTEM_PROMPT},
        {"role": "user", "content": RESUME_USER_TEMPLATE.format(resume_text=resume_text)},
    ]


def build_job_messages(job_text: str) -> list[dict[str, str]]:
    """构造职位解析消息列表"""
    return [
        {"role": "system", "content": JOB_SYSTEM_PROMPT},
        {"role": "user", "content": JOB_USER_TEMPLATE.format(job_text=job_text)},
    ]


def build_rerank_messages(resume_json: str, job_json: str) -> list[dict[str, str]]:
    """构造匹配重排消息列表"""
    return [
        {"role": "system", "content": RERANK_SYSTEM_PROMPT},
        {"role": "user", "content": RERANK_USER_TEMPLATE.format(resume_json=resume_json, job_json=job_json)},
    ]


def build_batch_rerank_messages(resume_json: str, jobs_json: str) -> list[dict[str, str]]:
    """构造批量匹配重排消息列表 (一次评估多个职位)"""
    return [
        {"role": "system", "content": BATCH_RERANK_SYSTEM_PROMPT},
        {"role": "user", "content": BATCH_RERANK_USER_TEMPLATE.format(resume_json=resume_json, jobs_json=jobs_json)},
    ]
