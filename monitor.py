#!/usr/bin/env python3
"""
正方教务系统成绩自动监控 v2.0
================================
每2小时自动查询成绩，有变化时通过 WxPusher 推送通知到手机。
运行在 GitHub Actions 上，无需服务器，无需电脑开机，完全免费。

适配学校: 河南工业大学 (HAUT)
适用系统: 正方教务管理系统 (jwglxt)

GitHub: https://github.com/calculate123/zhengfang-grade-monitor
"""

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

# ---- 配置 (敏感信息通过 GitHub Secrets 注入) ----
CONFIG = {
    "base_url": os.environ.get("ZF_BASE_URL", "https://jwglxt.haut.edu.cn/jwglxt"),
    "username": os.environ["ZF_USERNAME"],
    "password": os.environ["ZF_PASSWORD"],
    "wxpusher_token": os.environ["WXPUSHER_TOKEN"],
    "wxpusher_uid": os.environ["WXPUSHER_UID"],
}

GRADES_FILE = "grades_history.json"
LAST_CHECK_FILE = "last_check.txt"
CHECK_INTERVAL = 2       # 实际查询间隔（小时）
LOGIN_RETRIES = 3        # 登录重试次数


# ============================================================
#  通知推送
# ============================================================

def notify(title, content):
    """通过 WxPusher 发送通知到手机"""
    try:
        r = requests.post(
            "https://wxpusher.zjiecode.com/api/send/message",
            json={
                "appToken": CONFIG["wxpusher_token"],
                "content": f"## {title}\n\n{content}",
                "summary": title[:100],
                "contentType": 3,  # Markdown 格式
                "uids": [CONFIG["wxpusher_uid"]],
            },
            timeout=30,
        )
        if r.json().get("code") == 1000:
            print("[通知] 推送成功")
            return True
        print(f"[通知] 推送失败: {r.json().get('msg')}")
    except Exception as e:
        print(f"[通知] 网络异常: {e}")
    return False


# ============================================================
#  浏览器自动化
# ============================================================

def setup_driver():
    """启动 Chrome headless 浏览器"""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

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
    """登录教务系统，支持重试"""
    login_url = f"{CONFIG['base_url']}/xtgl/login_slogin.html"

    for attempt in range(1, LOGIN_RETRIES + 1):
        print(f"[登录] 第 {attempt}/{LOGIN_RETRIES} 次尝试...")
        driver.get(login_url)
        time.sleep(3)

        driver.find_element(By.ID, "yhm").send_keys(CONFIG["username"])
        driver.find_element(By.ID, "mm").send_keys(CONFIG["password"])

        # 有些学校的正方系统有验证码，这里是兼容处理
        try:
            yzm = driver.find_element(By.ID, "yzm")
            print("[登录] 检测到验证码，本脚本暂不支持自动识别，请检查学校是否开启了验证码")
            return False
        except Exception:
            pass

        driver.find_element(By.ID, "dl").click()
        time.sleep(3)

        if "index_initMenu" in driver.current_url:
            print("[登录] 登录成功")
            return True

        print(f"[登录] 失败，{'重试中...' if attempt < LOGIN_RETRIES else '已达最大重试次数'}")

    return False


# ============================================================
#  成绩查询与解析
# ============================================================

def get_grades(driver):
    """通过 AJAX 接口获取成绩列表"""
    result = driver.execute_script("""
        var xhr = new XMLHttpRequest();
        xhr.open('POST',
            '/jwglxt/cjcx/cjcx_cxDgXscj.html?doType=query&gnmkdm=N305005',
            false);
        xhr.setRequestHeader('Content-Type',
            'application/x-www-form-urlencoded;charset=UTF-8');
        xhr.send('xnm=&xqm=&_search=false&nd=' + Date.now() +
            '&queryModel.showCount=100&queryModel.currentPage=1' +
            '&queryModel.sortName=&queryModel.sortOrder=asc&time=0');
        try { return JSON.parse(xhr.responseText); }
        catch(e) { return null; }
    """)

    if not result or "items" not in result:
        return []

    return [
        {
            "kcmc":   str(i.get("kcmc", "")),   # 课程名称
            "kcdm":   str(i.get("kcdm", "")),   # 课程代码
            "kch":    str(i.get("kch", "")),     # 课程号
            "cj":     str(i.get("cj", "")),      # 成绩
            "xf":     str(i.get("xf", "")),      # 学分
            "xnmmc":  str(i.get("xnmmc", "")),   # 学年
            "xqmmc":  str(i.get("xqmmc", "")),   # 学期
        }
        for i in result["items"]
    ]


# ============================================================
#  成绩对比与持久化
# ============================================================

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
    """将成绩列表转为 {课程代码: 成绩项} 的字典"""
    return {
        g.get("kcdm") or g.get("kch", ""): g
        for g in grades
        if g.get("kcdm") or g.get("kch")
    }


def compare(old_list, new_list):
    """对比新旧成绩，返回新增/更新/删除"""
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
    """格式化成绩变化通知"""
    msg = "**成绩更新通知**\n\n"
    msg += f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    if changes["new"]:
        msg += "**新增成绩**\n\n"
        for g in changes["new"]:
            msg += f"- {g['kcmc']}: {g['cj']}分 ({g['xf']}学分)\n"
        msg += "\n"

    if changes["updated"]:
        msg += "**成绩更新**\n\n"
        for c in changes["updated"]:
            name = c["new"]["kcmc"]
            msg += f"- {name}: {c['old']['cj']} → **{c['new']['cj']}**\n"
        msg += "\n"

    if changes["deleted"]:
        msg += "**已删除**\n\n"
        for g in changes["deleted"]:
            msg += f"- {g['kcmc']}\n"
        msg += "\n"

    msg += "---\n*由 GitHub Actions 自动发送*"
    return msg


# ============================================================
#  定时间隔控制
# ============================================================

def should_check():
    """距上次检查超过设定间隔才执行，避免重复查询"""
    try:
        with open(LAST_CHECK_FILE, "r") as f:
            last = datetime.fromisoformat(f.read().strip())
        elapsed = (datetime.now() - last).total_seconds() / 3600
        if elapsed < CHECK_INTERVAL:
            print(f"[跳过] 距上次检查仅 {elapsed:.1f}h，未到 {CHECK_INTERVAL}h 间隔")
            return False
    except (FileNotFoundError, ValueError):
        pass
    return True


def update_last_check():
    with open(LAST_CHECK_FILE, "w") as f:
        f.write(datetime.now().isoformat())


# ============================================================
#  主流程
# ============================================================

def main():
    print(f"\n{'='*40}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 成绩监控 v2.0")

    if not should_check():
        return

    driver = setup_driver()
    try:
        # 1. 登录
        if not login(driver):
            notify("成绩查询失败", "教务系统登录失败，请检查账号密码是否正确。")
            return

        # 2. 查询
        grades = get_grades(driver)
        if not grades:
            notify("成绩查询失败", "登录成功但未获取到成绩数据，可能教务系统暂时异常。")
            return

        print(f"查询到 {len(grades)} 条成绩")

        # 3. 对比
        old = load_history()
        new_dict = grades_to_dict(grades)

        if not old:
            save_history(new_dict)
            update_last_check()
            lines = "\n".join(
                f"- {g['kcmc']}: {g['cj']}分 ({g['xf']}学分 {g['xnmmc']}{g['xqmmc']})"
                for g in grades
            )
            notify("成绩监控已启动", f"共 {len(grades)} 条成绩:\n\n{lines}")
            print("首次运行，已保存成绩快照")
            return

        # 4. 通知
        changes = compare(list(old.values()), grades)
        has_change = bool(changes["new"] or changes["updated"] or changes["deleted"])

        if has_change:
            notify("成绩有更新！", format_msg(changes))
            print(f"检测到变化: 新增 {len(changes['new'])}, 更新 {len(changes['updated'])}, 删除 {len(changes['deleted'])}")
        else:
            notify("成绩查询", "1")
            print("成绩无变化")

        save_history(new_dict)
        update_last_check()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
