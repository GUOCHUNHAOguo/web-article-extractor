# 网页文章提取器

基于关键词从网页中提取文章标题、URL 和摘要，并使用 LLM 提取详细信息。

## 功能特性

- 🔍 **网页抓取** - 获取任意网页的 HTML 内容
- 📰 **文章筛选** - 基于关键词过滤文章列表
- 📝 **内容提取** - 访问每篇文章详情页提取正文
- 🔄 **HTML 转 Markdown** - 将网页内容转换为 Markdown 格式
- 🤖 **LLM 智能整理** - 调用大模型提取关键信息并生成总结
- 💾 **JSON 输出** - 结构化保存结果

## 环境要求

- Python 3.9+
- 依赖包（见 `requirements_extractor.txt`）

## 安装

```bash
pip install -r requirements_extractor.txt
```

## 配置

在 `web_article_extractor.py` 中配置 LLM API：

```python
LLM_API_URL = "http://your-llm-api:3000/v1/completions"
LLM_MODEL = "your-model-name"
LLM_TOKEN = "your-api-token"
```

## 使用方法

```bash
python web_article_extractor.py
```

按提示输入：
1. 网页 URL
2. 关键词（多个用逗号分隔）
3. 输出文件名

## 输出示例

```json
{
  "source_url": "https://example.com",
  "keywords": ["AI", "科技"],
  "articles": [
    {
      "title": "文章标题",
      "url": "https://example.com/article.html",
      "summary": "文章摘要...",
      "detail": {
        "llm_extracted": "LLM提取的关键信息...",
        "raw_markdown": "Markdown格式的内容..."
      }
    }
  ],
  "total": 10
}
```

## 工作流程

```
输入URL → 获取HTML → 解析文章列表 → 关键词匹配
                                      ↓
                               遍历每篇文章详情
                                      ↓
                               HTML→Markdown → LLM提取 → JSON
```

## 依赖包

- `requests` - HTTP 请求
- `beautifulsoup4` - HTML 解析
- `html2text` - HTML 转 Markdown
- `lxml` - XML/HTML 解析器

## License

MIT
