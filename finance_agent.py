import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import smtplib
from email.mime.text import MIMEText

print("程序启动时间：", datetime.now())

# ===== AI =====
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="qwen2:7b")


# =========================================================
# 1️⃣ 交易所公告抓取（改进：过滤无效链接）
# =========================================================
def collect_exchange_announcements():
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []

    sources = [
        ("上交所", "http://www.sse.com.cn/disclosure/listedinfo/announcement/"),
        ("深交所", "http://www.szse.cn/disclosure/listed/notice/")
    ]

    for name, url in sources:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            # 只抓看起来像公告标题的链接
            for a in soup.find_all("a"):
                text = a.get_text(strip=True)

                if (
                    len(text) > 12 and
                    "公告" in text and
                    not text.startswith("http")
                ):
                    news.append(f"[公告]{text}")

        except Exception as e:
            print(f"{name} 抓取失败: {e}")

    print(f"交易所公告获取 {len(news)} 条")
    return news


# =========================================================
# 2️⃣ 政策新闻抓取（只保留正文类标题）
# =========================================================
def collect_policy_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []

    policy_sites = [
        ("国务院", "https://www.gov.cn/zhengce/zuixin.htm"),
        ("工信部", "https://www.miit.gov.cn/xwdt/")
    ]

    for name, url in policy_sites:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a"):
                text = a.get_text(strip=True)
                if len(text) > 15 and "解读" not in text:
                    news.append(f"[政策]{text}")

        except Exception as e:
            print(f"{name} 抓取失败: {e}")

    print(f"政策新闻获取 {len(news)} 条")
    return news


# =========================================================
# 3️⃣ 关键词筛选（只对公告）
# =========================================================
def filter_key_announcements(news_list):
    keywords = ["中标", "订单", "签署", "预增", "收购", "合作", "增持"]
    result = []

    for n in news_list:
        if "[公告]" in n and any(k in n for k in keywords):
            result.append(n)

    print(f"关键公告筛选后 {len(result)} 条")
    return result


# =========================================================
# 4️⃣ 题材统计（核心升级点🔥）
# =========================================================
def analyze_themes(news):
    theme_map = {
        "AI": ["人工智能", "算力", "芯片", "大模型"],
        "新能源": ["光伏", "储能", "电池", "新能源"],
        "半导体": ["半导体", "芯片", "封测"],
        "军工": ["军工", "卫星", "导弹"],
        "地产": ["房地产", "地产"],
        "医药": ["医药", "医疗", "创新药"]
    }

    counter = Counter()

    for item in news:
        for theme, words in theme_map.items():
            if any(w in item for w in words):
                counter[theme] += 1

    return counter


# =========================================================
# 5️⃣ AI 分析
# =========================================================
def analyze_with_ai(news, theme_counter):
    theme_text = "\n".join([f"{k}：{v}条" for k, v in theme_counter.items()])

    news_text = "\n".join(news[:30])

    prompt = f"""
你是A股短线交易员。

今日重要新闻：
{news_text}

题材统计：
{theme_text}

请严格按以下格式：

【市场主线判断】

【哪些行业或方向受益】

【是否可能形成短线炒作题材】
1.
2.

【情绪偏机会还是风险】

如果新闻分散，请写：今日无交易主线。
禁止编造指数数据。
"""

    response = llm.invoke(prompt)
    return response.content


# =========================================================
# 6️⃣ 邮件发送
# =========================================================
def send_email(report):
    sender = "18318881324@163.com"
    password = os.getenv("EMAIL_PASS")
    receiver = "18318881324@163.com"

    if not password:
        raise ValueError("未设置 EMAIL_PASS 环境变量")

    msg = MIMEText(report, 'plain', 'utf-8')
    msg['Subject'] = f"📈 AI金融日报 {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = sender
    msg['To'] = receiver

    server = smtplib.SMTP_SSL('smtp.163.com', 465)
    server.login(sender, password)
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()


# =========================================================
# 主程序
# =========================================================
if __name__ == "__main__":
    print("开始收集数据...")

    exchange_news = collect_exchange_announcements()
    policy_news = collect_policy_news()

    key_announcements = filter_key_announcements(exchange_news)

    all_news = key_announcements + policy_news

    if not all_news:
        report = "今日无关键公告或政策主线。"
    else:
        themes = analyze_themes(all_news)
        report = analyze_with_ai(all_news, themes)

    print("发送邮件中...")
    send_email(report)
    print("✅ 完成")
