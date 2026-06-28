# 🎬 Bili Collection Pipeline

> **B站合集批量转录工具 · Batch Bilibili Collection Transcriber**

一键把B站**整个合集**转成可读的文本！从200+集的波士顿圆脸，到36集的MIT电磁学公开课，这套流水线已实战验证上千集。

Batch-transcribe an entire Bilibili collection into readable Markdown. Proven on 1000+ videos from 200-episode news commentary to 36-episode MIT physics lectures.

---

## 🇨🇳 中文说明

### 核心流程

```
B站合集链接 → fetch_collection.py → 视频列表JSON
                                   → transcribe_collection.py → 下载→提音频→Whisper转录
                                                                  → semantic_segment.py → 语义分段
                                                                                         → .md知识库
```

### 快速开始

```bash
# 1. 安装依赖
pip install faster-whisper requests
# 还需系统安装 you-get 和 ffmpeg
# 备选下载器 yt-dlp

# 2. 拉取合集视频列表
python3 scripts/fetch_collection.py "https://www.bilibili.com/video/BVxxxxxx" -o collection.json

# 3. 批量转录
python3 scripts/transcribe_collection.py collection.json --output ./output --model small

# 4. 语义分段
python3 scripts/semantic_segment.py ./output/*.md
```

### 参数说明

#### transcribe_collection.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `videos_json` | 视频列表JSON | 必填 |
| `--output` / `-o` | 输出目录 | `./transcripts` |
| `--model` | Whisper模型 (tiny/base/small/medium/large-v3) | `small` |
| `--device` | 运行设备 (cuda/cpu) | `cuda` |
| `--downloader` | 下载器 (you-get/yt-dlp) | `you-get` |
| `--progress` | 进度文件路径 | `progress.json` |
| `--skip-download` | 跳过下载，仅转录 | false |
| `--limit` | 最大处理集数 | 全部 |

#### semantic_segment.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `files` | 待分段.md文件 | 必填 |
| `--force` | 强制重新分段 | false |

### 特性

- **合集级支持** — 直接解析B站合集（播单），而非仅限于UP主空间
- **断点续传** — 每集完成自动记录进度，重跑自动跳过
- **语义分段v2** — 基于 Jaccard 词汇连贯性 + 结构信号（指代/逻辑连词/设问/列举）的智能分段
- **GPU加速** — 支持 NVIDIA CUDA，RTX 4050 实测 ~7x 实时
- **LLM后处理**（可选）— 通过 DeepSeek / OpenAI 兼容 API 做错别字修正或散文化改写

### 输出格式

```markdown
# 视频标题

> BVID: BVxxxxxx | 时长: 10分43秒

转录正文...

---

## 段落1
...
```

### 实战战果

- 波士顿圆脸「MAGA东山再起」— 203集，~51h ✅
- 战争研究所「研究一下」— 102集，~17.6h ✅
- 山河有声「战略杂谈」— 126集，~44.7h ✅
- MIT 8.02 电磁学公开课 — 36集，英→中翻译 ✅
- 金砖支付合集 — 8集 ✅

---

## 🇬🇧 English

### Pipeline

```
Bilibili URL → fetch_collection.py → videos JSON
                                   → transcribe_collection.py → download→audio→Whisper→.md
                                                                  → semantic_segment.py → smart paragraphing
```

### Quick Start

```bash
# 1. Install dependencies
pip install faster-whisper requests
# System tools: you-get + ffmpeg (or yt-dlp as fallback)

# 2. Fetch collection video list
python3 scripts/fetch_collection.py "https://www.bilibili.com/video/BVxxxxxx" -o collection.json

# 3. Batch transcribe
python3 scripts/transcribe_collection.py collection.json --output ./output --model small

# 4. Semantic segmentation
python3 scripts/semantic_segment.py ./output/*.md
```

### Features

- **Collection-level support** — targets Bilibili playlists/collections, not just entire UP channels
- **Resume support** — auto-saves progress after each video; re-running skips completed ones
- **Smart paragraphing** — Jaccard vocabulary coherence + structural signals (reference words, logical connectors, Q&A patterns)
- **GPU accelerated** — NVIDIA CUDA; ~7× realtime on RTX 4050
- **LLM post-processing** (optional) — typo correction or prose polishing via DeepSeek/OpenAI

### CLI Reference

#### transcribe_collection.py

| Flag | Description | Default |
|------|-------------|---------|
| `videos_json` | Video list JSON (required) | — |
| `--output` / `-o` | Output directory | `./transcripts` |
| `--model` | Whisper model size | `small` |
| `--device` | Device (cuda/cpu) | `cuda` |
| `--downloader` | Downloader backend | `you-get` |
| `--progress` | Progress file | `progress.json` |
| `--skip-download` | Skip download, transcribe only | false |
| `--limit` | Max videos | all |

### Production Stats

- Boston Round Face "MAGA Rises Again" — 203 episodes ✅
- War Studies "Let's Look Into It" — 102 episodes ✅
- Shanhe Podcast "Strategic Talks" — 126 episodes ✅
- MIT 8.02 Electromagnetism — 36 episodes ✅ (EN→CN)
- BRICS Payment Series — 8 episodes ✅

---

## 📦 Installation

```bash
# Clone
git clone https://github.com/xiaozishan/bili-collection-pipeline.git
cd bili-collection-pipeline

# Python deps
pip install faster-whisper requests

# System deps
# you-get:  https://github.com/soimort/you-get
# ffmpeg:   https://ffmpeg.org/
# yt-dlp:   https://github.com/yt-dlp/yt-dlp  (alternative downloader)
```

## 📁 Project Structure

```
bili-collection-pipeline/
├── SKILL.md                     # ClawHub skill metadata
├── README.md                    # This file
├── requirements.txt             # Python dependencies
└── scripts/
    ├── fetch_collection.py      # Fetch collection video list via Bilibili API
    ├── transcribe_collection.py # Download → transcribe → save pipeline
    └── semantic_segment.py      # Smart paragraph segmentation (v2)
```

## 📜 License

MIT
