---
name: bili-collection-pipeline
description: "B站合集批量转录：拉取列表→you-get下载→ffmpeg提音频→faster-whisper转录→语义分段"
metadata:
  openclaw:
    requires:
      bins: [you-get, ffmpeg]
    install:
      - id: python
        kind: pip
        package: faster-whisper requests
        label: Install Python deps
---

# Bili Collection Pipeline

一键批量转录B站合集（播单），输出按语义分段的 Markdown 文件。

## 流程

```
B站视频链接 → fetch_collection.py → 视频列表JSON
                                   → transcribe_collection.py → 下载→提音频→Whisper转录
                                                                  → semantic_segment.py → 语义分段
                                                                                         → .md知识库
```

## 前置依赖

```bash
# 系统工具
# you-get:  https://github.com/soimort/you-get
# ffmpeg:   https://ffmpeg.org/
# yt-dlp:   备选下载器

# Python
pip install faster-whisper requests
```

## 完整用法

### 1. 拉取合集视频列表

```bash
python3 scripts/fetch_collection.py "https://www.bilibili.com/video/BV1GeDSYhEVZ" -o collection.json
```

脚本自动通过B站API解析得合集ID和全部视频列表。

### 2. 批量转录

```bash
python3 scripts/transcribe_collection.py collection.json \
    --output ./output \
    --model small \
    --device cuda \
    --progress progress.json
```

- 自动断点续传（每集完成写入 progress.json）
- 自动下载→提取16kHz WAV→Whisper转录
- 输出按 `合集名-序号-标题.md` 命名

### 3. 语义分段

```bash
python3 scripts/semantic_segment.py ./output/*.md
```

基于 Jaccard 词汇连贯性 + 结构信号（指代/逻辑连接词/设问/列举）进行智能分段。

### 4. （可选）LLM后处理

用 DeepSeek / OpenAI 兼容 API 做错别字修正或散文化改写。

## 示例

```bash
# 一次跑完
python3 scripts/fetch_collection.py "https://b23.tv/xxxxx" -o my_list.json
python3 scripts/transcribe_collection.py my_list.json --output ./my_transcripts --progress p.json
python3 scripts/semantic_segment.py ./my_transcripts/*.md
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `scripts/fetch_collection.py` | 解析B站合集，输出视频列表JSON |
| `scripts/transcribe_collection.py` | 批量下载→转录→输出.md |
| `scripts/semantic_segment.py` | 语义分段v2算法 |

## 输出格式

```markdown
# 视频标题

> BVID: BVxxxxxx | 时长: 10分43秒

转录正文...

---

## 段落1
...

## 段落2
...
```

## 注意事项

- **GPU显存**：Whisper small 需要 ~2GB，large-v3 需要 ~6GB
- **CUDA**：确保已安装 CUDA Toolkit 12.x
- **B站412**：如遇 you-get 412 封锁，改换 yt-dlp + cookies-from-browser
- **进度恢复**：中断后重跑同一条命令会自动跳过已完成视频

## 实战战果

- 波士顿圆脸「MAGA东山再起」203集 ✅
- 战争研究所「研究一下」102集 ✅
- 山河有声「战略杂谈」126集 ✅
- MIT 8.02 电磁学 36集 ✅ 英文→中文翻译
- 金砖支付合集 8集 ✅
