# KnowledgeFlow - 个人知识流管理平台

> AI驱动的知识管理工具：导入→整理→检索→画像，一站式学习知识管家

## 项目结构

```
project/
├── src/                    # 最新源代码（当前 PyQt 版本）
│   ├── knowledgeflow_pyqt_dashboard.py   # 主程序（后端逻辑 + PyQt5 GUI）
│   ├── web_importer.py                   # 网页导入模块（B站/小红书/通用）
│   ├── requirements_pyqt_mvp.txt         # Python 依赖
│   └── run_pyqt_mvp_windows.bat          # Windows 启动脚本
│
├── data/                   # 运行时数据
│   ├── organized_output/   # AI 整理后的知识条目
│   ├── read_demo_output/   # 原始解析结果（PDF/DOCX/视频/网页）
│   ├── vector_index/       # FAISS 向量索引
│   ├── bilibili_audio_cache/  # B站音频缓存
│   └── web_import_cache/   # 网页导入缓存
│
├── models/                 # AI 模型
│   └── faster-whisper-large-v3/  # Whisper 语音转写模型
│
├── test_data/              # 测试数据集
│   ├── 测试集/             # 多格式兼容/综合能力评测集
│   └── 测试集.zip
│
├── docs/                   # 文档资料
│   ├── presentations/      # PPT 汇报文件
│   ├── ppt_pictures/       # PPT 用图片
│   └── tech_roadmap/       # 技术路线图
│
├── media/                  # 视频/截图等媒体文件
│
├── archive/                # 历史存档（旧版本，仅供参考）
│   ├── milestone1_demos/   # Milestone 1 早期 demo 脚本
│   ├── milestone1_data/    # Milestone 1 输出数据
│   ├── milestone2_data/    # Milestone 2 中间数据（重复的）
│   ├── boyang_hou/         # Boyang_Hou 旧版本分支
│   ├── combination/        # conbination 旧版本分支
│   └── old_pyqt_versions/  # PyQt 迭代版本历史
│
├── milestone2/             # [旧目录] 原始 milestone2 结构，保留不动
│   ├── Boyang_Hou/
│   ├── conbination/
│   ├── models/
│   ├── new_frontend/
│   ├── 技术路线/
│   └── 测试集/
│
└── ppt picture/            # [旧目录] 原 PPT 图片，已迁至 docs/ppt_pictures/
```

## 核心功能

| 模块 | 说明 |
|------|------|
| 文件导入 | PDF/DOCX/PPTX/TXT/图片/视频（Whisper转写） |
| 网页导入 | B站（WBI签名）/ 小红书 / 通用网页 / YouTube |
| AI 整理 | Qwen/DeepSeek LLM 自动提取结构化知识 |
| 混合检索 | 向量召回 + 关键词召回 + 重排序 |
| 知识画像 | 规则画像（即时）+ LLM 深度画像（后台） |

## 技术栈（当前 PyQt 版）

- **GUI**: PyQt5（深色科技感主题）
- **LLM**: Qwen / DeepSeek（OpenAI-compatible API）
- **向量检索**: FAISS + paraphrase-multilingual-MiniLM-L12-v2
- **语音转写**: faster-whisper / openai-whisper
- **网页抓取**: B站API+WBI / trafilatura+BeautifulSoup4 / yt-dlp

## 下一阶段：Web 迁移

计划迁移至 **Vue 3 + Vite + FastAPI** 架构，支持本地运行及未来服务器部署。
