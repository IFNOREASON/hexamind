# HexaMind 完整功能 MVP 实施计划

## Context

当前项目 `d:\WorkSpace\openclaw\ronglu` 下有两个静态 HTML 原型文件（page1.html、page2.html），其中 page2.html 是 HexaMind 的核心原型，包含 Three.js 3D 知识图谱、AI 对话框、文档管理、学习建议等完整 UI。目标是将其转化为 Vue 3 + FastAPI + LangGraph 的完整功能 MVP。

**核心功能：全模态知识图谱自动生成** -- 用户导入的资料（文档、链接、图片、视频、音频等）自动解析提取知识，生成统一的知识图谱。所有模态的知识合并到同一图谱中，节点标记来源模态类型，跨模态概念自动去重关联。**参考 graphify（D:\tools\graphify-4）的实现架构**，采用其置信度评分体系、三层去重策略、NetworkX 图构建、社区检测、超边支持和结构化 LLM 提取方案。

**MVP 策略：核心 + 预留** -- MVP 阶段完整实现文档（PDF/DOCX/TXT）和网页链接的解析与图谱生成；图片和音视频做好解析器接口预留（统一的 `BaseParser` 抽象），上传入口和数据模型已包含这些类型，后续接入 VLM/ASR 即可启用。

**技术选型确认：**
- 前端：Vite + Vue 3 (Composition API + TypeScript) + TailwindCSS
- 后端：FastAPI + SQLAlchemy + SQLite (MVP)
- AI Agent：LangGraph
- LLM：默认阿里通义千问（Qwen），支持配置切换
- 3D 可视化：仅保留 Three.js 主知识图谱视图
- 项目位置：`d:\WorkSpace\openclaw\ronglu\frontend` 和 `d:\WorkSpace\openclaw\ronglu\backend`

---

## 一、前端架构（frontend/）

### 1.1 项目结构

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── package.json
└── src/
    ├── main.ts
    ├── App.vue
    ├── assets/styles/
    │   ├── main.css                # Tailwind 指令 + 全局基础样式
    │   ├── glassmorphism.css       # .glass, .glass-strong
    │   ├── animations.css          # @keyframes: pulse-glow, breathe, slideIn, blink, flow
    │   └── scrollbar.css           # 滚动条美化
    ├── router/index.ts             # Vue Router（单路由，预留扩展）
    ├── stores/                     # Pinia 状态管理
    │   ├── source.ts               # 资料来源（文档/链接/图片/音视频）管理
    │   ├── graph.ts                # 知识图谱节点、边、选中状态
    │   ├── chat.ts                 # 聊天消息、输入状态
    │   ├── learning.ts             # 学习建议、掌握度
    │   └── ui.ts                   # 面板可见性、对话框展开
    ├── types/                      # TypeScript 类型定义
    │   ├── source.ts               # Source, SourceType, ParseStatus
    │   ├── graph.ts                # KnowledgeNode (含 sourceType, communityId, confidence), KnowledgeLink (含 confidence/confidenceScore), Hyperedge
    │   ├── chat.ts
    │   └── learning.ts
    ├── api/                        # API 调用层
    │   ├── client.ts               # Axios 实例配置
    │   ├── sources.ts              # 资料上传/链接提交/列表/删除
    │   ├── graph.ts
    │   ├── chat.ts                 # 支持 SSE 流式
    │   └── learning.ts
    ├── composables/                # Three.js 组合式函数
    │   ├── useThreeScene.ts        # 场景生命周期：init/animate/dispose
    │   ├── useKnowledgeGraph.ts    # 节点/边 mesh 动态创建、增量更新、布局、发光效果
    │   ├── useEmptyState.ts        # 空图谱引导动画（发光圆环+提示文字，数据到达后淡出）
    │   ├── useNodeInteraction.ts   # Raycaster 点击检测
    │   ├── useOrbitControls.ts     # 轨道控制器
    │   ├── useParticles.ts         # 背景粒子
    │   ├── useFileUpload.ts        # 拖拽+点击上传
    │   └── useTypingAnimation.ts   # 打字机动效
    ├── components/
    │   ├── layout/                 # 布局组件
    │   │   ├── TopNav.vue
    │   │   ├── LeftPanel.vue
    │   │   ├── RightPanel.vue
    │   │   ├── CenterCanvas.vue    # Three.js 容器 + 叠加控件
    │   │   └── BottomChat.vue
    │   ├── left/                   # 左侧面板子组件
    │   │   ├── SourceInput.vue     # 多模态输入：文件拖拽上传 + URL输入框 + 模态切换Tab
    │   │   ├── SourceList.vue      # 已导入资料列表（按模态类型显示不同图标）
    │   │   ├── SourceItem.vue      # 单条资料（图标按模态区分、名称、大小/URL、状态）
    │   │   └── TagCloud.vue
    │   ├── center/                 # 中间区域叠加组件
    │   │   ├── GraphControls.vue
    │   │   └── NodeDetailPopup.vue
    │   ├── right/                  # 右侧面板子组件
    │   │   ├── MasteryOverview.vue
    │   │   ├── SuggestionList.vue
    │   │   ├── SuggestionCard.vue
    │   │   └── DeadlineList.vue
    │   ├── chat/                   # 对话框子组件
    │   │   ├── ChatHeader.vue
    │   │   ├── ChatMessages.vue
    │   │   ├── ChatBubble.vue
    │   │   ├── ChatInput.vue
    │   │   ├── QuickActions.vue
    │   │   └── ChatMinimized.vue
    │   └── shared/                 # 共享组件
    │       ├── GlassCard.vue
    │       ├── GradientText.vue
    │       └── ProgressBar.vue
    └── utils/
        ├── colors.ts
        └── format.ts
```

### 1.2 组件层级

```
App.vue
├── TopNav
├── <main> (flex-1, flex row)
│   ├── LeftPanel (可折叠, w-80 ↔ w-0)
│   │   ├── SourceInput (Tab切换: 文件上传 / 链接输入 / 图片 / 音视频)
│   │   ├── SourceList → SourceItem (v-for, 图标按模态区分)
│   │   └── TagCloud
│   ├── CenterCanvas
│   │   ├── <div ref="canvasContainer">  ← Three.js 挂载
│   │   ├── GraphControls (绝对定位左上)
│   │   └── NodeDetailPopup (绝对定位右上)
│   └── RightPanel (可折叠)
│       ├── MasteryOverview
│       ├── SuggestionList → SuggestionCard (v-for)
│       └── DeadlineList
└── BottomChat
    ├── ChatMinimized (v-if 折叠)
    └── <expanded> (v-else)
        ├── ChatHeader
        ├── ChatMessages → ChatBubble (v-for)
        ├── ChatInput
        └── QuickActions
```

### 1.3 Three.js 集成策略

核心思路：将原型中 ~450 行内联 Three.js 代码拆分为 Vue 组合式函数（composables），通过 `onMounted`/`onBeforeUnmount` 管理生命周期。

**初始空图谱 + 动态构建**：应用启动时图谱无任何知识节点，仅展示粒子背景 + 中央引导动画（发光的 HexaMind logo 或脉冲圆环 + "导入资料开始构建知识图谱" 文字提示）。用户上传资料并解析完成后，`graphStore.nodes` 从空数组更新为实际数据，`useKnowledgeGraph` 监听到变化后动态创建节点 mesh 并以进入动画（节点从中心向外扩散 + 淡入）填充场景，引导提示自动消失。后续每次新增资料解析完成，增量追加新节点到已有图谱中（新节点以高亮脉冲动画出现，逐渐融入场景）。

- **useThreeScene**: 创建 Scene（FogExp2）、Camera（FOV 75）、Renderer（antialias + alpha），使用 `ResizeObserver` 替代 `window.resize`（面板折叠时画布自适应）
- **useKnowledgeGraph**: 监听 `graphStore.nodes/links` 响应式更新 mesh：
  - 空状态：不创建任何节点 mesh，场景仅有粒子和引导提示
  - 首次数据到达：批量创建节点，播放从中心扩散的进入动画
  - 增量更新：对比新旧节点列表，仅创建新增节点（高亮脉冲进入），移除已删除节点（淡出），保留已有节点不变
  - 实现同心环布局算法、节点呼吸发光效果、连线流动
- **useEmptyState**: 空图谱引导组件逻辑，监听 `graphStore.nodes.length`，为 0 时显示 Three.js 内的引导动画（发光圆环 + 粒子汇聚效果），节点出现后自动淡出
- **useNodeInteraction**: Raycaster 点击检测 → `graphStore.selectNode()`
- **useOrbitControls**: 阻尼 0.05、自动旋转、camera 重置，监听 store 状态
- **useParticles**: 500 粒子背景，随渲染循环缓慢旋转（空状态和有数据状态均展示）

Three.js 版本升级到 npm 包 v0.160+，使用 ES Module 导入 + TypeScript 类型。

### 1.4 API 集成

- Axios 实例：`baseURL` 从 `VITE_API_BASE_URL` 读取（默认 `http://localhost:8000/api`）
- AI 对话使用 SSE 流式（`fetch` + `ReadableStream`），逐 token 渲染
- 包含 Mock 模式（`VITE_USE_MOCK=true`），后端未就绪时使用原型硬编码数据

### 1.5 前端依赖

```
vue, vue-router, pinia, three, @types/three, axios
vite, @vitejs/plugin-vue, typescript, tailwindcss, postcss, autoprefixer, vue-tsc
@fontsource/inter
```

---

## 二、后端架构（backend/）

### 2.1 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # Pydantic Settings 配置
│   ├── database.py                # SQLAlchemy 异步引擎
│   ├── models/                    # ORM 模型
│   │   ├── source.py              # Source 表（统一资料来源：文档/链接/图片/音视频）
│   │   ├── graph.py               # GraphNode, GraphEdge 表
│   │   ├── chat.py                # ChatMessage 表
│   │   └── learning.py            # MasteryRecord 表
│   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── source.py
│   │   ├── graph.py
│   │   ├── chat.py
│   │   └── learning.py
│   ├── api/                       # API 路由
│   │   ├── router.py              # 路由聚合
│   │   ├── sources.py             # /api/sources/*（文件上传 + 链接提交）
│   │   ├── graph.py               # /api/graph/*
│   │   ├── chat.py                # /api/chat/*（SSE 流式）
│   │   └── learning.py            # /api/learning/*
│   ├── services/                  # 业务逻辑层
│   │   ├── source_service.py      # 资料导入统一入口
│   │   ├── graph_service.py       # NetworkX 图构建 + 数据库同步
│   │   ├── extraction_service.py  # 结构化 LLM 提取（graphify 风格提示词）
│   │   ├── cache_service.py       # SHA256 提取缓存管理
│   │   ├── cluster_service.py     # Leiden/Louvain 社区检测
│   │   ├── retrieval_service.py   # 知识库检索（关键词+TF-IDF，预留向量检索）
│   │   ├── chat_service.py
│   │   └── learning_service.py
│   ├── agents/                    # LangGraph 工作流
│   │   ├── ingest_agent.py        # 全模态资料处理 Agent（核心）
│   │   ├── chat_agent.py          # 对话 Agent
│   │   └── learning_agent.py      # 学习建议 Agent
│   ├── parsers/                   # 多模态解析器（统一 BaseParser 接口）
│   │   ├── __init__.py            # BaseParser 抽象类 + 分发器
│   │   ├── pdf_parser.py          # PyMuPDF          [MVP 实现]
│   │   ├── docx_parser.py         # python-docx       [MVP 实现]
│   │   ├── txt_parser.py          # chardet 编码检测   [MVP 实现]
│   │   ├── web_parser.py          # httpx + BeautifulSoup/trafilatura 网页抓取 [MVP 实现]
│   │   ├── image_parser.py        # VLM 图片理解       [接口预留，返回占位文本]
│   │   └── audio_video_parser.py  # ASR 语音识别       [接口预留，返回占位文本]
│   └── utils/
│       ├── llm.py                 # LLM 客户端初始化
│       └── memory.py              # LangGraph Checkpointer 配置（对话记忆持久化）
├── uploads/                       # 上传文件存储
├── data/                          # SQLite 数据库
├── .env
├── .env.example
├── requirements.txt
└── run.py                         # uvicorn 启动脚本
```

### 2.2 数据模型（参考 graphify 的节点/边/超边 schema）

**Source**（资料来源，统一所有模态）: id, name(文件名或URL标题), source_type(enum: document/link/image/audio/video), file_type(pdf/docx/txt/url/jpg/png/mp3/mp4等), file_size(bytes, 链接为null), file_path(本地路径, 链接为null), url(网页链接地址, 文件为null), status(uploaded/fetching/parsing/parsed/failed/unsupported), content_text(提取的文本内容), content_hash(SHA256, 用于缓存判断是否需要重新提取), metadata(JSON, 存储模态特有信息如网页标题/图片描述/音频时长), timestamps

**GraphNode**（参考 graphify node schema）: id(str, 确定性ID生成), name, description, category(root/core/concept/algorithm/technique/component), color, size, source_id(FK→Source), source_type(标记概念来自哪种模态), file_type(document/link/image/audio/video), community_id(int, 社区检测分配), timestamps

**GraphEdge**（参考 graphify 置信度体系）: id, source_node_id(FK→GraphNode), target_node_id(FK→GraphNode), relationship(is_a/part_of/prerequisite/related_to/semantically_similar_to/cites/rationale_for), confidence(enum: EXTRACTED/INFERRED/AMBIGUOUS), confidence_score(float 0.0-1.0), weight(float, 默认1.0), source_id(FK→Source, 标记此关系来自哪个资料), timestamps

**Hyperedge**（参考 graphify 超边设计，3+节点组关系）: id, label, relation(participate_in/implement/form), confidence(EXTRACTED/INFERRED), confidence_score, source_id(FK→Source), timestamps
**HyperedgeMember**: id, hyperedge_id(FK), node_id(FK→GraphNode) — 多对多关联表

**ChatMessage**: id, role(user/assistant), content, referenced_nodes(JSON), timestamps

**MasteryRecord**: id, node_id(FK→GraphNode, unique), mastery_level(0-100), last_reviewed_at, next_review_at, review_count, timestamps

**ExtractionCache**（参考 graphify SHA256 缓存机制）: id, content_hash(SHA256, unique), source_id(FK→Source), extracted_nodes(JSON), extracted_edges(JSON), extracted_hyperedges(JSON), timestamps — 相同内容不重复调用 LLM

### 2.3 API 端点设计

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/sources/upload | 上传文件（PDF/DOCX/TXT/图片/音视频），触发后台解析 |
| POST | /api/sources/link | 提交网页URL，触发后台抓取+解析 |
| GET | /api/sources | 资料列表（支持 ?type=document/link/image 过滤） |
| DELETE | /api/sources/{id} | 删除资料及关联图谱数据 |
| GET | /api/sources/{id}/status | 解析状态轮询 |
| GET | /api/graph | 获取完整知识图谱（节点含 source_type 字段） |
| GET | /api/graph/node/{id} | 节点详情（含来源资料信息） |
| POST | /api/graph/generate | 触发指定资料的图谱生成 |
| POST | /api/chat | AI 对话（SSE 流式响应） |
| GET | /api/chat/history | 历史消息 |
| GET | /api/learning/suggestions | AI 学习建议 |
| GET | /api/learning/mastery | 掌握度数据 |
| PUT | /api/learning/mastery/{node_id} | 更新掌握度 |

### 2.4 多模态解析器架构

所有解析器继承统一的 `BaseParser` 抽象基类：

```python
# parsers/__init__.py
class BaseParser(ABC):
    @abstractmethod
    async def parse(self, source: Source) -> ParseResult:
        """返回 ParseResult(text=提取文本, metadata=模态特有信息)"""
        ...

    @classmethod
    def supports(cls, source_type: str, file_type: str) -> bool:
        """判断此解析器是否支持该类型"""
        ...

def get_parser(source: Source) -> BaseParser:
    """根据 source_type + file_type 自动分发到对应解析器"""
```

| 解析器 | 模态 | MVP状态 | 实现方式 |
|--------|------|---------|----------|
| PdfParser | 文档 | 完整实现 | PyMuPDF 提取文本 |
| DocxParser | 文档 | 完整实现 | python-docx 提取段落 |
| TxtParser | 文档 | 完整实现 | chardet 编码检测 + 直接读取 |
| WebParser | 链接 | 完整实现 | httpx 抓取 + trafilatura 提取正文 |
| ImageParser | 图片 | 接口预留 | 预留 VLM 调用接口，MVP 返回 "图片解析功能即将上线" |
| AudioVideoParser | 音视频 | 接口预留 | 预留 ASR 调用接口，MVP 返回 "音视频解析功能即将上线" |

**WebParser 详细设计**（MVP 完整实现）：
- 使用 `httpx` 异步抓取网页（支持重定向、超时15s、User-Agent伪装）
- 使用 `trafilatura` 提取网页正文（自动去除导航/广告/页脚等噪音）
- 提取 metadata：页面标题、描述、发布时间
- 错误处理：超时/404/403 等情况标记 status="failed"

### 2.5 LangGraph Agent 工作流

**全模态资料处理 Agent** (`ingest_agent.py`) — 参考 graphify 的 detect→extract→build→cluster 管线：
```
route_by_modality → parse_content → check_cache → extract_concepts → build_graph → merge_and_dedup → cluster_communities → END
```
- State: source_id, source_type, raw_text, content_hash, metadata, concepts, relationships, hyperedges, nodes_created, status

- `route_by_modality`: 条件路由节点，根据 source_type 决定解析路径（同前）

- `parse_content`: 调用 `get_parser(source)` 获取对应解析器，执行解析，填充 raw_text 和 metadata

- `check_cache`（参考 graphify SHA256 缓存）: 计算 raw_text 的 SHA256 hash，查询 ExtractionCache 表。若命中则直接跳到 `merge_and_dedup`（跳过 LLM 调用），否则继续 `extract_concepts`

- `extract_concepts`（参考 graphify 结构化提取提示词）: 文本分块(~3000 token/块，200 token 重叠) → 使用 graphify 风格的结构化 LLM 提取。LLM 提示词要求：
  - 提取命名概念/实体，每个含 id、label、description、category
  - 提取关系，每条含 source→target、relation 类型、**置信度等级**（EXTRACTED/INFERRED/AMBIGUOUS）和 **confidence_score**（0.0-1.0）
  - 提取超边（3+ 节点组关系），每组含参与节点列表和组关系描述
  - 检测语义相似性：跨不同资料但解决相同问题的概念，添加 `semantically_similar_to` 边
  - 提取设计意图/原理说明，创建 `rationale_for` 边
  - 输出严格 JSON 格式（无 markdown、无说明文字）
  - LLM 提示词中注入 source_type 信息，不同模态使用不同提取策略：
    - 文档/链接：提取命名概念、实体、引用关系、设计原理
    - 图片（未来）：识别布局模式、图表数据、图示组件
    - 音视频（未来）：从转录文本中提取概念
  - 跨块合并去重：相同概念（名称大小写不敏感匹配）合并，保留更丰富的描述
  - 提取完成后写入 ExtractionCache

- `build_graph`（参考 graphify NetworkX 图构建）: 
  - 使用 **NetworkX** 在内存中构建有向图
  - 节点通过确定性 ID 生成（参考 graphify `_make_id`：名称部分拼接→非字母数字替换为下划线→小写）
  - NetworkX `add_node()` 天然幂等，同 ID 节点后写覆盖（语义节点覆盖结构节点，保留更丰富标签）
  - 每个节点记录 source_type、category，按 category 分配颜色和大小
  - 边携带 confidence + confidence_score + relation
  - 超边存储在 `G.graph["hyperedges"]` 中

- `merge_and_dedup`（参考 graphify 三层去重）:
  - **第一层**：提取阶段内 seen_ids 集合，同一资料内不产生重复节点
  - **第二层**：NetworkX add_node 幂等合并，跨资料相同 ID 自动合并
  - **第三层**：语义合并 — 将新提取的节点与数据库已有节点按名称匹配（大小写不敏感），已存在的概念只新增边不重复创建。初始化 MasteryRecord
  - 将 NetworkX 图序列化回数据库（GraphNode + GraphEdge + Hyperedge 表）

- `cluster_communities`（参考 graphify Leiden/Louvain 社区检测）:
  - 对完整图执行社区检测：优先 Leiden 算法（如 graspologic 可用），回退 Louvain
  - 将 DiGraph 转为无向图用于聚类
  - 处理孤立节点（单节点社区）
  - 过大社区自动拆分（> 25% 总节点数）
  - 计算社区内聚度（actual_edges / max_possible_edges）
  - 写回 GraphNode.community_id

**对话 Agent** (`chat_agent.py`) — 含记忆 + RAG 知识库检索：
```
load_memory → retrieve_from_knowledge_base → generate_response → save_memory → END
```
- **记忆机制**：使用 LangGraph 的 `checkpointer`（`MemorySaver` 或 `SqliteSaver`）持久化对话状态。每次对话自动加载历史上下文（thread_id 标识会话），Agent 能记住用户之前的提问和学习进展，实现多轮连续对话。
  - `load_memory`: 从 checkpointer 加载当前 thread 的对话历史和用户画像摘要（最近 N 轮完整消息 + 更早的摘要压缩）
  - `save_memory`: 对话完成后自动保存到 checkpointer，同时当消息数超过阈值时触发摘要压缩（LLM 将旧消息压缩为简短摘要，避免上下文无限增长）
- **RAG 知识库检索**：生成回复前，先从用户已导入资料构建的知识库中检索相关内容，确保 AI 回答基于用户实际资料而非纯粹的模型知识。
  - `retrieve_from_knowledge_base`: 将用户问题与 GraphNode 的 name/description 进行关键词匹配 + 语义相似度检索（MVP 阶段使用关键词匹配 + 简单的 TF-IDF 相似度，预留向量检索接口），同时检索关联的 Source.content_text 原文片段作为参考上下文。返回 top-K 相关节点 + 原文片段 + 掌握度数据。
  - `generate_response`: 构建系统提示，注入检索到的知识图谱上下文和原文片段。提示词明确要求 AI：(1) 优先基于用户资料回答，(2) 引用具体知识点时标注来源，(3) 结合用户掌握度给出个性化指导。流式输出，提取引用节点 ID。

**学习建议 Agent** (`learning_agent.py`) — 含记忆：
```
load_context → analyze_mastery → generate_suggestions → format_output → END
```
- `load_context`: 从 checkpointer 加载用户学习历史和偏好（哪些主题问得多、哪些反复出错）
- `analyze_mastery`: 查询所有 MasteryRecord，结合记忆中的学习行为识别薄弱点、逾期复习、前置缺失
- `generate_suggestions`: LLM 生成 3-5 条个性化建议，结合用户历史行为而非仅靠掌握度数字
- `format_output`: 结构化输出，映射到 node_id

### 2.5a 记忆与检索架构

**LangGraph Checkpointer 配置**（`app/utils/memory.py`）：
- MVP 使用 `langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver`，数据存储在 `data/memory.db`
- 每个用户一个 `thread_id`，对话状态自动持久化和恢复
- 后续可迁移到 PostgreSQL checkpointer

**知识库检索层**（`app/services/retrieval_service.py`）：
- `search_knowledge(query: str, top_k: int = 5)` → 从 GraphNode + Source 中检索相关内容
- MVP 实现：SQL LIKE 模糊匹配 GraphNode.name/description + 简单 TF-IDF 打分
- 预留接口：`VectorRetriever` 抽象类，后续接入向量数据库（如 Chroma/FAISS）做语义检索
- 返回结构：`[{ node: GraphNode, source_text_snippet: str, relevance_score: float }]`

### 2.6 LLM 配置

默认使用阿里通义千问（Qwen），通过 `langchain-openai` 的 `ChatOpenAI` 以 OpenAI 兼容模式调用：

```python
# app/config.py
LLM_PROVIDER = "qwen"  # qwen / openai / deepseek / ollama
LLM_API_KEY = "sk-xxx"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = "qwen-plus"
```

支持切换：修改 `.env` 中的 `LLM_BASE_URL` 和 `LLM_MODEL` 即可切换到 OpenAI / DeepSeek / 本地 Ollama。

### 2.7 后端依赖

```
# 核心框架
fastapi>=0.115.0, uvicorn[standard]>=0.30.0, python-multipart>=0.0.9
# 数据库
sqlalchemy>=2.0.0, aiosqlite>=0.20.0
# LangGraph / LangChain（含记忆持久化）
langgraph>=0.2.0, langgraph-checkpoint-sqlite>=2.0.0, langchain-core>=0.3.0, langchain-openai>=0.2.0
# 图构建与社区检测（参考 graphify）
networkx>=3.0, python-louvain>=0.16  # Louvain 社区检测
# graspologic>=3.4.0  # 可选：Leiden 算法（更优但依赖较重，Python<3.13）
# 文档解析 [MVP]
PyMuPDF>=1.24.0, python-docx>=1.1.0, chardet>=5.0.0
# 网页抓取 [MVP]
httpx>=0.27.0, trafilatura>=1.12.0
# LLM 工具
tiktoken>=0.7.0
# 检索（MVP TF-IDF）
scikit-learn>=1.5.0
# 配置
pydantic-settings>=2.0.0
```

---

## 三、实施步骤

### 步骤 1：前端项目脚手架
- Vite + Vue 3 + TypeScript 项目初始化
- 安装并配置 TailwindCSS、PostCSS、自定义主题色
- 从 page2.html 提取全局样式（glassmorphism, animations, scrollbar）
- 设置 Vue Router（单路由）+ Pinia
- 创建所有 store 文件，填入 Mock 数据

### 步骤 2：前端静态 UI 组件
- 迁移 TopNav、LeftPanel（多模态 SourceInput + SourceList + TagCloud）
  - SourceInput 包含 Tab 切换：文件上传区（拖拽+点击）/ URL 输入框 / 图片上传 / 音视频上传
  - SourceList 根据 source_type 显示不同模态图标（文档📄、链接🔗、图片🖼、音频🎵、视频🎬）
- 迁移 RightPanel（MasteryOverview + SuggestionList + DeadlineList）
- 迁移 BottomChat（ChatHeader + ChatMessages + ChatInput + QuickActions）
- 接入 UI store 实现面板折叠/展开、对话框最小化
- 使用 Mock 数据验证视觉还原度

### 步骤 3：Three.js 知识图谱集成
- 实现 useThreeScene 组合式函数（场景/相机/渲染器/ResizeObserver）
- 实现 useKnowledgeGraph（节点 mesh、同心环布局、呼吸发光、连线流动）
  - **节点视觉区分模态来源**：不同 source_type 的节点使用不同形状或光环颜色标记
  - **社区着色**：同一 community_id 的节点使用同一色系，社区间视觉可区分
  - **置信度视觉映射**：边的透明度/虚实由 confidence_score 决定（高置信度实线亮色，低置信度虚线暗色）
  - **超边可视化**：同一超边内的节点用半透明色块包围标记组关系
- 实现 useOrbitControls、useParticles、useNodeInteraction
- 在 CenterCanvas 中编排所有组合式函数
- 验证：节点点击详情（含来源模态、社区、置信度信息）、自动旋转、面板折叠时画布自适应

### 步骤 4：后端项目脚手架
- 创建 FastAPI 项目结构
- 配置 Pydantic Settings（LLM、数据库、CORS）
- 定义 SQLAlchemy ORM 模型（Source、GraphNode、GraphEdge、Hyperedge、HyperedgeMember、ChatMessage、MasteryRecord、ExtractionCache）
- 定义 Pydantic 请求/响应模式（GraphNode 响应含 confidence、community_id、source_type；GraphEdge 响应含 confidence/confidence_score）
- 实现数据库自动建表
- 验证：启动服务器，健康检查端点返回 200

### 步骤 5：资料管理 API + 多模态解析器
- 实现 BaseParser 抽象基类和解析器分发器
- 实现 MVP 解析器：PdfParser、DocxParser、TxtParser、WebParser
- 实现预留解析器：ImageParser、AudioVideoParser（返回占位提示）
- 实现资料 API：文件上传 `/api/sources/upload`、链接提交 `/api/sources/link`、列表/删除/状态
- 文件保存到 uploads/，链接抓取的 HTML 转文本存入 content_text
- 验证：上传 PDF + 提交 URL，确认解析成功；上传图片确认返回"即将上线"提示

### 步骤 6：LangGraph 全模态处理 Agent（graphify 架构）
- 实现 ingest_agent 完整工作流：route_by_modality → parse → check_cache → extract → build → merge_dedup → cluster → END
- 实现 extraction_service：graphify 风格结构化 LLM 提取提示词（严格 JSON schema 输出，含置信度评分）
- 实现 cache_service：SHA256 内容哈希缓存，相同内容跳过 LLM 调用
- 实现 graph_service：NetworkX 内存图构建 + 确定性节点 ID 生成 + 三层去重 + 数据库同步
- 实现 cluster_service：Louvain 社区检测（可选 Leiden），孤立节点处理，过大社区拆分
- 超边提取与存储（Hyperedge + HyperedgeMember 表）
- 作为 BackgroundTask 在上传/提交后自动触发
- 验证：
  - 上传 PDF → 查看 /api/graph → 节点含 confidence、community_id、source_type
  - 提交相关网页 URL → 跨模态概念去重验证（同名概念合并，只新增边）
  - 重复上传同一文件 → 确认缓存命中，不重复调用 LLM

### 步骤 7：LangGraph 对话 Agent + 记忆 + RAG + SSE 流式
- 实现 LangGraph Checkpointer 配置（AsyncSqliteSaver → data/memory.db）
- 实现 retrieval_service（关键词匹配 + TF-IDF 相似度检索 GraphNode + Source 原文片段）
- 实现 chat_agent 完整工作流：load_memory → retrieve_from_knowledge_base → generate_response → save_memory
- 对话记忆：通过 thread_id 自动加载/保存会话状态，超阈值时 LLM 压缩摘要
- RAG 检索：回复前从知识库检索 top-K 相关节点和原文片段，注入提示词
- 实现 SSE StreamingResponse 端点
- 对话保存到数据库，响应中包含引用节点 ID
- 验证：
  - 多轮对话测试 → 确认 Agent 记住之前提问的上下文
  - 提问已上传资料中的知识点 → 确认回复引用了实际资料内容而非通用知识
  - 流式输出 → 关联节点高亮

### 步骤 8：LangGraph 学习建议 Agent（含记忆）
- 实现 learning_agent（含 checkpointer 记忆加载，分析用户学习行为模式）
- 实现掌握度 CRUD 和建议端点
- 间隔重复算法（next_review_at = now + 2^review_count 天）
- 验证：更新掌握度 → 获取个性化建议（建议应结合用户历史学习行为）

### 步骤 9：前后端联调
- 前端 API 层对接真实后端（替换 Mock）
- 完整链路测试：
  - 上传 PDF → 解析 → 图谱渲染 → 3D 节点显示文档模态标记
  - 提交网页链接 → 抓取解析 → 新概念合并到已有图谱 → 跨模态去重验证
  - 上传图片 → 显示"即将上线"状态
  - 对话中提问 → 流式回复 → 相关节点高亮
  - 学习建议正确显示
- 处理 CORS、错误提示、加载状态

---

## 四、关键文件清单

### 前端
- `frontend/src/composables/useThreeScene.ts` — Three.js 与 Vue 生命周期桥接
- `frontend/src/composables/useKnowledgeGraph.ts` — 3D 图谱动态创建与增量更新核心（含模态来源视觉区分）
- `frontend/src/composables/useEmptyState.ts` — 空图谱引导动画（数据到达前的视觉引导）
- `frontend/src/stores/source.ts` — 多模态资料来源状态管理
- `frontend/src/stores/graph.ts` — 知识图谱数据中心
- `frontend/src/components/left/SourceInput.vue` — 多模态输入组件（文件上传+URL输入+Tab切换）
- `frontend/src/components/layout/CenterCanvas.vue` — 编排所有 Three.js 组合式函数
- `frontend/src/api/sources.ts` — 资料上传/链接提交 API 集成
- `frontend/src/api/chat.ts` — SSE 流式对话集成

### 后端
- `backend/app/parsers/__init__.py` — BaseParser 抽象类 + 解析器分发（全模态架构核心）
- `backend/app/parsers/web_parser.py` — 网页抓取+正文提取（MVP 新增）
- `backend/app/agents/ingest_agent.py` — 全模态资料处理 LangGraph 工作流（核心，graphify 架构）
- `backend/app/agents/chat_agent.py` — 对话 Agent（记忆 + RAG 检索 + 流式输出）
- `backend/app/services/extraction_service.py` — graphify 风格结构化 LLM 提取（提示词+JSON schema）
- `backend/app/services/graph_service.py` — NetworkX 图构建 + 三层去重 + DB 同步
- `backend/app/services/cache_service.py` — SHA256 提取缓存
- `backend/app/services/cluster_service.py` — Leiden/Louvain 社区检测
- `backend/app/services/retrieval_service.py` — 知识库检索服务（关键词+TF-IDF，预留向量检索）
- `backend/app/utils/memory.py` — LangGraph Checkpointer 配置（对话记忆持久化）
- `backend/app/models/source.py` — 统一资料来源数据模型
- `backend/app/models/graph.py` — GraphNode + GraphEdge + Hyperedge + ExtractionCache 模型
- `backend/app/main.py` — FastAPI 入口
- `backend/app/config.py` — LLM/数据库配置
- `backend/app/api/sources.py` — 资料上传/链接提交端点

### 原型参考
- `d:\WorkSpace\openclaw\ronglu\page2.html` — UI 样式、布局、动效的参考源

---

## 五、验证方案

1. **前端验证**：`npm run dev` 启动 Vite 开发服务器，对照 page2.html 原型检查视觉还原度、Three.js 动效、面板交互、多模态输入组件
2. **后端验证**：`python run.py` 启动 FastAPI，使用 `/docs` Swagger UI 测试所有端点
3. **多模态解析验证（graphify 架构）**：
   - 上传 PDF → 状态变为 "parsed" → /api/graph 返回节点（含 community_id、confidence）和带置信度评分的边
   - 提交网页 URL → 状态变为 "parsed" → 图谱新增来自该网页的概念
   - 上传同一主题的 PDF + 网页 → 确认跨模态三层去重（同名概念合并为一个节点，新增跨模态边）
   - 重复上传相同文件 → SHA256 缓存命中，不重复 LLM 调用
   - 社区检测验证 → 相关概念自动聚类到同一社区，节点含 community_id
   - 超边验证 → 3+ 节点的组关系正确提取并可通过 API 查询
   - 上传图片 → 状态变为 "unsupported"，前端显示"即将上线"
4. **端到端验证**：
   - 空状态验证：首次打开页面 → 图谱区显示引导动画（发光圆环+"导入资料开始构建知识图谱"提示） → 上传资料后引导消失，节点以从中心扩散的动画出现
   - 增量更新：已有图谱基础上再导入新资料 → 新节点以高亮脉冲追加，跨模态已有概念不重复
   - 完整链路：导入多种资料 → 图谱从空动态生成 → 3D 可视化（节点标记模态来源）→ AI 对话 → 学习建议
   - 图谱节点点击 → 详情弹窗显示来源模态和来源资料名称
5. **记忆验证**：连续多轮对话 → AI 记住之前的提问上下文（如 "我刚才问的那个概念" 能正确理解）→ 刷新页面后再次对话 → 确认记忆从 checkpointer 恢复
6. **RAG 知识库检索验证**：提问已上传资料中的具体知识 → 回复引用实际资料内容而非通用模型知识 → 回复中标注来源节点 → 对应节点在图谱中高亮
7. **类型检查**：`npx vue-tsc --noEmit` 确保 TypeScript 无错误
8. **代码质量**：前端 `npm run lint`，后端使用 ruff 检查
