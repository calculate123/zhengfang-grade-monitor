#!/usr/bin/env python3
"""
一键配置向导
============
运行本脚本，交互式输入信息后，自动：
  1. Fork 你的模板仓库
  2. 设置 GitHub Secrets（学号、密码、WxPusher Token、UID）
  3. 触发首次运行
  4. 后续每2小时自动检查，无需再做任何操作

使用: python wizard.py
"""

import requests
import getpass
import sys
import re


def print_step(n, text):
    print(f"\n{'='*50}")
    print(f"  第{n}步: {text}")
    print(f"{'='*50}")


def get_input(prompt, secret=False):
    """获取用户输入，支持隐藏密码"""
    if secret:
        return getpass.getpass(f"  {prompt}: ").strip()
    return input(f"  {prompt}: ").strip()


def validate_not_empty(val, name):
    if not val:
        print(f"\n  [错误] {name} 不能为空，请重新运行。")
        sys.exit(1)
    return val


def main():
    print("""
╔══════════════════════════════════════════════════╗
║     正方教务系统成绩监控 — 一键配置向导          ║
║     https://github.com/calculate123/zhengfang-grade-monitor  ║
╚══════════════════════════════════════════════════╝
    """)

    # ====== 第1步: GitHub 仓库 ======
    print_step(1, "GitHub 仓库设置")

    print("""
  首先需要你在 GitHub 上基于模板创建仓库:
  1. 打开 https://github.com/calculate123/zhengfang-grade-monitor
  2. 点击绿色按钮 "Use this template" → "Create a new repository"
  3. Repository name 任意填（如 "grade-monitor"）
  4. 务必选择 Private（私有）！
  5. 点击 "Create repository"
  """)

    input("  完成后按回车继续...")

    gh_user = validate_not_empty(
        get_input("你的 GitHub 用户名（如 calculate123）"),
        "GitHub 用户名"
    )
    repo_name = validate_not_empty(
        get_input("你创建的仓库名称（如 grade-monitor）"),
        "仓库名称"
    )

    # ====== 第2步: GitHub Token ======
    print_step(2, "GitHub 访问令牌")

    print("""
  需要一个 GitHub Token 来自动配置 Secrets:
  1. 打开 https://github.com/settings/tokens
  2. 点击 "Generate new token" → "Generate new token (classic)"
  3. Note 填 "grade-monitor-setup"
  4. Expiration 选 "No expiration"
  5. 勾选 "repo" 和 "workflow" 两个权限
  6. 点击 "Generate token"，复制生成的 token
  """)

    gh_token = validate_not_empty(
        get_input("粘贴你的 GitHub Token（ghp_开头）", secret=True),
        "GitHub Token"
    )

    # ====== 第3步: 教务系统 ======
    print_step(3, "教务系统账号")

    student_id = validate_not_empty(
        get_input("你的学号"),
        "学号"
    )
    password = validate_not_empty(
        get_input("教务系统密码（输入时不显示）", secret=True),
        "密码"
    )

    # ====== 第4步: WxPusher ======
    print_step(4, "WxPusher 推送配置")

    print("""
  WxPusher 用于把成绩变化推送到你手机。需要:
  1. 手机应用商店下载 "WxPusher" App → 微信登录
  2. 打开 https://wxpusher.zjiecode.com/ → 扫码登录
  3. "应用管理" → "新建应用" → 复制 AppToken
  4. 应用详情页 → "关注" → 用 App 扫码订阅
  5. App 中查看 "我的UID"
  """)

    wx_token = validate_not_empty(
        get_input("WxPusher AppToken（AT_开头）"),
        "AppToken"
    )
    wx_uid = validate_not_empty(
        get_input("WxPusher UID（UID_开头）"),
        "UID"
    )

    # ====== 第5步: 执行配置 ======
    print_step(5, "自动配置")

    API = "https://api.github.com"
    HEADERS = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    repo = f"{gh_user}/{repo_name}"

    # 获取 repo public key
    r = requests.get(f"{API}/repos/{repo}/actions/secrets/public-key", headers=HEADERS)
    if r.status_code != 200:
        print(f"\n  [错误] 无法访问仓库 {repo}，请检查用户名/仓库名/Token 是否正确。")
        print(f"  状态码: {r.status_code} 响应: {r.json().get('message', '')}")
        sys.exit(1)

    pk = r.json()
    key_id = pk["key_id"]
    pub_key_b64 = pk["key"]

    # 加密函数
    from nacl import encoding, public
    from base64 import b64encode

    def encrypt(val):
        pk_obj = public.PublicKey(pub_key_b64.encode("utf-8"), encoding.Base64Encoder())
        box = public.SealedBox(pk_obj)
        encrypted = box.encrypt(val.encode("utf-8"))
        return b64encode(encrypted).decode("utf-8")

    secrets = {
        "ZF_USERNAME": student_id,
        "ZF_PASSWORD": password,
        "WXPUSHER_TOKEN": wx_token,
        "WXPUSHER_UID": wx_uid,
    }

    success = 0
    for name, val in secrets.items():
        r = requests.put(
            f"{API}/repos/{repo}/actions/secrets/{name}",
            headers=HEADERS,
            json={"encrypted_value": encrypt(val), "key_id": key_id},
        )
        status = "OK" if r.status_code in (201, 204) else f"失败({r.status_code})"
        if r.status_code in (201, 204):
            success += 1
        print(f"  [{status}] {name}")

    if success != 4:
        print("\n  [错误] Secrets 设置不完整，请检查 Token 权限后重试。")
        sys.exit(1)

    # ====== 第6步: 触发首次运行 ======
    print_step(6, "触发首次检查")

    r = requests.post(
        f"{API}/repos/{repo}/actions/workflows/monitor.yml/dispatches",
        headers=HEADERS,
        json={"ref": "master"},
    )

    if r.status_code == 204:
        print(f"""
  ✓  配置完成！首次检查已触发。

  你现在可以:
  - 打开 https://github.com/{repo}/actions 查看运行状态
  - 等2分钟后检查 WxPusher App 是否收到成绩推送
  - 之后每2小时自动检查，不需要再做任何操作
  - 你的电脑关机、手机没网都不影响

  如果没收到推送，检查:
  1. WxPusher App 中是否扫码订阅了应用
  2. GitHub Actions 是否已启用
  """)
    else:
        print(f"""
  ✓  Secrets 已配置，但首次触发失败。

  请手动触发:
  1. 打开 https://github.com/{repo}/actions
  2. 点击 "成绩监控" → "Run workflow"
  """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消。")
        sys.exit(0)
