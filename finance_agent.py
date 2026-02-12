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

def collect_news():
    """收集交易所公告（上交所+深交所）"""
    headers = {"User-Agent": "Mozilla/5.0"}
    news_list = []
    
    # 上交所公告
    try:
        url = "http://www.sse.com.cn/disclosure/listedinfo/announcement/"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("a")[:20]
        
        for i in items:
            text = i.get_text(strip=True)
            if len(text) > 10:
                news_list.append(text)
    except Exception as e:
        print(f"上交所公告获取失败: {e}")
    
    # 深交所公告
    try:
        url = "http://www.szse.cn/disclosure/listed/notice/"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("a")[:20]
        
        for i in items:
            text = i.get_text(strip=True)
            if len(text) > 10:
                news_list.append(text)
    except Exception as e:
        print(f"深交所公告获取失败: {e}")
    
    # 去重并限制数量
    news_list = list(set(news_list))[:30]
    print(f"收集到交易所公告 {len(news_list)} 条")
    return news_list

def collect_policy_news():
    """抓取政策新闻（国务院+工信部）"""
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []
    
    # 国务院政策
    try:
        url = "https://www.gov.cn/zhengce/zuixin.htm"
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("a")[:15]
        
        for i in items:
            t = i.text.strip()
            if len(t) > 10:
                news.append("[政策] " + t)
    except Exception as e:
        print(f"国务院政策获取失败: {e}")
    
    # 工信部
    try:
        url = "https://www.miit.gov.cn/xwdt/"
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("a")[:15]
        
        for i in items:
            t = i.text.strip()
            if len(t) > 10:
                news.append("[政策] " + t)
    except Exception as e:
        print(f"工信部新闻获取失败: {e}")
    
    print(f"收集到政策新闻 {len(news)} 条")
    return news

def filter_key_announcements(news_list):
    """筛选包含关键词的公告"""
    keywords = ["中标", "订单", "签署", "预增", "收购", "合作", "增持"]
    result = []
    
    for n in news_list:
        if any(k in n for k in keywords):
            result.append("[公告] " + n)
    
    print(f"筛选后保留关键公告 {len(result)} 条")
    return result

def analyze_news(news_text):
    prompt = f"""
你是A股短线交易员。

今日财经快讯：
{news_text}

严格按以下格式输出：

【政策 + 公司公告 + 重大事件】倾向总结

【哪些行业或方向受益】

【是否有资金可能炒作的题材】
1. 
2. 

【情绪是偏机会还是利空】

要求：
- 是否有在资金可能炒作的题材
- 哪些行业或方向受益  
- 情绪是偏机会还是利空
- 若无有效交易主线，请明确输出：今日无交易主线

禁止编造指数、涨跌幅、成交额。
没有数据就写"未提供具体数据"。
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
    news1 = collect_news()  # 交易所公告
    news2 = collect_policy_news()  # 政策新闻
    
    # 合并并筛选关键公告
    all_news = news1 + news2
    all_news = filter_key_announcements(all_news)
    news = "\n".join(all_news)

    print("🧠 AI 分析中...")
    report = analyze_news(news)

    print("📧 发送报告...")
    try:
        send_email(report)
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败：", e)

    print("✅ 今日金融报告已发送！")