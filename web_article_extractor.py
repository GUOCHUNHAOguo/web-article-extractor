#!/usr/bin/env python3
"""
网页文章提取器
输入URL，基于关键词筛选标题和摘要，进入详情页提取信息
"""

import requests
from bs4 import BeautifulSoup
import html2text
import json
import re
from urllib.parse import urljoin, urlparse
import time
import sys

# 配置
LLM_API_URL = "http://10.12.16.203:3000/v1/completions"
LLM_MODEL = "zenmux/glm-4.7"
LLM_TOKEN = "b99Jl5rtmuYa5hPe5WioOKj2iP4uF6m657Tyn9v5814NLtM6"


def fetch_html(url, timeout=30):
    """获取网页 HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def html_to_markdown(html):
    """HTML 转为 Markdown"""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    return h.handle(html)


def extract_articles(html, keywords, base_url="https://www.vrtuoluo.cn"):
    """从 HTML 提取文章列表（标题、URL、摘要）"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # 查找所有链接
    all_links = soup.find_all('a', href=True)
    
    for link_elem in all_links[:150]:
        try:
            href = link_elem.get('href', '')
            
            # 只处理文章链接
            if not href or href.startswith('#') or 'javascript' in href.lower():
                continue
            
            # 检查是否是文章链接（包含数字ID）
            if re.search(r'/\d+\.html', href):
                # 拼接完整 URL
                full_url = urljoin(base_url, href)
                
                # 获取标题 - 链接文本
                title = link_elem.get_text(strip=True)
                
                # 如果链接文本太短，尝试从父元素获取
                if not title or len(title) < 10:
                    parent = link_elem.find_parent(['div', 'li', 'article'])
                    if parent:
                        title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'span', 'p'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # 获取摘要 - 从父元素找段落
                summary = ""
                parent = link_elem.find_parent(['div', 'li', 'article'])
                if parent:
                    p_elem = parent.find('p')
                    if p_elem:
                        summary = p_elem.get_text(strip=True)[:200]
                
                # 检查关键词匹配
                text_lower = (title + " " + summary).lower()
                if keywords == [""] or any(kw.lower() in text_lower for kw in keywords):
                    articles.append({
                        'title': title,
                        'url': full_url,
                        'summary': summary
                    })
        except Exception:
            continue
    
    # 去重
    seen = set()
    unique_articles = []
    for art in articles:
        if art['url'] not in seen:
            seen.add(art['url'])
            unique_articles.append(art)
    
    return unique_articles


def extract_article_detail(url):
    """提取文章详情页"""
    html = fetch_html(url)
    if not html:
        return None
    
    # 转为 Markdown
    markdown = html_to_markdown(html)
    
    # 用 LLM 提取关键信息
    prompt = f"""从以下文章内容中提取关键信息，以 JSON 格式返回：
{{
    "title": "文章标题",
    "author": "作者",
    "date": "发布日期",
    "content_summary": "内容摘要（200字以内）",
    "key_points": ["关键点1", "关键点2", "关键点3"],
    "tags": ["标签1", "标签2"]
}}

文章内容：
{markdown[:5000]}
"""

    try:
        response = requests.post(
            f"{LLM_API_URL}",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.3
            },
            headers={"Authorization": f"Bearer {LLM_TOKEN}"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'url': url,
                'llm_extracted': result.get('choices', [{}])[0].get('text', ''),
                'raw_markdown': markdown[:3000]
            }
    except Exception as e:
        print(f"  ⚠️ LLM extraction failed: {e}")
    
    return {
        'url': url,
        'raw_markdown': markdown[:3000]
    }


def summarize_with_llm(articles):
    """用 LLM 总结所有文章"""
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    
    prompt = f"""根据以下文章列表，生成一个结构化的总结报告：

{articles_json}

请按以下格式组织：
## 文章概览
- 共找到 X 篇文章

## 分类整理
按主题或关键词分组，列出每篇文章的标题和核心要点

## 重点推荐
选出 3-5 篇最有价值的文章，说明推荐理由
"""

    try:
        response = requests.post(
            f"{LLM_API_URL}",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "max_tokens": 2000,
                "temperature": 0.5
            },
            headers={"Authorization": f"Bearer {LLM_TOKEN}"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('choices', [{}])[0].get('text', '')
    except Exception as e:
        print(f"  ⚠️ Summary generation failed: {e}")
    
    return None


def main():
    """主函数"""
    print("Web Article Extractor")
    print("=" * 50)
    
    # 输入
    url = input("Enter URL: ").strip()
    if not url:
        print("URL cannot be empty")
        return
    
    keywords_input = input("Keywords (comma-separated): ").strip()
    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    if not keywords:
        keywords = [""]
    
    output_file = input("Output filename (default: articles.json): ").strip() or "articles.json"
    
    print(f"\nFetching: {url}")
    print(f"Keywords: {keywords}")
    
    # 获取网页
    html = fetch_html(url)
    if not html:
        print("Failed to fetch webpage")
        return
    
    print(f"Success! HTML size: {len(html)} chars")
    
    # 提取文章
    print("\nExtracting articles...")
    articles = extract_articles(html, keywords)
    print(f"Found {len(articles)} articles")
    
    # 提取详情
    print("\nExtracting details...")
    for i, art in enumerate(articles[:10], 1):
        print(f"  [{i}/{len(articles[:10])}] {art['title'][:40]}...")
        detail = extract_article_detail(art['url'])
        if detail:
            art['detail'] = detail
        time.sleep(0.3)
    
    # 保存结果
    result = {
        'source_url': url,
        'keywords': keywords,
        'articles': articles,
        'total': len(articles)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved to: {output_file}")
    
    # LLM 总结
    print("\nGenerating AI summary...")
    summary = summarize_with_llm(articles)
    if summary:
        summary_file = output_file.replace('.json', '_summary.md')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Summary saved to: {summary_file}")
        print("\n" + "=" * 50)
        print(summary)


if __name__ == "__main__":
    main()
