"""结构化输出的 Pydantic Schema。

这是产品设计文档第 8 章「结构化输出与数据结构」的严格实现，
所有 Agent 的最终产物都要收敛到 :class:`GameOutput`。

版本演进：
    - v1.0：MVP。平铺 Node + 字符串 requires/unlock + 单字段 asset_prompt。
    - v1.1：（内部迭代基线）沿用 v1.0 结构 + Assets.characters。
    - v1.2：本次升级——加入
        1. 章节层级（act/chapter/segment_order/parent_node_id）
        2. 场景与演出细化（Scene / BGM / CG / Voiceover + 拆分 asset_prompt）
        3. 道具系统（Item + Node/Choice 层的 gain/consume/requires_items）
        4. 结构化触发条件（Condition AST，含 var_cmp/has_item/choice_taken/and/or/not）
        5. 内容块类型化（NodeType 扩展为 dialogue/narration/inner_monologue/system/
           status_change/choice/minigame/ending）

设计原则：
    - **向后兼容**：v1.1 JSON 仍可被 v1.2 引擎读入；缺失字段用默认值。
    - **可序列化**：所有类型均为 Pydantic v2 模型，支持 model_dump_json。
    - **可考察**：Condition 的 discriminated union + expression 冗余，
      使字段既能被程序精确 evaluate、也能被人快速审阅。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

# --------------------------------------------------------------------------- #
# 中间产物：解析 Agent 输出
# --------------------------------------------------------------------------- #


class Character(BaseModel):
    """人设卡。"""

    name: str
    role: str = Field(..., description="主角/配角/反派/NPC...")
    persona: str = Field(..., description="性格、外貌、背景的一句话总结")
    motivation: Optional[str] = Field(None, description="核心动机（推动剧情用）")
    ref_image: Optional[str] = Field(None, description="立绘参考图 URL/路径")


class Worldview(BaseModel):
    """世界观设定。"""

    era: str = Field(..., description="时代/纪年，例：民国 1932")
    location: str = Field(..., description="主要场景/地域")
    rules: List[str] = Field(default_factory=list, description="世界特殊规则/设定条目")


# v1.2 新增：幕/章 顶层结构
class Chapter(BaseModel):
    """章。属于某个幕，包含若干节点。"""

    id: str = Field(..., description="章 ID，例：c_intro_01")
    act_id: str = Field(..., description="所属幕 ID")
    title: str
    summary: Optional[str] = Field(None, description="章节梗概")


class Act(BaseModel):
    """幕。对齐传统剧本三/五幕结构以及《凤仪千秋》等宫斗剧的「幕/章/节」惯例。

    早期简单剧本允许省略 chapter_ids，直接把节点挂到 act 上。
    """

    id: str = Field(..., description="幕 ID，例：act_1")
    title: str = Field(..., description="幕的标题，例：起势 / 承 / 转 / 合")
    summary: Optional[str] = Field(None, description="本幕主旨（一两句话）")
    chapter_ids: List[str] = Field(default_factory=list, description="包含的章 ID 列表")


class StorySetting(BaseModel):
    """解析 Agent 的完整产物：人设 + 世界观 + 大纲。"""

    title: str
    logline: str = Field(..., description="一句话故事简介")
    genre: List[str] = Field(default_factory=list, description="类型标签")
    worldview: Worldview
    characters: List[Character]
    main_conflict: str = Field(..., description="主要冲突/戏剧问题")
    outline: List[str] = Field(default_factory=list, description="主线大纲（3–8 段）")
    # v1.2 新增：顶层幕结构。允许 None 以兼容老输入。
    acts: Optional[List[Act]] = Field(
        None, description="v1.2：幕结构。为 None 时表示未启用幕/章层级"
    )
    chapters: Optional[List[Chapter]] = Field(
        None, description="v1.2：章结构。为 None 时表示未启用章层级"
    )


# --------------------------------------------------------------------------- #
# 中间产物：剧情规划 Agent 输出（MECE 支线骨架）
# --------------------------------------------------------------------------- #


class BranchSkeleton(BaseModel):
    """一条分支的骨架描述——务必与其他分支 MECE 互斥。"""

    id: str = Field(..., description="分支 ID，例：b_love / b_revenge")
    label: str = Field(..., description="分支主题短标签")
    conflict_source: str = Field(..., description="冲突来源（与其他分支必须不同）")
    ending_direction: str = Field(..., description="结局走向（与其他分支必须不同）")
    key_props: List[str] = Field(default_factory=list, description="关键道具/线索")
    beats: List[str] = Field(..., description="节拍大纲（3–8 条），每条是一句话")
    # v1.2 新增：分支在幕/章层级的定位（可选）
    act_id: Optional[str] = Field(None, description="所属幕 ID（v1.2）")
    chapter_ids: List[str] = Field(
        default_factory=list, description="包含的章 ID 列表（v1.2）"
    )


class StorySkeleton(BaseModel):
    """规划 Agent 完整产物。"""

    variables: Dict[str, int] = Field(
        default_factory=dict, description="初始变量表：{'好感度': 0, '勇气': 0, ...}"
    )
    branches: List[BranchSkeleton]
    choice_points: List[str] = Field(
        default_factory=list, description="全局关键选择点（分岔位置）"
    )
    # v1.2 新增：与 setting.acts 冗余存一份，便于下游 Agent 直接读
    acts: Optional[List[Act]] = Field(None, description="v1.2：幕结构（可选）")
    chapters: Optional[List[Chapter]] = Field(
        None, description="v1.2：章结构（可选）"
    )


# --------------------------------------------------------------------------- #
# v1.2 新增：Condition AST（结构化触发条件）
# --------------------------------------------------------------------------- #


class ConditionBase(BaseModel):
    """条件 AST 共用基类。

    ``expression`` 字段冗余保存人类可读表达式（例：``"好感度>=60 && 勇气>=40"``），
    仅用于阅读与调试；引擎侧 evaluate 时**不看** expression，只看 type + payload。
    这样即便 expression 与 AST 不一致（例：手改了 AST 但忘更 expression），
    也不影响运行时行为。
    """

    expression: Optional[str] = Field(
        None,
        description="人类可读表达式（冗余），仅供阅读与调试；evaluate 不看此字段",
    )

    def evaluate(self, state: "EvalState") -> bool:  # noqa: D401 - simple predicate
        """默认实现由具体子类覆盖。"""
        raise NotImplementedError


class VarCmp(ConditionBase):
    """变量比较条件：``var op value``。"""

    type: Literal["var_cmp"] = "var_cmp"
    var: str = Field(..., description="变量名，需在 GameOutput.variables 中存在")
    op: Literal[">", ">=", "<", "<=", "==", "!="] = Field(..., description="比较符")
    value: int = Field(..., description="比较基准值")

    def evaluate(self, state: "EvalState") -> bool:
        v = state.variables.get(self.var, 0)
        ops = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        return ops[self.op](v, self.value)


class HasItem(ConditionBase):
    """拥有道具条件：需持有 item_id 至少 min_count 件。"""

    type: Literal["has_item"] = "has_item"
    item_id: str = Field(..., description="道具 ID，需在 GameOutput.assets.items 中存在")
    min_count: int = Field(1, ge=1, description="至少需要持有的数量")

    def evaluate(self, state: "EvalState") -> bool:
        return state.inventory.get(self.item_id, 0) >= self.min_count


class ChoiceTaken(ConditionBase):
    """曾选择过某选项：node_id 的第 choice_index 个 choice 是否被玩家选中过。"""

    type: Literal["choice_taken"] = "choice_taken"
    node_id: str = Field(..., description="选项所属节点 ID")
    choice_index: int = Field(..., ge=0, description="该节点 choices 数组下标")

    def evaluate(self, state: "EvalState") -> bool:
        return (self.node_id, self.choice_index) in state.taken_choices


class And_(ConditionBase):
    """逻辑与：所有子条件均为 True。"""

    type: Literal["and"] = "and"
    conditions: List["Condition"] = Field(..., description="子条件（≥1）")

    def evaluate(self, state: "EvalState") -> bool:
        return all(c.evaluate(state) for c in self.conditions)


class Or_(ConditionBase):
    """逻辑或：至少一个子条件为 True。"""

    type: Literal["or"] = "or"
    conditions: List["Condition"] = Field(..., description="子条件（≥1）")

    def evaluate(self, state: "EvalState") -> bool:
        return any(c.evaluate(state) for c in self.conditions)


class Not_(ConditionBase):
    """逻辑非。"""

    type: Literal["not"] = "not"
    condition: "Condition"

    def evaluate(self, state: "EvalState") -> bool:
        return not self.condition.evaluate(state)


# Discriminated union：Pydantic 根据 type 字段自动挑选具体类型
Condition = Annotated[
    Union[VarCmp, HasItem, ChoiceTaken, And_, Or_, Not_],
    Field(discriminator="type"),
]

# 前向引用回填
And_.model_rebuild()
Or_.model_rebuild()
Not_.model_rebuild()


class EvalState(BaseModel):
    """给 :meth:`Condition.evaluate` 使用的最小运行时状态。

    模拟器/一致性校验可以直接构造这个对象喂给 evaluate，无需再自行实现解析器。
    """

    variables: Dict[str, int] = Field(default_factory=dict)
    inventory: Dict[str, int] = Field(default_factory=dict, description="item_id → 数量")
    taken_choices: List[tuple] = Field(
        default_factory=list, description="(node_id, choice_index) 历史"
    )


# --------------------------------------------------------------------------- #
# v1.2 新增：Condition 兼容层（parse_condition & 表达式回写）
# --------------------------------------------------------------------------- #


_CMP_OPS = (">=", "<=", "==", "!=", ">", "<")  # 顺序敏感：长匹配优先


def parse_condition(expr: str) -> Optional[Condition]:
    """把 v1.1 风格的字符串表达式解析为 Condition AST。

    支持的语法（最小集，够覆盖存量剧本）：
        - 变量比较：``好感度>=60`` / ``勇气 > 40`` / ``金钱 != 0``
        - 逻辑与：``A && B``（也接受关键字 ``and``）
        - 逻辑或：``A || B``（也接受关键字 ``or``）
        - 括号：``(A && B) || C``

    解析失败返回 None；调用方应把原始 expression 作为 fallback
    存到 ``ConditionBase.expression`` 里，并给 warning。

    有意**不支持**复杂函数调用（例 ``has_item(x)``）——这类语义在 v1.2
    应由 LLM/Agent 直接生成结构化 HasItem 节点，不该出现在旧字符串里。
    """
    if not expr or not expr.strip():
        return None
    try:
        tokens = _tokenize(expr)
        pos = [0]
        node = _parse_or(tokens, pos)
        if node is None or pos[0] != len(tokens):
            return None
        # 顶层挂上 expression，便于调试；子节点保持无 expression 以避免污染
        node.expression = expr.strip()
        return node
    except Exception:
        return None


def _tokenize(expr: str) -> List[str]:
    """极简 tokenizer：识别括号 / && / || / and / or / 比较符 / 变量名 / 数字。"""
    tokens: List[str] = []
    i = 0
    s = expr.strip()
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if s[i : i + 2] in ("&&", "||"):
            tokens.append(s[i : i + 2])
            i += 2
            continue
        # 关键字 and / or（不区分大小写）
        lo = s[i:].lower()
        if lo.startswith("and ") or lo == "and":
            tokens.append("&&")
            i += 3
            continue
        if lo.startswith("or ") or lo == "or":
            tokens.append("||")
            i += 2
            continue
        # 比较符（长匹配优先）
        matched = False
        for op in _CMP_OPS:
            if s.startswith(op, i):
                tokens.append(op)
                i += len(op)
                matched = True
                break
        if matched:
            continue
        # 数字（可带负号）
        if ch.isdigit() or (ch == "-" and i + 1 < len(s) and s[i + 1].isdigit()):
            j = i + 1
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(s[i:j])
            i = j
            continue
        # 标识符：中文 + 字母 + 数字 + 下划线
        j = i
        while j < len(s) and (
            s[j].isalnum() or s[j] == "_" or ord(s[j]) > 0x7F
        ):
            j += 1
        if j == i:
            # 无法识别的字符
            raise ValueError(f"tokenize failed at {i}: {s[i]!r}")
        tokens.append(s[i:j])
        i = j
    return tokens


def _parse_or(tokens: List[str], pos: List[int]) -> Optional[Condition]:
    left = _parse_and(tokens, pos)
    if left is None:
        return None
    parts: List[Condition] = [left]
    while pos[0] < len(tokens) and tokens[pos[0]] == "||":
        pos[0] += 1
        right = _parse_and(tokens, pos)
        if right is None:
            return None
        parts.append(right)
    if len(parts) == 1:
        return parts[0]
    return Or_(conditions=parts)


def _parse_and(tokens: List[str], pos: List[int]) -> Optional[Condition]:
    left = _parse_atom(tokens, pos)
    if left is None:
        return None
    parts: List[Condition] = [left]
    while pos[0] < len(tokens) and tokens[pos[0]] == "&&":
        pos[0] += 1
        right = _parse_atom(tokens, pos)
        if right is None:
            return None
        parts.append(right)
    if len(parts) == 1:
        return parts[0]
    return And_(conditions=parts)


def _parse_atom(tokens: List[str], pos: List[int]) -> Optional[Condition]:
    if pos[0] >= len(tokens):
        return None
    t = tokens[pos[0]]
    if t == "(":
        pos[0] += 1
        inner = _parse_or(tokens, pos)
        if pos[0] >= len(tokens) or tokens[pos[0]] != ")":
            return None
        pos[0] += 1
        return inner
    # 变量比较：ident op value
    if pos[0] + 2 < len(tokens) and tokens[pos[0] + 1] in _CMP_OPS:
        var = tokens[pos[0]]
        op = tokens[pos[0] + 1]
        val_tok = tokens[pos[0] + 2]
        try:
            val = int(val_tok)
        except ValueError:
            return None
        pos[0] += 3
        return VarCmp(var=var, op=op, value=val)  # type: ignore[arg-type]
    return None


def render_condition(cond: Optional[Condition]) -> str:
    """把 Condition AST 反向 render 成人类可读表达式。用于日志、Ending 展示等。"""
    if cond is None:
        return ""
    if isinstance(cond, VarCmp):
        return f"{cond.var}{cond.op}{cond.value}"
    if isinstance(cond, HasItem):
        base = f"has_item({cond.item_id}"
        if cond.min_count != 1:
            base += f", {cond.min_count}"
        return base + ")"
    if isinstance(cond, ChoiceTaken):
        return f"choice_taken({cond.node_id}, {cond.choice_index})"
    if isinstance(cond, And_):
        return " && ".join(f"({render_condition(c)})" for c in cond.conditions)
    if isinstance(cond, Or_):
        return " || ".join(f"({render_condition(c)})" for c in cond.conditions)
    if isinstance(cond, Not_):
        return f"!({render_condition(cond.condition)})"
    return ""


def _coerce_condition(v: Any) -> Any:
    """给 field_validator 用的字符串 → Condition 转换器。

    - None / 已是 Condition 对象 / dict：原样交给 Pydantic 走标准校验；
    - str：先试 parse_condition；解析失败则退化为
      ``VarCmp(var="_expr", op=">=", value=0, expression=<原字符串>)``——
      一个「恒真」（因为默认变量 0 >= 0）但**保留原始表达式**的兜底节点，
      让下游有据可查。同时打印 warning。
    """
    if v is None:
        return v
    if isinstance(v, str):
        parsed = parse_condition(v)
        if parsed is not None:
            return parsed
        import warnings

        warnings.warn(
            f"parse_condition 失败，已回退为恒真占位并保留原表达式：{v!r}",
            stacklevel=3,
        )
        return VarCmp(var="_expr", op=">=", value=0, expression=v)  # type: ignore[arg-type]
    return v


# --------------------------------------------------------------------------- #
# v1.2 新增：Scene / Item / BGM / CG / Voiceover 资产
# --------------------------------------------------------------------------- #


class Scene(BaseModel):
    """场景。多个 Node 可复用同一 scene_id，避免 background 重复。"""

    id: str = Field(..., description="场景 ID，例：s_courtyard_01")
    location: str = Field(..., description="地点名，例：宫廷正殿")
    background: Optional[str] = Field(
        None, description="背景素材 URL/路径；未生成时为 None"
    )
    description: Optional[str] = Field(None, description="场景描述（用于生成素材）")
    default_bgm_id: Optional[str] = Field(None, description="推荐 BGM ID")


ItemType = Literal["key_item", "consumable", "collectible"]


class Item(BaseModel):
    """道具。与「变量」并行：变量表达可累加的连续量（好感度、勇气），
    Item 表达离散/可拥有物（信物、钥匙、药水）。两套系统互不替代。
    """

    id: str = Field(..., description="道具 ID，例：i_key_of_east_gate")
    name: str
    type: ItemType = Field(
        ...,
        description="key_item=关键道具（推进主线用）/ consumable=消耗品 / collectible=收集品",
    )
    stackable: bool = Field(False, description="是否可堆叠")
    description: Optional[str] = None
    icon: Optional[str] = Field(None, description="图标资源路径")


class BGM(BaseModel):
    """背景音乐资产。"""

    id: str
    name: Optional[str] = None
    description: Optional[str] = Field(None, description="风格/情绪描述，用于生成或检索")
    url: Optional[str] = None


class CG(BaseModel):
    """CG 立绘/插画资产。"""

    id: str
    description: Optional[str] = Field(None, description="画面描述（用于生成）")
    scene_id: Optional[str] = Field(None, description="所属场景（可选）")
    url: Optional[str] = None


class Voiceover(BaseModel):
    """配音资产（占位；实际语音生成留给后续 pipeline）。"""

    id: str
    speaker: Optional[str] = Field(None, description="发言者，例：主角内心声 / 系统提示音")
    text: Optional[str] = Field(None, description="配音文本")
    url: Optional[str] = None


# --------------------------------------------------------------------------- #
# 最终产物：与引擎对接的 GameOutput
# --------------------------------------------------------------------------- #


# v1.2：NodeType 扩展。为了向后兼容，v1.1 已有的 dialogue/narration/choice/minigame/ending 一律保留。
NodeType = Literal[
    "dialogue",
    "narration",
    "inner_monologue",  # v1.2 新增：内心独白（斜体渲染 + 内心声 TTS）
    "system",  # v1.2 新增：系统提示（居中横条 + 不配音）
    "status_change",  # v1.2 新增：纯数值变化提示（【勇气 +5】）
    "choice",
    "minigame",
    "ending",
]
# 语义别名：v1.2 起「NodeType」在语义上也代表节点内容块的类型
ContentType = NodeType

StagingTier = Literal["static", "semi-dynamic", "full-video"]


class Effect(BaseModel):
    """选择对属性的影响。"""

    variable: str
    delta: int


class Choice(BaseModel):
    text: str
    effects: Dict[str, int] = Field(
        default_factory=dict, description="属性增减，例：{'勇气': 5}"
    )
    goto: str = Field(..., description="下一节点 id")
    # v1.2：requires 从 Optional[str] 升级为 Optional[Condition]（结构化 AST）
    # field_validator 会自动把旧的字符串输入转成 AST，保持向后兼容。
    requires: Optional[Condition] = Field(
        None, description="解锁条件（v1.2：Condition AST；旧字符串会自动转 AST）"
    )
    # v1.2 新增：道具相关字段
    requires_items: List[str] = Field(
        default_factory=list, description="选择本条所需持有的道具 ID 列表（v1.2）"
    )
    gain_items: List[str] = Field(
        default_factory=list, description="选择本条后获得的道具 ID 列表（v1.2）"
    )
    consume_items: List[str] = Field(
        default_factory=list,
        description="选择本条后消耗的道具 ID 列表（v1.2）；必须是 requires_items 或已持有的",
    )

    @field_validator("requires", mode="before")
    @classmethod
    def _coerce_requires(cls, v: Any) -> Any:
        """兼容 v1.1：requires 传字符串时自动 parse 为 Condition AST。"""
        return _coerce_condition(v)


class Minigame(BaseModel):
    type: Literal["timed_click", "qte", "puzzle"] = "timed_click"
    window_ms: int = Field(800, ge=100, le=5000)
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    on_success: str = Field(..., description="成功后跳转节点 id")
    on_failure: Optional[str] = Field(None, description="失败后跳转节点 id")
    reward: Dict[str, int] = Field(default_factory=dict, description="成功奖励属性")


class Node(BaseModel):
    id: str
    type: NodeType
    branch_id: Optional[str] = Field(None, description="所属分支")
    character: Optional[str] = Field(None, description="发言角色（对话/内心独白节点）")
    content: str = Field(..., description="正文（对话/旁白/描述）")
    choices: List[Choice] = Field(default_factory=list)
    minigame: Optional[Minigame] = None
    staging: StagingTier = Field(
        "static", description="演出档位（演出设计 Agent 决定）"
    )
    emotion_intensity: float = Field(
        0.5, ge=0.0, le=1.0, description="情绪强度 0-1，用于演出决策"
    )
    # v1.1 保留：asset_prompt 仍作为「兜底/汇总」字段，给素材生成流水线一个 fallback prompt
    asset_prompt: Optional[str] = Field(
        None, description="素材生成 prompt（v1.2 起为兜底汇总字段；细粒度字段见下）"
    )

    # --- v1.2 新增：章节层级 ---------------------------------------------- #
    act_id: Optional[str] = Field(None, description="所属幕 ID（v1.2）")
    chapter_id: Optional[str] = Field(None, description="所属章 ID（v1.2）")
    segment_order: Optional[int] = Field(
        None,
        description=(
            "本节点在同章内的段落顺序（v1.2）。允许 None，"
            "缺失时下游按 nodes 列表顺序推断"
        ),
    )
    parent_node_id: Optional[str] = Field(
        None,
        description=(
            "叙事结构上的父节点 ID（v1.2）。"
            "与 Choice.goto 独立：parent 表达剧情树的层级，goto 表达玩家路径"
        ),
    )

    # --- v1.2 新增：场景与演出细化 ---------------------------------------- #
    scene_id: Optional[str] = Field(None, description="场景 ID（v1.2；引用 Assets.scenes）")
    location: Optional[str] = Field(None, description="地点名，从 asset_prompt 拆出（v1.2）")
    background: Optional[str] = Field(None, description="背景描述/资源（v1.2）")
    camera: Optional[str] = Field(None, description="镜头语言，例：特写/中景/远景（v1.2）")
    bgm_id: Optional[str] = Field(None, description="BGM ID（v1.2；引用 Assets.bgms）")
    cg_id: Optional[str] = Field(None, description="CG ID（v1.2；引用 Assets.cgs）")
    voiceover: Optional[str] = Field(
        None, description="配音资产 ID（v1.2；引用 Assets.voiceovers）"
    )

    # --- v1.2 新增：道具进出 --------------------------------------------- #
    gain_items: List[str] = Field(
        default_factory=list, description="进入该节点即获得的道具 ID 列表（v1.2）"
    )
    consume_items: List[str] = Field(
        default_factory=list, description="进入该节点即消耗的道具 ID 列表（v1.2）"
    )


class Ending(BaseModel):
    id: str
    branch_id: Optional[str] = None
    title: str
    # v1.2：unlock 从 str 升级为 Condition AST
    unlock: Condition = Field(..., description="解锁条件（v1.2：Condition AST）")
    is_true_ending: bool = False
    is_hidden: bool = False

    @field_validator("unlock", mode="before")
    @classmethod
    def _coerce_unlock(cls, v: Any) -> Any:
        """兼容 v1.1：unlock 传字符串时自动 parse 为 Condition AST。"""
        return _coerce_condition(v)


class StoryTree(BaseModel):
    nodes: List[Node]
    endings: List[Ending]
    start_node: str = Field(..., description="起始节点 id")


class Assets(BaseModel):
    characters: List[Character] = Field(default_factory=list)
    # v1.2 新增资产池
    scenes: List[Scene] = Field(default_factory=list, description="场景池（v1.2）")
    items: List[Item] = Field(default_factory=list, description="道具池（v1.2）")
    bgms: List[BGM] = Field(default_factory=list, description="BGM 池（v1.2）")
    cgs: List[CG] = Field(default_factory=list, description="CG 池（v1.2）")
    voiceovers: List[Voiceover] = Field(
        default_factory=list, description="配音资产池（v1.2）"
    )


class GameOutput(BaseModel):
    """引擎侧的最终合约。任何 Agent 产物都要收敛到它。"""

    schema_version: str = Field("1.2", description="Schema 版本")
    title: str
    logline: str
    genre: List[str] = Field(default_factory=list)
    variables: Dict[str, int] = Field(default_factory=dict)
    story_tree: StoryTree
    assets: Assets = Field(default_factory=Assets)
    # v1.2 新增：把幕/章顶层挂在 GameOutput 上，方便前端做目录页
    acts: Optional[List[Act]] = Field(None, description="幕结构（v1.2，可选）")
    chapters: Optional[List[Chapter]] = Field(
        None, description="章结构（v1.2，可选）"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Pipeline 顶层结果
# --------------------------------------------------------------------------- #


class ConsistencyReport(BaseModel):
    passed: bool
    issues: List[str] = Field(default_factory=list)
    duplicate_branch_pairs: List[List[str]] = Field(default_factory=list)
    # v1.2 新增：新问题类别（保持向后兼容——旧字段仍返回）
    missing_hierarchy: List[str] = Field(
        default_factory=list,
        description="缺失章节结构信息的节点 ID 列表（v1.2）",
    )
    dangling_item_refs: List[str] = Field(
        default_factory=list,
        description="引用了未在 items 池中定义的道具 ID（v1.2）",
    )
    condition_var_issues: List[str] = Field(
        default_factory=list,
        description="Condition 里引用的变量不在 variables 表中（v1.2）",
    )


class PipelineResult(BaseModel):
    """一次生成的完整产物 + 过程摘要。"""

    game: GameOutput
    setting: StorySetting
    skeleton: StorySkeleton
    consistency: ConsistencyReport
    agent_logs: List[str] = Field(default_factory=list)

    def model_dump_json(self, **kwargs) -> str:  # type: ignore[override]
        kwargs.setdefault("indent", 2)
        # Pydantic v2 doesn't accept ensure_ascii; leave it to user via kwargs
        return super().model_dump_json(**kwargs)
