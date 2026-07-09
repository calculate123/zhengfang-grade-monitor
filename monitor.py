#!/usr/bin/env python3
"""正方教务成绩自动监控 - GitHub Actions版 (Linux/Chrome)"""
import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
import urllib3

urllib3.disable_warnings()

# 从环境变量读取配置（敏感信息存入GitHub Secrets）
CONFIG = {
    "base_url": os.environ.get("ZF_BASE_URL", "https://jwglxt.haut.edu.cn/jwglxt"),
    "username": os.environ["ZF_USERNAME"],
    "password": os.environ["ZF_PASSWORD"],
    "wxpusher_token": os.environ["WXPUSHER_TOKEN"],
    "wxpusher_uid": os.environ["WXPUSHER_UID"],
}

GRADES_FILE = "grades_history.json"
LAST_CHECK_FILE = "last_check.txt"
CHECK_INTERVAL = 2  # 小时


def notify(title, content):
    """WxPusher推送"""
    try:
        r = requests.post(
            "https://wxpusher.zjiecode.com/api/send/message",
            json={
                "appToken": CONFIG["wxpusher_token"],
                "content": f"## {title}\n\n{content}",
                "summary": title[:100],
                "contentType": 3,
                "uids": [CONFIG["wxpusher_uid"]],
            },
            timeout=30,
        )
        result = r.json()
        if result.get("code") == 1000:
            print("[通知] 推送成功")
            return True
        print(f"[通知] 失败: {result.get('msg')}")
    except Exception as e:
        print(f"[通知] 异常: {e}")
    return False


def setup_driver():
    """配置Chrome headless (GitHub Actions Ubuntu环境)"""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    # 优先使用系统chromedriver，否则尝试默认路径
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=opts)
    except Exception:
        driver = webdriver.Chrome(options=opts)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def login(driver):
    driver.get(f"{CONFIG['base_url']}/xtgl/login_slogin.html")
    time.sleep(3)
    driver.find_element(By.ID, "yhm").send_keys(CONFIG["username"])
    driver.find_element(By.ID, "mm").send_keys(CONFIG["password"])
    driver.find_element(By.ID, "dl").click()
    time.sleep(3)
    return "index_initMenu" in driver.current_url


def get_grades(driver):
    result = driver.execute_script("""
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/jwglxt/cjcx/cjcx_cxDgXscj.html?doType=query&gnmkdm=N305005', false);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8');
        xhr.send('xnm=&xqm=&_search=false&nd=' + Date.now() +
            '&queryModel.showCount=100&queryModel.currentPage=1' +
            '&queryModel.sortName=&queryModel.sortOrder=asc&time=0');
        try { return JSON.parse(xhr.responseText); } catch(e) { return null; }
    """)
    if result and "items" in result:
        return [
            {
                "kcmc": str(i.get("kcmc", "")),
                "kcdm": str(i.get("kcdm", "")),
                "kch": str(i.get("kch", "")),
                "cj": str(i.get("cj", "")),
                "xf": str(i.get("xf", "")),
                "xnmmc": str(i.get("xnmmc", "")),
                "xqmmc": str(i.get("xqmmc", "")),
            }
            for i in result["items"]
        ]
    return []


def load_history():
    try:
        with open(GRADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history(grades_dict):
    with open(GRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(grades_dict, f, ensure_ascii=False, indent=2)


def grades_to_dict(grades):
    return {g.get("kcdm") or g.get("kch", ""): g for g in grades if g.get("kcdm") or g.get("kch")}


def compare(old_list, new_list):
    changes = {"new": [], "updated": [], "deleted": []}
    old = grades_to_dict(old_list)
    new = grades_to_dict(new_list)
    for code, ng in new.items():
        if code not in old:
            changes["new"].append(ng)
        elif old[code]["cj"] != ng["cj"]:
            changes["updated"].append({"old": old[code], "new": ng})
    for code in old:
        if code not in new:
            changes["deleted"].append(old[code])
    return changes


def format_msg(changes):
    msg = "**成绩更新通知**\n\n"
    msg += f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    if changes["new"]:
        msg += "🆕 **新增成绩**\n"
        for g in changes["new"]:
            msg += f"- {g['kcmc']}: {g['cj']}分 ({g['xf']}学分)\n"
        msg += "\n"
    if changes["updated"]:
        msg += "🔄 **成绩更新**\n"
        for c in changes["updated"]:
            msg += f"- {c['new']['kcmc']}: {c['old']['cj']} → {c['new']['cj']}\n"
        msg += "\n"
    if changes["deleted"]:
        msg += "❌ **已删除**\n"
        for g in changes["deleted"]:
            msg += f"- {g['kcmc']}\n"
        msg += "\n"
    return msg


def should_check():
    """距上次检查超过2小时才执行"""
    try:
        with open(LAST_CHECK_FILE, "r") as f:
            last = datetime.fromisoformat(f.read().strip())
        elapsed = (datetime.now() - last).total_seconds() / 3600
        if elapsed < CHECK_INTERVAL:
            print(f"[跳过] 距上次检查仅 {elapsed:.1f} 小时 < {CHECK_INTERVAL}h")
            return False
    except (FileNotFoundError, ValueError):
        pass
    return True


def update_last_check():
    with open(LAST_CHECK_FILE, "w") as f:
        f.write(datetime.now().isoformat())


def main():
    print(f"[{datetime.now()}] 开始检查...")

    if not should_check():
        return  # 跳过，更新last_check文件方便下次判断

    driver = setup_driver()

    try:
        if not login(driver):
            notify("⚠ 成绩查询失败", "登录失败，请检查账号密码")
            return

        grades = get_grades(driver)
        if not grades:
            notify("⚠ 成绩查询失败", "未获取到成绩数据")
            return

        print(f"查询到 {len(grades)} 条成绩")
        old = load_history()
        new_dict = grades_to_dict(grades)

        if not old:
            save_history(new_dict)
            update_last_check()
            lines = "\n".join([f"- {g['kcmc']}: {g['cj']}分" for g in grades])
            notify("📚 成绩监控已启动", f"共 {len(grades)} 条:\n\n{lines}")
            print("首次运行，已保存")
            return

        changes = compare(list(old.values()), grades)
        has = bool(changes["new"] or changes["updated"] or changes["deleted"])

        if has:
            notify("📚 成绩有更新！", format_msg(changes))
            print("有变化!")
        else:
            notify("成绩查询", "1")
            print("无变化")

        save_history(new_dict)
        update_last_check()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
