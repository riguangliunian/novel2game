# 互动漫剧游戏生成智能体（Interactive Manhua Game Agent）

> **痛点**：短漫剧行业在 AI 加持下已把「看」的内容做到极致降本，但「玩」的互动漫剧仍靠人工手搓分支剧本与数值，一部多分支互动剧的编剧+策划周期以周计、门槛高，存量漫剧编辑和小说作者难以低成本转型。
>
> **方案**：一个「互动漫剧游戏生成智能体」——上传小说自动改编成多分支互动剧本，或输入主题/人物关键词从零原创，通过多 Agent 流水线产出「分支剧情 + 对话选择 + 穿插小游戏」的可玩互动漫剧游戏。
>
> **一句话定位**：把「写小说/剧本」和「做互动游戏」之间的鸿沟，用一条会写作、懂结构、能配数值的 AI 流水线填平——ToB 给短漫剧公司做低成本转型工具，ToC 给创作者做「一个人的互动游戏工作室」。

---

## 🚀 P1 完整产品：本地向导 + 动静混合素材 + 一键导出

> P0 已跑通「输入 → 7 Agent 流水线 → `output/game.json`」的 CLI 链路。**P1 在完全不破坏 P0 CLI 的前提下**，新增了一套本地 Web 产品：可视化向导、Planner 后人工介入、动静混合素材生成、可玩预览与符合抖音互动空间要求的 zip 导出。

### P1 能做什么

| 能力 | 说明 |
| --- | --- |
| 🧭 本地前端向导 | 步骤式向导：填输入 → 配参数 → 跑流水线 → 看进度 → 人工介入 → 预览 → 导出 |
| ⏱️ 实时进度 | 7 个 Agent 逐个上报 `pending / running / done` 状态 |
| ✋ Human-in-the-loop | **Planner 完成后暂停**，前端展示分支结构供审阅/编辑，点「确认继续」才跑后续 Agent |
| 🎬 动静混合素材 | 系统自动判断每个节点出「视频」还是「静态图」，动态比例由 `video_ratio` 配置控制（默认 ~20%） |
| 🔌 素材 API 入口 | 图片 / 视频生成 API 各一个填写入口，OpenAI-Compatible；**填了就启用，没填就跳过素材生成** |
| ▶️ 游戏预览 | 前端点击选项跳转章节，展示每个节点的图/视频，可完整走完 1-2 章分支 |
| 📦 一键导出 | 导出 zip：根目录含 `index.html`，内联所有素材，本地双击即玩，符合抖音互动空间要求（≤8MB） |

### P1 安装与启动（3 步）

```bash
# 1. 安装（含 P0 依赖 + P1 Web 依赖）
cd interactive-manhua-agent
pip install -e ".[web]"          # 或： pip install -r requirements.txt && pip install -e .

# 2. 配置（可选）——没有任何 API Key 也能用 dry-run 跑通全链路
cp .env.example .env             # 按需填 LLM / 图片 / 视频 API；不填则前端勾选 dry-run

# 3. 启动本地向导服务
manhua-agent-web                 # 控制台脚本
# 或： python -m manhua_agent.server
# 或指定端口： manhua-agent-web --host 127.0.0.1 --port 8000
```

启动后浏览器打开 **http://127.0.0.1:8000**，按向导操作即可。全程无需联网构建前端（纯 HTML+JS，由后端托管）。

### P1 使用流程

1. **填输入**：选「关键词原创」或「上传小说改编」，填关键词 / 粘贴（或上传 .txt）小说正文。
2. **配参数**：主分支数、每分支节点上限、演出档位、`video_ratio` 动态比例；无 API Key 时勾选 **Dry-run**。
3. **跑流水线**：实时看 7 个 Agent 的进度。
4. **人工介入**：Planner 跑完自动暂停，可编辑每条分支的名称/冲突/结局/节拍，点「确认，继续生成」。
5. **预览 & 导出**：内嵌播放器可点选项试玩；点「导出 zip 包」下载，解压双击 `index.html` 即玩。

### P1 动静混合规则

- **倾向生成视频**：关键剧情转折点、高情绪强度场景（打斗/告别/反转）、章节开场/结尾、`full-video` 档位节点。
- **倾向生成静态图**：对话推进、旁白、系统提示、数值变化、次要选项节点。
- 系统给每个节点打「视频得分」，再按 `video_ratio` 取得分最高的前若干个标为视频——**只改 `video_ratio` 就能调整动静比例，无需改代码**（`.env` 的 `VIDEO_RATIO` 或向导里的滑杆均可）。
- 素材 API：`IMAGE_*` / `VIDEO_*` 各是一个入口，均兼容 OpenAI `/v1/images/generations` 风格。都没填 → 跳过素材生成，前端/导出用**程序化占位底图**（按情绪/场景生成配色），游戏依然完整可玩。

### P0 CLI 完全保留

P1 未改动任何 P0 行为，原有 CLI 继续可用：

```bash
manhua-agent --mode keywords --keywords "宫斗,复仇,重生" --dry-run --output output/game.json
```

---

## 目录

1. [产品定位与核心创新](#1-产品定位与核心创新)
2. [目标用户与使用场景](#2-目标用户与使用场景)
3. [产品形态与核心体验](#3-产品形态与核心体验)
4. [技术方案：多 Agent 生成流水线](#4-技术方案多-agent-生成流水线)
5. [模型与 API 选型](#5-模型与-api-选型)
6. [结构化输出与数据结构](#6-结构化输出与数据结构)
7. [数值策划设计](#7-数值策划设计)
8. [关键风险与合规](#8-关键风险与合规)
9. [里程碑与验证](#9-里程碑与验证)
10. [安装与使用（Quick Start）](#10-安装与使用quick-start)
11. [项目结构](#11-项目结构)
12. [配置说明](#12-配置说明)
13. [常见问题](#13-常见问题)

---

## 1. 产品定位与核心创新

### 1.1 做什么

一个面向互动漫剧游戏的生成智能体。用户从两种入口进入，最终得到一份可直接运行的、带小游戏的多分支互动漫剧游戏：

- **输入模式①：小说改编** —— 上传一部小说（长文本）。智能体解析情节框架、人物关系与世界观，自动改编为多分支互动剧本，保留原作主线的同时补出可玩的支线与选择点。适合手握小说 IP、想低成本试水互动化的创作者与版权方。
- **输入模式②：关键词原创** —— 只给主题、人物、世界观关键词（如「民国 / 女法医 / 悬疑 / 双男主」）。智能体从零原创互动剧本，并在信息不足时**主动追问补全**关键词，把模糊创意逼成可生成的完整设定。适合没有成稿、只有灵感的作者。

**输出形态**：分支剧情 + 对话选择 + 穿插小游戏操作（限时点击、QTE 等微交互），落地为一份可玩的**动静结合互动漫剧游戏**——静态立绘、局部动效、完整视频按情感强度与预算档位混搭出演，H5 / 端原生均可承接，带属性系统、分支解锁与多结局。

### 1.2 核心创新：三个别人还没同时做好的点

1. **有「活人感」的文学创作能力**：不是把小说压缩成梗概，而是能写出有冲突张力、人物动机自洽、支线之间不雷同的多分支剧情。这是与「模板化拼接」类工具的根本区别。
2. **结构 + 数值一体生成**：多数生成工具只产文本，本产品把「剧情树结构 + 属性/分支解锁/小游戏数值」作为一等公民一起生成，直接产出可玩的游戏而非可读的剧本。
3. **引导式补全**：面对 ToC 的「我也说不清想要什么」，用交互式澄清把关键词补全成高质量设定，降低生成废稿率。
4. **动静结合演出，不是妥协是差异化**：Galgame、橙光的商业实践已经证明「日常静态 + 关键动态」才是最好用的互动叙事语言。本产品把动静组合上升为叙事一等公民和成本一等公民——静图给日常对话、动效给情感转折、视频给高潮结局，同时对齐 C 端全静态 / 进阶局部动态 / ToB 全视频三档成本。

---

## 2. 目标用户与使用场景

| 用户群 | 画像 | 核心诉求 | 典型场景 |
| --- | --- | --- | --- |
| ToB：短漫剧公司 | 存量线性漫剧编辑、制片，面临同质化竞争 | 低成本切入互动/可玩赛道，复用存量编辑人力，不额外招游戏策划 | 把已有漫剧 IP 或成稿一键改成互动版本，做付费点/广告位测试 |
| ToC：小说作者/爱好者 | 有创意或成稿，缺游戏化与工程能力 | 独自把创意落地成可玩游戏，无需团队 | 上传自己的小说或输入设定，生成可分享、可变现的互动漫剧游戏 |

两类用户共用同一生成内核，差异在交付：ToB 侧重批量、可控、私有化与团队协作；ToC 侧重零门槛、引导式补全与一键分享。

---

## 3. 产品形态与核心体验

### 3.1 一条主线：从输入到可玩

用户流程分四段：**输入 → 引导补全 → 生成（多 Agent）→ 可视化编辑与预跑 → 发布可玩游戏**。其中「引导补全」是提质关键，「可视化编辑 + 模拟器预跑」是把 AI 初稿收敛成成品的人机协作环。

### 3.2 核心可玩元素

**叙事层**：

- 多分支剧情树，主线 + 支线，多结局
- 对话选择（影响属性与后续解锁）
- 漫剧化呈现：分镜图 + 对话框 + 旁白

**游戏层**：

- 穿插小游戏：限时点击、QTE、简单解谜等微交互
- 属性系统：好感度、勇气、金钱、隐藏值
- 分支解锁：属性阈值 / 前置选择 / 道具 / QTE 成绩

### 3.3 动静结合演出档位

| 档位 | 目标用户 | 演出形式 | 单部相对成本 |
| --- | --- | --- | --- |
| 全静态档 | C 端个人创作者、经费有限的爱好者 | 纯静态立绘 + 分镜图 + 对话框 + 旁白，完整承载分支与小游戏 | 最低（无视频成本，接近视觉小说） |
| 进阶动态档 | 有一定预算的 ToC 进阶用户 / 中小 ToB | 日常静态 + 关键情感节点或结局插入局部动效、短视频 | 中等，按动态节点数计费 |
| 全视频档 | ToB 商业客户、KOL、大 IP 项目 | 全流程视频演出，可直接对齐 SeedanceGo 视频向能力 | 最高，视频占主要开销 |

**叙事逻辑**：动静切换要服务于情绪强度，而不是随机分配。产品在生成阶段就为每个节点标注情绪强度与戏剧权重，作为演出形式决策的输入（对应「演出设计 Agent」）。

### 3.4 关键需求（P0/P1）

| 优先级 | 需求 | 行为与规则 | 验收标准 |
| --- | --- | --- | --- |
| P0 | 小说改编生成 | 上传 ≤N 万字小说，抽取情节/人设/世界观，生成带 ≥3 分支的互动剧本 | 生成剧本人设一致、分支无逻辑冲突、可在引擎运行 |
| P0 | 关键词原创生成 | 输入关键词，缺失要素时追问补全，再生成完整互动剧本 | 补全后生成成功率达标；无关键要素缺失导致的废稿 |
| P0 | 结构化可运行输出 | 输出强制 JSON（剧情树 + 节点 + 变量 + 互动指令），引擎可直接加载 | JSON 通过 schema 校验，引擎零改动可跑 |
| P0 | 支线不雷同 | 多支线内容向量去重，冲突/重复自动打回重写 | 支线相似度低于阈值；无明显重复桥段 |
| P1 | 可视化编辑器 | 剧情树与数值可视化编辑，人工微调节点/选择/属性 | 编辑结果实时回写 JSON 并可预跑 |
| P1 | 数值模拟器预跑 | 批量模拟玩家路径，输出分支到达率、结局分布、卡点 | 能定位不可达分支与数值失衡点 |
| P1 | 小游戏穿插 | 在合适节点插入限时点击/QTE，难度与奖励可配 | 小游戏可运行、难度可调、结果影响剧情 |

**非目标（当前阶段不做）**：真人肖像仿真剧、复杂 3D/实时对战玩法、UGC 社区与交易系统、多人在线互动。

---

## 4. 技术方案：多 Agent 生成流水线

### 4.1 整体架构链路

整个系统是一条「输入 → 多 Agent 串行流水线 → 结构化输出 → 引擎运行」的链路，底部由**模型路由、向量库、素材生成、数值模拟**四个公共支撑层托底，输出层再通过可视化编辑器回流迭代。

架构图（文字描述）：

```
┌─────────────────────────────────────────────────────────────────┐
│  输入层：小说文本  |  关键词/主题（含引导式追问补全）             │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     多 Agent 生成流水线                          │
│                                                                  │
│   ①解析 Agent ──► ②剧情规划 Agent ──► ③写作 Agent               │
│      (Parser)      (Story Planner)     (Writer)                 │
│                                            │                     │
│                                            ▼                     │
│   ⑦结构化输出 ◄── ⑥演出设计 Agent ◄── ⑤游戏化 Agent ◄─ ④一致性  │
│   (JSON Schema)    (Direction)         (Gamification)  校验     │
│                                                     (Consistency)│
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  支撑层：模型路由 | 向量库(RAG/去重) | 素材生成(图/视频) | 模拟器│
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  输出层：JSON 剧情树 + 可视化编辑器 + 预跑 → 引擎运行 → 可玩游戏  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 七个 Agent 的职责与关键约束

流水线借鉴 profile / tool / artifact 骨架：每个 Agent 是一个受限 profile，只暴露自己该用的工具，产物以 artifact 形式在链路上传递。

| Agent | 职责 | 关键约束 / 产物 |
| --- | --- | --- |
| ① 解析 Agent（Parser） | 读长文本，抽取情节框架、人物设定、世界观、关系图；关键词模式下做设定归纳 | 长上下文模型；产物为结构化设定包（人设卡、大纲、世界观） |
| ② 剧情规划 Agent（Story Planner） | 先定结构：剧情树骨架、分支节点、MECE 支线拆分、选择点位置 | 结构先行，支线按 MECE 互斥不重叠；产物为剧情树骨架 + 变量占位 |
| ③ 写作 Agent（Writer） | 在骨架上填内容：分支剧情、对话、旁白，追求冲突张力与「活人感」 | 创意写作用高温度 + 显式约束；按节点生成，避免整篇一次写 |
| ④ 一致性校验 Agent（Consistency Checker） | 校验人设/世界观/时间线一致性；对支线做向量去重，重复或冲突打回重写 | 低温度、强规则；产物为校验报告 + 打回指令 |
| ⑤ 游戏化 Agent（Gamification） | 把叙事变可玩：布置对话选择、插入 QTE/限时小游戏、挂接属性与分支解锁、埋数值点 | 产物为互动指令 + 数值挂点 + 小游戏配置 |
| ⑥ 演出设计 Agent（Direction / Staging） | 为每个剧情节点评估情绪强度与戏剧权重，分配演出档位：static / semi-dynamic / full-video；结合用户套餐档位做降级或升级 | 产物为节点级演出档位标签 + 素材需求清单；受预算/档位约束 |
| ⑦ 结构化输出（Structured Output） | 汇总为强制 JSON：剧情树 + 节点 + 变量 + 互动指令 + 演出档位，供引擎直接加载 | 强制 JSON schema，出错回退重试而非自由文本 |

### 4.3 支线不雷同：四个协同手段

「不同支线之间不出现逻辑冲突、也不互相雷同」是本产品最难、也最能拉开差距的地方。四个手段配合使用：

1. **结构先行**：由剧情规划 Agent 先产出互斥的支线骨架（MECE），让「分岔」发生在结构层而非文字层。
2. **显式约束**：写作 Agent 的每个分支 prompt 里显式写入「本支线必须区别于已生成支线 X 的以下要素：冲突源/结局走向/关键道具」。
3. **温度调控**：创意分支用较高温度扩大发散，一致性/结构环节用低温度收敛。
4. **向量去重**：一致性校验 Agent 把每条支线向量化，与已有支线算相似度，超阈值判定雷同并打回重写；向量库同时承担长程记忆。

---

## 5. 模型与 API 选型

选型遵循一条原则：**按环节的能力需求分配模型，而不是全链路用一个模型**。

| 环节 | 选型 | 选型理由 | 备选 / 回退 |
| --- | --- | --- | --- |
| 解析 Agent（长文本理解） | Gemini 1.5 Pro / GPT-4o | 百万级上下文，能一次吞下整本小说做全局理解 | Claude 长上下文；超长时先分块摘要再合并 |
| 写作 Agent（创意写作） | Claude（Sonnet/Opus 级） | 中文长文创作的文风与人物对话最接近「活人感」 | GPT-4o 作为风格对照 |
| 一致性校验 Agent | GPT-4o / Claude（低温度） | 需要严格规则判断与事实比对 | 规则引擎 + 小模型做初筛 |
| 演出设计 Agent | GPT-4o / Claude（中等温度） | 综合理解剧情语义、情绪强度与预算约束 | 小模型初筛 + 大模型校准关键节点 |
| 结构化输出 | GPT-4o（强制 JSON mode） | function calling / JSON mode 对 schema 遵从度高 | Claude tool use；失败重试 + 局部修补 |
| 向量化（去重/记忆） | text-embedding 类嵌入模型 | 支线相似度计算与长程记忆检索 | 开源 bge 系列，支持私有化 |
| 图像素材（静态 / 立绘 / 分镜） | 可灵 / Seedream | 漫剧风格图像质量与人物一致性控制成熟 | 按动静结合比例控制经费 |
| 视频 / 动效生成（进阶档、全视频档） | Seedance 系列 / 可灵视频 | 承接局部动效与完整视频演出 | 仅对演出设计 Agent 标记为 semi-dynamic / full-video 的节点调用 |

**接入方式**：模型路由层统一封装，按 Agent 的 profile 决定调用哪个模型；创意环节走高温度、校验/结构环节走低温度并强制 JSON。这样换模型或降级只改路由配置，不动业务链路。

> 本初版代码通过 OpenAI-Compatible API 抽象了 LLM 调用，只要修改 `.env` 里的 `base_url` 就可以对接 OpenAI / DeepSeek / 火山方舟 / 智谱 / 阿里通义 等任意兼容 OpenAI 协议的推理服务。

---

## 6. 结构化输出与数据结构

结构化输出是「AI 产物」与「可玩游戏」之间的合同。输出强制 JSON，核心对象如下（简化示意）：

```json
{
  "story_tree": {
    "nodes": [
      {
        "id": "n_012",
        "type": "dialogue",
        "content": "……",
        "choices": [
          {"text": "拔剑相向", "effects": {"勇气": 5}, "goto": "n_013"},
          {"text": "转身离开", "effects": {"好感度": -3}, "goto": "n_020"}
        ],
        "minigame": {"type": "timed_click", "window_ms": 800, "on_success": "n_014"},
        "staging": "semi-dynamic"
      }
    ],
    "endings": [{"id": "e_true", "unlock": "好感度>=60 && 勇气>=40"}]
  },
  "variables": {"好感度": 0, "勇气": 0, "金钱": 100},
  "assets": {"characters": [{"name": "沈砚", "ref_image": "..."}]}
}
```

引擎侧只认这份 schema：节点、选择、效果、跳转、小游戏、变量、解锁条件、素材引用、演出档位一应俱全。任何 Agent 产物最终都要收敛到它，校验不过则回退重试。

完整 Pydantic Schema 定义见 `src/manhua_agent/models.py`。

### 6.1 剧本格式：Schema 明细表（v1.1 基线，历史文档）

> 本表描述 v1.0 → v1.1 的基线 Schema，作为历史文档保留；v1.2 的字段扩展见 **6.4**。

| 顶层字段 | 类型 | 用途 |
| --- | --- | --- |
| `schema_version` | string | 版本号，v1.1 基线固定为 `"1.0"`（v1.2 起改为 `"1.2"`） |
| `title` / `logline` / `genre` | 基础元信息 | 作品名、简介、类型标签 |
| `variables` | dict[str,int] | 全局属性表（好感度/勇气/金钱…） |
| `story_tree.nodes` | list[Node] | 节点数组：`id / type / branch_id / character / content / choices / minigame / staging / emotion_intensity / asset_prompt` |
| `story_tree.endings` | list[Ending] | 结局数组：`id / branch_id / title / unlock (str) / is_true_ending / is_hidden` |
| `story_tree.start_node` | str | 起始节点 id |
| `assets.characters` | list[Character] | 人设卡列表（v1.1 仅 characters） |

v1.1 已知问题详见 6.3「剧本格式：v1.1 → v1.2 演进记录」。

### 6.3 剧本格式：v1.1 → v1.2 演进记录

**v1.1 待优化清单**（现已解决 → 见 6.4）：

| 问题 | 描述 | 状态 |
| --- | --- | --- |
| 剧情结构扁平 | Node 只有平铺 + branch_id，无幕/章/段层级 | 已解决 v1.2：加入 act_id / chapter_id / segment_order / parent_node_id |
| 演出字段粗糙 | 只有一个 asset_prompt 字符串，图/视频/BGM/CG/配音无法分开引用 | 已解决 v1.2：Scene + BGM + CG + Voiceover 顶层资产池 |
| 道具缺失 | 变量能表达连续量，但离散「拥有物」没有一等公民 | 已解决 v1.2：新增 Item + gain/consume/requires_items |
| 条件是字符串 DSL | `"好感度>=60 && 勇气>=40"`，下游要各自实现解析器 | 已解决 v1.2：Condition AST（discriminated union）+ evaluate() 方法 |
| 内容块类型太少 | dialogue/narration/... 不够；前端渲染差异（内心独白/系统提示/数值变化）没法表达 | 已解决 v1.2：NodeType 扩展为 8 种 |

**v1.2 兼容策略**：详见「常见问题」Q6。

### 6.4 v1.2 Schema 升级设计详解

> 本节记录 v1.2 所有 Schema 变更的**动机 / 设计 / 权衡 / 示例**。原则：**重要优化点必须经得起推敲——设计要有理由、被质疑时能站得住**。

---

#### 优化点 1：章节层级

**1) 背景与动机**

v1.1 的 `Node` 是完全平铺的节点数组，只用 `branch_id` 区分分支。这带来两个具体痛点：

- **前端做不出目录页**：《凤仪千秋》这类多幕宫斗剧的读者已经养成「回目录跳到某幕」的习惯；平铺结构下前端只能按数组下标切段，语义不明。
- **剧情结构与玩家路径混淆**：分支树（结构性）和玩家跳转（`Choice.goto`）本是两个正交概念，但 v1.1 把它们都塞在 nodes 的排列里，导致模拟器/编辑器要自行推断哪些节点属于同一「章」。

**2) 设计方案**

| 新字段 | 位置 | 类型 | 用途 | 空值语义 |
| --- | --- | --- | --- | --- |
| `Act` | 顶层 | list[Act] | 幕对象：`id / title / summary / chapter_ids` | `acts=None` 时表示未启用幕/章层级（早期剧本可只填 branch_id） |
| `Chapter` | 顶层 | list[Chapter] | 章对象：`id / act_id / title / summary` | 同上 |
| `Node.act_id` | 节点 | Optional[str] | 所属幕 | None → 下游按节点顺序推断 |
| `Node.chapter_id` | 节点 | Optional[str] | 所属章 | None → 允许，不影响运行时 |
| `Node.segment_order` | 节点 | Optional[int] | 本节点在同章内的段落顺序 | None → 按 nodes 数组顺序 |
| `Node.parent_node_id` | 节点 | Optional[str] | 叙事结构上的父节点 | 与 `Choice.goto` **独立**：parent 表示剧情树层级，goto 表示玩家路径 |

**3) 设计权衡**

- **为什么用「幕 → 章 → 段」三级而不是两级或四级？**
  - 两级（幕→节）表达力不足：宫斗/悬疑剧的「一幕多章、一章多段」是刚需，二级切不出来。
  - 四级（卷→幕→章→段）过设：长篇小说才用「卷」，短漫剧一部通常只 1 卷，多一层徒增负担。
  - 三级对齐传统剧本三/五幕结构，也对齐《凤仪千秋》「幕/章/节」惯例，普适性最好。
- **为什么 `parent_node_id` 与 `Choice.goto` 分开？**
  - `parent` 是**结构性**关系：n_c02_02 的 parent 是 n_c02_01，与玩家选了什么无关。
  - `goto` 是**运行时**跳转：受 `requires` / `Minigame.on_success` 影响。
  - 混在一起会让「剧情树可视化」和「玩家路径回放」互相拖累。

**4) 示例 JSON**

```json
{
  "acts": [
    {"id": "act_1", "title": "起势", "chapter_ids": ["c_prologue"]},
    {"id": "act_2", "title": "承转", "chapter_ids": ["c_b_truth_intro", "c_b_love_intro"]},
    {"id": "act_3", "title": "合",   "chapter_ids": ["c_b_truth_climax", "c_b_love_climax"]}
  ],
  "chapters": [
    {"id": "c_prologue",         "act_id": "act_1", "title": "序幕"},
    {"id": "c_b_truth_intro",    "act_id": "act_2", "title": "追寻真相 · 引入"}
  ],
  "story_tree": {
    "nodes": [
      {
        "id": "n_b_truth_02",
        "type": "dialogue",
        "act_id": "act_2",
        "chapter_id": "c_b_truth_intro",
        "segment_order": 2,
        "parent_node_id": "n_b_truth_01"
      }
    ]
  }
}
```

---

#### 优化点 2：场景与演出细化

**1) 背景与动机**

v1.1 一个节点用**一个字符串** `asset_prompt` 承载所有演出信息：场景、背景、镜头、BGM、CG、配音全糅在一起。真实素材流水线（可灵/Seedream/Seedance + BGM 检索 + TTS）需要**分别**取用：图像生成器只想要背景描述、TTS 只想要文本+音色 ID。字符串糅合导致：
- 各生成器要各自做正则/LLM 拆解 → 出错率高；
- 相同场景（同一「宫廷正殿」）在不同节点重复描述 → 生成的背景图**不一致**（画风漂移）。

**2) 设计方案**

拆分为「资产池 + 节点引用」两层结构。资产池顶层（`Assets.scenes / .bgms / .cgs / .voiceovers`），节点引用（`Node.scene_id / .bgm_id / .cg_id / .voiceover`）+ 细粒度字段（`.location / .background / .camera`）。

| 顶层对象 | 用途 | 关键字段 |
| --- | --- | --- |
| `Scene` | 场景。多 Node 复用同一 scene_id，避免 background 重复生成 | `id / location / background / description / default_bgm_id` |
| `BGM` | 背景音乐资产 | `id / name / description / url` |
| `CG` | CG 立绘/插画 | `id / description / scene_id / url` |
| `Voiceover` | 配音资产（内心声/系统音等） | `id / speaker / text / url` |

`Node` 上新增：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `scene_id` | Optional[str] | 场景 ID（引用 `Assets.scenes`） |
| `location / background / camera` | Optional[str] × 3 | 从 asset_prompt 拆出的地点 / 背景描述 / 镜头语言 |
| `bgm_id / cg_id / voiceover` | Optional[str] × 3 | 各资产 ID 引用 |
| `asset_prompt` | Optional[str] | **保留**，作为「汇总兜底」字段 |

**3) 设计权衡**

- **为什么保留 `asset_prompt`？**
  - 向下兼容：v1.1 剧本仍能读；
  - 素材生成流水线的 fallback prompt：如果某个节点没填细粒度字段，pipeline 还能用汇总串生成。
  - 代价是字段冗余，但按「兼容 > 简洁」权衡，值得。
- **为什么用 `bgm_id` 而不是直接嵌 `bgm: BGM` 对象？**
  - 引用式（ID）避免重复，多节点复用同一 BGM 时改一处即可；
  - 前端加载器可以做**懒加载**：只在真正播到该节点时才拉 URL。
- **为什么把 CG 也单独抽出来？**
  - CG 通常按「事件」而非「场景」组织（关键抉择前的立绘），与 Scene 的复用粒度不同。

**4) 示例 JSON**

```json
{
  "assets": {
    "scenes": [
      {"id": "s_courtyard", "location": "宫廷正殿", "background": "金碧辉煌的正殿全景",
       "default_bgm_id": "bgm_tense"}
    ],
    "bgms": [
      {"id": "bgm_calm",   "name": "舒缓·日常"},
      {"id": "bgm_tense",  "name": "紧张·推进"},
      {"id": "bgm_climax", "name": "激烈·高潮"}
    ],
    "cgs": [
      {"id": "cg_confrontation", "description": "主角与反派对峙的高情绪立绘",
       "scene_id": "s_courtyard"}
    ],
    "voiceovers": [
      {"id": "vo_inner_shenyan", "speaker": "沈砚·内心声"}
    ]
  },
  "story_tree": {
    "nodes": [
      {
        "id": "n_conflict_01",
        "type": "inner_monologue",
        "scene_id": "s_courtyard",
        "location": "宫廷正殿",
        "camera": "特写镜头",
        "bgm_id": "bgm_tense",
        "cg_id": "cg_confrontation",
        "voiceover": "vo_inner_shenyan",
        "asset_prompt": "沈砚，宫廷正殿，情绪强度0.8，特写镜头，内心独白……"
      }
    ]
  }
}
```

---

#### 优化点 3：道具系统

**1) 背景与动机**

v1.1 的「变量」只能表达**连续可累加量**（好感度 +5、勇气 +3）。真实剧本里有大量**离散、可拥有**的物件：
- 关键道具：宫廷令牌、密信、钥匙 —— 有 or 无，二值；
- 消耗品：药水、路引 —— 用一次减一件；
- 收集品：档案/卷宗 —— 集齐 N 件解锁隐藏结局。

用变量硬编码（例：`密令=1`）语义丑陋、也没法承载 `name / icon / description` 等展示信息。

**2) 设计方案**

新增顶层对象 `Item` + 节点/选择两层的道具进出字段。

| 对象/字段 | 类型 | 用途 |
| --- | --- | --- |
| `Item` | Assets 顶层 | `id / name / type / stackable / description / icon` |
| `ItemType` | Literal | `key_item` / `consumable` / `collectible` |
| `Node.gain_items` | list[str] | 进入该节点即获得的道具 ID |
| `Node.consume_items` | list[str] | 进入该节点即消耗的道具 ID |
| `Choice.requires_items` | list[str] | 选择本条**所需持有**的道具 |
| `Choice.gain_items` | list[str] | 选择本条**后获得**的道具 |
| `Choice.consume_items` | list[str] | 选择本条**后消耗**的道具 |

**3) 设计权衡**

- **道具 vs 变量：为什么两套并行？**
  - 语义完全不同：变量是「连续量」，道具是「离散物」；
  - 硬用变量表达道具会污染变量表（`密令=1` 与 `好感度=60` 放在一起，语义不齐）；
  - 前端 UI 完全不同：变量 = 数值条，道具 = 背包格。
- **`consume_items` 的校验规则**：`Structurer._self_repair` 保证 `consume_items` 里的每个 item 必须已被 `requires_items` 声明或已在既有节点 `gain_items` 出现过——否则去掉引用，避免运行时「消耗一个从未拥有过的道具」的诡异行为。
- **为什么 `Item.type` 只三种？**
  - 覆盖 95% 场景；再细分（例：装备 / 材料）留给后续 v1.3 扩展。

**4) 示例 JSON**

```json
{
  "assets": {
    "items": [
      {"id": "i_b_truth_key", "name": "证据", "type": "key_item", "stackable": false,
       "description": "揭露真相所需的关键证据"},
      {"id": "i_b_truth_potion", "name": "追寻真相·勇气丹", "type": "consumable", "stackable": true}
    ]
  },
  "story_tree": {
    "nodes": [
      {
        "id": "n_b_truth_02",
        "gain_items": ["i_b_truth_key"],
        "choices": [
          {
            "text": "服下勇气丹强攻",
            "requires_items": ["i_b_truth_potion"],
            "consume_items": ["i_b_truth_potion"],
            "effects": {"勇气": 5},
            "goto": "n_b_truth_03"
          }
        ]
      }
    ]
  }
}
```

---

#### 优化点 4：结构化触发条件（Condition AST）**——本次升级最重要、最要经得起考察的一项**

**1) 背景与动机**

v1.1 的 `Choice.requires` 与 `Ending.unlock` 都是纯字符串 DSL：

```
"好感度>=60 && 勇气>=40 && 金钱<100"
```

问题：

- **LLM 生成语法容易错**：`"好感度>=60 and 勇气>=40"`、`"好感度 >= 60 && 勇气≥40"`、变量名拼写变体（`好感度` vs `好感值`）—— 每一种下游都得兼容。
- **每个消费者要各自实现解析器**：模拟器、可视化编辑器、一致性校验、真机引擎——四份解析器逻辑一旦不一致，就是灾难。
- **无法静态校验**：字符串里引用的变量不在 `variables` 表中，只有真机跑到才发现。
- **没法引用非变量条件**：想加「玩家持有某道具」「玩家上一节点选过第 2 项」这类条件时，DSL 得再扩语法。

行业最佳实践：**结构化 AST（discriminated union）**。参考 Ren'Py `CondCombinator`、Unity Behavior Tree、Rasa Story——都放弃了字符串 DSL 走 AST。

**2) 设计方案**

用 Pydantic v2 `Annotated[Union[...], Field(discriminator="type")]` 定义 Condition：

```python
class ConditionBase(BaseModel):
    expression: Optional[str] = None   # 冗余，仅供人类阅读/调试

class VarCmp(ConditionBase):
    type: Literal["var_cmp"] = "var_cmp"
    var: str; op: Literal[">", ">=", "<", "<=", "==", "!="]; value: int

class HasItem(ConditionBase):
    type: Literal["has_item"] = "has_item"
    item_id: str; min_count: int = 1

class ChoiceTaken(ConditionBase):
    type: Literal["choice_taken"] = "choice_taken"
    node_id: str; choice_index: int

class And_(ConditionBase):    type: Literal["and"] = "and"; conditions: List["Condition"]
class Or_(ConditionBase):     type: Literal["or"]  = "or";  conditions: List["Condition"]
class Not_(ConditionBase):    type: Literal["not"] = "not"; condition: "Condition"

Condition = Annotated[Union[VarCmp, HasItem, ChoiceTaken, And_, Or_, Not_],
                      Field(discriminator="type")]
```

每个 Condition 变体都实现 `evaluate(state: EvalState) -> bool`，模拟器直接调用，**不需要**再实现解析器。

| 字段 | 语义 |
| --- | --- |
| `type` | discriminator：Pydantic 依此选择具体类 |
| `expression` | **冗余**、可选、字符串。仅供人类阅读；引擎不看此字段 |
| `evaluate(state)` | 递归求值。`EvalState` 包含 `variables / inventory / taken_choices` |

**3) 设计权衡**

- **为什么不继续用 DSL 字符串？**（承担全部质疑）
  - LLM 生成错：真实测试里生成率 ~5% 语法错、~10% 变量名拼写变体——不可接受。
  - 消费方重复实现解析器：4 处 × 各自 bug = 灾难。
  - 结构化 AST 是主流方案（Ren'Py CondCombinator / Unity Behavior Tree / Rasa Story）。
- **为什么用 Pydantic 的 discriminated union 而不是自定义类树？**
  - 类型安全：Pydantic v2 自动依 `type` 字段挑对子类，避免 dict 手动 dispatch。
  - JSON 可序列化：`model_dump_json()` 与 `model_validate_json()` 直接工作。
  - IDE 类型提示：`isinstance(cond, VarCmp)` 让 IDE 补全属性。
- **为什么保留 `expression`？**
  - **仅**供人阅读与调试；evaluate 不看此字段（即便 AST 与 expression 不一致，也以 AST 为准）。
  - LLM 生成时可以由 AST 反 render 一份人类可读表达式回填，方便审阅（`render_condition()`）。
- **为什么保留 `parse_condition(str) -> Condition` 兼容函数？**
  - 存量 v1.1 剧本仍能被 v1.2 读入；`Choice.requires` / `Ending.unlock` 的 `field_validator` 自动把字符串 parse 为 AST。
  - 但**不再作为默认路径**：Gamification Agent 生成时**必须**直接产出结构化 AST（System Prompt 里明确禁止字符串）。
- **`ChoiceTaken` 为什么用 `(node_id, choice_index)` 而不是 `choice_id`？**
  - `choice_index` 与前端 UI 直接对应（第几个按钮），无需额外给每个 Choice 生成 UUID。
  - `node_id` 已存在，够定位。

**4) 示例 JSON**

```json
{
  "endings": [
    {
      "id": "e_true",
      "title": "追寻真相·真结局",
      "unlock": {
        "type": "and",
        "expression": "好感度>=60 && 勇气>=40 && has_item(i_b_truth_key)",
        "conditions": [
          {"type": "var_cmp", "var": "好感度", "op": ">=", "value": 60},
          {"type": "var_cmp", "var": "勇气",   "op": ">=", "value": 40},
          {"type": "has_item", "item_id": "i_b_truth_key", "min_count": 1}
        ]
      }
    }
  ]
}
```

**兼容层**：v1.1 的 `"好感度>=60 && 勇气>=40"` 传入时，`_coerce_condition()` 自动 parse 为 `And_(VarCmp, VarCmp)`；无法解析时回退为「恒真占位」并把原字符串写到 `expression` 字段，同时抛 warning——**保证下游不崩，但留下调查痕迹**。

---

#### 优化点 5：内容块类型化

**1) 背景与动机**

v1.1 的 `NodeType` 只有 5 种：`dialogue / narration / choice / minigame / ending`。前端渲染差异很大：

- **对白气泡** vs **旁白横条** vs **内心独白斜体** vs **系统提示居中** —— 视觉样式完全不同；
- **TTS 配音**：旁白用旁白音色、内心独白用主角内心声（男主的低语）、系统提示不配音；
- **数值变化提示**（`【勇气 +5】`）需要独立成节点，方便前端做「数字跳动」动画。

v1.1 全部塞在 dialogue/narration 里，前端只能靠内容里的关键字/字符样式硬 parse——**极其脆弱**。

**2) 设计方案**

`NodeType` 扩展为 8 种（v1.1 原 5 种全部保留，向后兼容）：

| type | 语义 | 前端渲染 | TTS |
| --- | --- | --- | --- |
| `dialogue` | 对白 | 对话气泡 + 头像 | 角色音色 |
| `narration` | 旁白 | 横条底部 | 旁白音色 |
| `inner_monologue` | **v1.2**：内心独白 | 斜体 + 半透明底 | 主角内心声 |
| `system` | **v1.2**：系统提示 | 居中横条 + 图标 | 不配音 |
| `status_change` | **v1.2**：纯数值变化提示 | 数字跳动动画 | 不配音（或系统音效） |
| `choice` | 选择点 | 按钮组 | — |
| `minigame` | 小游戏 | 交互组件 | — |
| `ending` | 结局 | 结局卡 | 结局音乐 |

`ContentType` 语义别名 = `NodeType`。

**3) 设计权衡**

- **为什么不用「多媒体块混排」（`List[ContentBlock]`）？**
  - 会增加 3-4 层嵌套，前端解析成本↑↑，v1.2 阶段过设。
  - 现实里一个节点混排图/视频/表情包的场景占比不高（<5%）。
  - **留后手**：README 明确记录「后续如果要多媒体块混排，可再升级为 `List[ContentBlock]`，当前 `content: str` + `type` 的组合是过渡形态」。
- **为什么把 `status_change` 独立成节点，而不是把 effects 挂在 dialogue 上？**
  - 前端做「数字跳动动画」需要**明确的时机点**：知道从这一节点开始播放动画。
  - 与 dialogue 混在一起，前端就得判断「本 dialogue 是否包含 effects → 是则播动画」，逻辑分散。
  - 单独节点后，剧本作者也可以主动决定「什么时候提示玩家：勇气 +5」的节奏感。
- **为什么保留 `content: str` 而不是拆成 `text_blocks / images / audio`？**
  - 冗余渐进式演进：v1.2 只解决渲染类型问题，多媒体拆分留到需求真正出现时再做。

**4) 示例 JSON**

```json
[
  {"id": "n_02", "type": "narration",
   "content": "夜半的青瓦上，一枚火信纸悄然坠落。"},
  {"id": "n_03", "type": "inner_monologue", "character": "沈砚",
   "content": "……她说的话，我到底信几分？"},
  {"id": "n_04", "type": "status_change",
   "content": "【勇气 +5】"},
  {"id": "n_05", "type": "system",
   "content": "已解锁分支：追寻真相"}
]
```

---



## 7. 数值策划设计

互动漫剧游戏「好不好玩」，一半靠剧情，一半靠数值。AI 在其中的角色是「出初稿 + 跑验证」，人做「审美判断 + 微调」。

### 7.1 AI 在数值策划中的闭环

**AI 生成初版数值框架 → 可视化编辑（人工微调）→ 模拟器预跑检验 → 平衡性报告回填 → 再迭代**。

### 7.2 三大数值模块

| 模块 | 设计内容 | 设计要点 |
| --- | --- | --- |
| 属性系统 | 角色/剧情变量：好感度、勇气值、金钱、隐藏好感等；选择与小游戏结果对其增减 | 数量克制（3–6 个主属性）；每个属性都要有明确的解锁/结局用途 |
| 分支解锁条件 | 属性阈值（好感度≥60）、前置选择、道具持有、QTE 成绩组合 | 关键结局要「跳一跳够得到」；避免不可达分支和唯一解路径 |
| 小游戏数值平衡 | 限时点击窗口时长、难度曲线、成功率、奖励产出 | 难度随进度上升但留容错；奖励与剧情权重挂钩，不喧宾夺主 |

### 7.3 AI 能做什么、人做什么

**AI 负责**：依据剧情张力生成初版属性表与数值曲线；自动挂接选择→属性→解锁的逻辑；模拟器批量/蒙特卡洛预跑玩家路径；产出平衡性报告。

**人负责**：在可视化编辑器里审阅并微调数值；判断「难度手感」「情感节奏」等主观项；决定哪些结局是隐藏/彩蛋；对模拟器暴露的问题拍板取舍。

---

## 8. 关键风险与合规

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| 内容合规与备案 | 微短剧自 2024 年起分类分层审核，需备案/许可；AI 生成内容需按规定显著标识 | 接入审核前置；AI 生成内容加标识；敏感题材拦截 |
| 肖像权/版权 | 仿真人形象涉肖像权；改编第三方小说涉版权 | 默认漫剧风格、非真人；改编需上传方声明授权；提供版权提示 |
| 支线雷同/逻辑冲突 | 多分支下最易出的质量问题 | 结构先行 + 显式约束 + 向量去重 + 一致性校验四重兜底 |
| 生成成本失控 | 长文本 + 多 Agent + 图像素材叠加，单次生成成本高 | 模型分级路由、动静结合控图量、缓存与增量重生成 |
| ToC 废稿率 | 关键词太模糊导致生成质量差 | 引导式补全，把补全做成硬前置而非可选 |

---

## 9. 里程碑与验证

| 阶段 | 目标 | 交付 | 验证标准 |
| --- | --- | --- | --- |
| P0 MVP | 先把最核心的一步跑通：无论是拿一篇小说来改，还是只给几个关键词从零开始写，都能产出一份规范的剧情 JSON，并且这份 JSON 能被现有引擎直接跑起来 | 当前仓库提供的是 **7 个 Agent 串起来的生成流程**，外加一个能验证结果是否可跑的 demo。也就是说，你现在拿到这个包，已经可以做“输入故事素材/创意 → 自动生成互动漫剧游戏数据”这件事 | 至少能稳定产出一个 **3 个及以上分支**、能在引擎里跑通的完整 demo。**重点是：现在能做的是生成可运行的剧情与交互数据；还不能直接帮你把图像/视频素材、可视化编辑和数值调优这些后续能力一起做完** |
| P1 可用 | 在 P0 的基础上，把“能跑”升级成“更好改、更好调”。补上可视化编辑器、数值模拟器，以及更完整的小游戏穿插能力 | 交付会从“纯 AI 生成”升级为“AI 先生成，人再可视化修改”，同时给出分支平衡性和玩法表现的分析结果 | 不只是能生成，还要能证明这套内容更像一个成品：比如支线不要太像、玩家能走到主要分支、不同结局的分布要基本合理 |
| P2 商业化 | 再往后才是把产品真正做成可对外卖、可对外用的版本：支持 ToB 私有化/席位交付，也支持 ToC 一键分享、接广告或内购变现 | 除了生成能力本身，还会补齐发布、计费、IAA/IAP 对接等商业化基础设施 | 试点客户能够把这套能力真正用于“生产内容 → 发布上线 → 产生收入”的完整闭环 |

> **一句话理解这个仓库：它是 P0 阶段的参考实现，适合拿来验证“AI 能不能先把互动漫剧游戏的剧情数据自动生成出来”。**
>
> 你现在拿到这个包，**能做的事**主要是：输入小说或关键词，走完整的 7 Agent 流水线，产出结构化 JSON，并把这份 JSON 喂给引擎跑出一个可玩的互动漫剧 demo。
>
> **暂时不能直接靠这个包完成的事**包括：自动生成最终可用的图像/视频素材、用可视化界面改剧情、批量做数值平衡模拟、直接发布上线或接入商业化变现。
>
> 如果把它理解成产品阶段，它更像是一个“主链路验证包”——重点验证 **内容生成链路已经通了**，而不是一个开箱即用的完整生产平台。

---

## 10. 安装与使用（Quick Start）

### 10.1 环境要求

- Python **3.9+**
- 一个 OpenAI-Compatible 的 LLM 服务（OpenAI / DeepSeek / 火山方舟豆包 / 智谱 / 通义千问 均可）

### 10.2 安装步骤

```bash
# 1. 解压
unzip interactive-manhua-agent.zip
cd interactive-manhua-agent

# 2. （可选）创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 以可编辑模式安装本地包（关键）
pip install -e src/

# 5. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
```

### 10.3 两种输入模式

#### 模式一：小说改编

```bash
python -m manhua_agent.cli \
    --mode novel \
    --input examples/input_novel.txt \
    --output output/game.json \
    --staging semi-dynamic
```

#### 模式二：关键词原创

```bash
python -m manhua_agent.cli \
    --mode keywords \
    --keywords "民国,女法医,悬疑,双男主" \
    --output output/game.json \
    --staging static
```

也可以从 JSON 传入结构化关键词：

```bash
python -m manhua_agent.cli \
    --mode keywords \
    --input examples/input_keywords.json \
    --output output/game.json
```

### 10.4 参数说明

| 参数 | 含义 | 可选值 |
| --- | --- | --- |
| `--mode` | 输入模式 | `novel` / `keywords` |
| `--input` | 输入文件路径 | `.txt`（小说）或 `.json`（关键词） |
| `--keywords` | 关键词逗号分隔 | 例：`民国,女法医,悬疑` |
| `--output` | 输出 JSON 路径 | 默认 `output/game.json` |
| `--staging` | 演出档位 | `static` / `semi-dynamic` / `full-video` |
| `--branches` | 主分支数量 | 默认 `3` |
| `--dry-run` | 不调用 LLM，用规则生成占位样例 | 无需 API Key 即可跑通链路 |
| `--verbose` | 打印每个 Agent 的中间产物 | flag |

### 10.5 快速验证（无需 API Key）

```bash
# dry-run 模式仅使用规则生成器，用于验证安装成功
python -m manhua_agent.cli --mode keywords --keywords "校园,推理" --dry-run --verbose
```

看到 `output/game.json` 里含有 `story_tree.nodes` / `variables` / `endings` 结构即安装成功。

### 10.6 编程接口（Python API）

```python
from manhua_agent import run_pipeline, PipelineConfig

result = run_pipeline(
    PipelineConfig(
        mode="keywords",
        keywords=["民国", "女法医", "悬疑", "双男主"],
        staging="semi-dynamic",
        branch_count=3,
    )
)
print(result.model_dump_json(indent=2, ensure_ascii=False))
```

---

## 11. 项目结构

```
interactive-manhua-agent/
├── README.md                     ← 本文档
├── requirements.txt              ← 依赖（含 P1 Web 依赖）
├── pyproject.toml                ← 打包配置（含 manhua-agent / manhua-agent-web 入口）
├── .env.example                  ← 环境变量样例（含 P1 素材 API / VIDEO_RATIO）
├── examples/                     ← 输入/输出示例
│   ├── input_novel.txt
│   ├── input_keywords.json
│   └── output_sample.json
├── output/                       ← 运行结果输出目录（P1 Web 任务在 output/webruns/<id>/）
├── web/                          ← 【P1】本地向导前端（纯 HTML+JS，由后端托管）
│   ├── index.html                ← 向导页面
│   ├── style.css                 ← 向导样式
│   └── app.js                    ← 向导逻辑（步骤/轮询/HITL/预览/导出）
└── src/manhua_agent/
    ├── __init__.py               ← 顶层导出
    ├── cli.py                    ← 命令行入口（P0，保持不变）
    ├── config.py                 ← Pydantic 配置（P1 新增素材端点 + video_ratio）
    ├── llm.py                    ← 模型路由（OpenAI-compatible）
    ├── models.py                 ← 结构化输出 Schema（P1 Node 新增 media_type/media_url）
    ├── vectorstore.py            ← 向量去重（内存版）
    ├── graph.py                  ← LangGraph 流水线编排（P0）
    ├── pipeline_steps.py         ← 【P1】可暂停的分阶段执行器（Planner 后 HITL）
    ├── exporter.py               ← 【P1】导出可玩 H5 zip 包
    ├── prompts/
    │   └── system_prompts.py     ← 所有 Agent 的 system prompt
    ├── agents/                   ← 七个 Agent（P0，保持不变）
    │   ├── parser.py             ← ① 解析 Agent
    │   ├── planner.py            ← ② 剧情规划 Agent
    │   ├── writer.py             ← ③ 写作 Agent
    │   ├── consistency.py        ← ④ 一致性校验 Agent
    │   ├── gamification.py       ← ⑤ 游戏化 Agent
    │   ├── direction.py          ← ⑥ 演出设计 Agent
    │   └── structurer.py         ← ⑦ 结构化输出 Agent
    ├── assets/                   ← 【P1】动静混合素材
    │   └── generator.py          ← 动静决策 + OpenAI-Compatible 图片/视频生成
    ├── player/                   ← 【P1】H5 播放器引擎（预览与导出共用）
    │   ├── player.css / player.js
    │   └── index_template.html   ← 导出包入口模板
    └── server/                   ← 【P1】本地 FastAPI 服务
        ├── app.py                ← API 路由 + 静态托管（manhua-agent-web 入口）
        └── jobs.py               ← 任务生命周期与后台执行
```

### P1 API 一览（`manhua-agent-web` 启动后）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 向导前端页面 |
| GET | `/api/config` | 默认配置（video_ratio / 各 API 是否就绪） |
| POST | `/api/jobs` | 创建任务，自动跑到 Planner 后暂停 |
| GET | `/api/jobs/{id}/status` | 轮询进度（7 Agent 状态 + 素材进度） |
| GET | `/api/jobs/{id}/skeleton` | 取分支结构（HITL 审阅/编辑） |
| POST | `/api/jobs/{id}/confirm` | 确认（可带编辑后的分支结构）→ 继续 |
| GET | `/api/jobs/{id}/game` | 取最终 GameOutput（预览） |
| GET | `/api/jobs/{id}/assets/{file}` | 素材静态服务（预览） |
| POST | `/api/jobs/{id}/export` | 打包导出 zip |
| GET | `/api/jobs/{id}/download` | 下载导出的 zip |

---

## 12. 配置说明

`.env` 支持的字段：

```dotenv
# 主 LLM（写作/规划/一致性/游戏化/演出/结构化）
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 可选：为「解析 Agent」单独指定长上下文模型
PARSER_MODEL=gpt-4o
PARSER_BASE_URL=https://api.openai.com/v1

# 可选：为「写作 Agent」单独指定创意写作模型
WRITER_MODEL=claude-sonnet-4
WRITER_API_KEY=sk-ant-...
WRITER_BASE_URL=https://api.anthropic.com/v1

# 嵌入模型（用于支线去重）
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://api.openai.com/v1

# 温度分档
TEMPERATURE_CREATIVE=0.9   # 写作 Agent
TEMPERATURE_STRUCTURE=0.2  # 规划/一致性/结构化 Agent
TEMPERATURE_DIRECTION=0.5  # 演出设计 Agent

# 相似度阈值（超过则判定支线雷同，触发打回重写）
SIMILARITY_THRESHOLD=0.85

# ===== P1 新增：动静混合素材生成 =====
# 动态素材比例（视频节点占比，默认 ~20%）——只改这里即可调整动静比例，无需改代码
VIDEO_RATIO=0.2

# 图片生成 API（OpenAI-Compatible，填了就启用，没填就跳过素材生成）
IMAGE_API_KEY=sk-...
IMAGE_BASE_URL=https://api.openai.com/v1   # 未指定则复用 LLM_BASE_URL
IMAGE_MODEL=dall-e-3                        # 例：dall-e-3 / doubao-seedream-3-0-t2i
IMAGE_SIZE=512x512                          # 建议偏小，控制导出 zip 体积（≤8M）

# 视频生成 API（OpenAI-Compatible，填了就启用，没填就跳过素材生成）
VIDEO_API_KEY=sk-...
VIDEO_BASE_URL=https://api.openai.com/v1   # 未指定则复用 LLM_BASE_URL
VIDEO_MODEL=doubao-seedance                 # 例：doubao-seedance / kling-video
VIDEO_SIZE=512x512
```

未配置某个专用模型时，会**自动回退**到 `LLM_*` 主配置。
**图片 / 视频 API 若都不填，P1 会跳过素材生成步骤**，导出的游戏用程序化占位底图，依然完整可玩。

---

## 13. 常见问题

**Q1：没有 API Key 能不能跑？**
可以，加 `--dry-run` 即可用内置的规则占位生成器跑通完整链路，用于验证安装与理解 schema。

**Q2：某个 Agent 失败了怎么办？**
`--verbose` 会打印每个 Agent 的输入与产物；单个 Agent 失败会带回原始 LLM 响应，便于定位 prompt 或模型问题。结构化输出（Agent ⑦）失败会自动重试最多 3 次，仍失败则打回上一步。

**Q3：怎么换成火山方舟豆包/DeepSeek/通义千问？**
只要它们提供 OpenAI-compatible 接口，改 `.env` 里的 `LLM_BASE_URL` 与 `LLM_MODEL` 即可，业务代码零改动。

**Q4：图像/视频素材什么时候接入？**
本仓库属 P0 MVP，只跑通「文本 → 结构化 JSON」主链路。演出 Agent 会为每个节点生成素材需求清单（prompt + 档位），但实际调用可灵/Seedream/Seedance 的模块作为后续阶段接入点预留（`src/manhua_agent/agents/direction.py` 中的 `dispatch_asset_generation` 目前是占位）。

**Q5：怎么把生成结果接入引擎？**
输出的 JSON 就是引擎合约，字段含义严格对齐 `src/manhua_agent/models.py`。业界通用引擎（如 Ren'Py、Nova 系列、自研 H5 引擎）均可基于这份 schema 做加载器。

**Q6：v1.1 的 JSON 还能被 v1.2 的引擎读吗？**
可以。v1.2 严格保证向后兼容：

1. **旧字段全部保留**：v1.1 中的 `NodeType`、`asset_prompt`、`Assets.characters`、`Ending.unlock`（字符串）、`Choice.requires`（字符串）等都仍可读。
2. **缺失的 v1.2 字段自动用默认值填充**：
   - `Node.act_id / chapter_id / segment_order / parent_node_id` → `None`（下游按顺序推断）
   - `Node.scene_id / bgm_id / cg_id / voiceover / location / background / camera` → `None`（下游走 `asset_prompt` fallback）
   - `Node.gain_items / consume_items / Choice.requires_items / gain_items / consume_items` → `[]`
   - `Assets.scenes / items / bgms / cgs / voiceovers` → `[]`
   - `acts / chapters` → `None`
3. **`Choice.requires` / `Ending.unlock` 字符串会自动转成 Condition AST**：
   - 通过 `field_validator` 调用 `parse_condition(str) -> Condition`；
   - 支持 v1.1 常见语法：`var op value` / `A && B` / `A || B` / 括号；
   - **解析失败**时不会崩溃，而是回退为一个「恒真」的 `VarCmp(var='_expr', op='>=', value=0, expression=<原字符串>)`，并抛 warning——**下游可运行、但留下痕迹**方便人工修复。
4. **`schema_version` 手动指定**：v1.1 数据的 `schema_version` 保持 `"1.0"`；v1.2 生成的数据固定写 `"1.2"`。引擎侧可按此做兼容分支。

**不建议**：v1.2 起，Gamification Agent 生成的新剧本**必须**直接产出结构化 `Condition` 对象（System Prompt 里已禁止字符串），字符串路径**仅作**读入 v1.1 存量数据的兼容层。

---

## 版本信息

- **v1.0（P0 MVP）** · 2026-07-21 · 陆子桐
- 基础依据：本目录设计文档 v1.0 + 部门已有 SeedanceGo 交互式剧情 Agent 工程骨架
- **v1.2（Schema 升级：章节层级 + 场景演出 + 道具 + Condition AST + 内容块类型化）· 2026-07-21**
