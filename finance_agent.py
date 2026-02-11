import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
print("程序启动时间：", datetime.now())

# ===== AI 部分 =====
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="qwen2:7b")

# ===== 新闻源 =====
rss_sources = {
    "中国金融": "https://rsshub.app/eastmoney/news",
    "国际金融": "https://feeds.reuters.com/reuters/businessNews",
    "中国股市": "https://rsshub.app/sina/finance",
    "国际股市": "https://feeds.reuters.com/reuters/marketsNews"
}

def get_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text[:3000]
    except:
        return ""

def collect_news():
    news_data = ""
    for category, url in rss_sources.items():
        feed = feedparser.parse(url)
        news_data += f"\n\n【{category}】\n"
        for entry in feed.entries[:5]:
            news_data += f"\n标题: {entry.title}\n"
            if hasattr(entry, "link"):
                content = get_article_text(entry.link)
                news_data += f"内容摘要: {content[:500]}\n"
    return news_data

def analyze_news(news_text):
    prompt = f"""
你是专业金融分析师，请基于以下新闻生成每日金融报告：

{news_text}

请输出：
1. 今日全球市场总体趋势
2. 中国股市影响
3. 国际市场影响
4. 重要风险提示
5. 投资者需要关注的要点
"""
    response = llm.invoke(prompt)
    return response.content

def send_email(report):
    sender = "18318881324@163.com"
    password = os.getenv("EMAIL_PASS")
    print("环境变量 EMAIL_PASS =", password)
    receiver = "18318881324@163.com"

    msg = MIMEText(report, 'plain', 'utf-8')
    msg['Subject'] = f"📈 AI金融日报 {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = sender
    msg['To'] = receiver

    server = smtplib.SMTP_SSL('smtp.163.com', 465)
    server.login(sender, password)
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()

if __name__ == "__main__":
    print("📰 收集新闻中...")
    news = collect_news()

    print("🧠 AI 分析中...")
    report = analyze_news(news)

    print("📧 发送报告...")
try:
    send_email(report)
    print("邮件发送成功")
except Exception as e:
    print("邮件发送失败：", e)


    print("✅ 今日金融报告已发送！")

