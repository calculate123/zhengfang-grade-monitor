#!/usr/bin/env python3
"""
正方教务成绩监控 - 桌面客户端
打包: pyinstaller --onefile --windowed --name "成绩监控" app.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import json
import base64
import webbrowser
from io import BytesIO
from nacl import encoding, public


class GradeMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("正方教务成绩监控 v2.0")
        self.root.geometry("520x660")
        self.root.resizable(False, False)

        # 样式
        self.bg = "#f5f5f5"
        self.accent = "#1890ff"
        self.root.configure(bg=self.bg)

        self.build_ui()

    def build_ui(self):
        # 标题
        title = tk.Label(
            self.root,
            text="正方教务系统成绩监控",
            font=("Microsoft YaHei", 18, "bold"),
            bg=self.bg,
            fg="#333",
        )
        title.pack(pady=(20, 5))

        subtitle = tk.Label(
            self.root,
            text="每2小时自动查成绩，变化推送到手机",
            font=("Microsoft YaHei", 10),
            bg=self.bg,
            fg="#888",
        )
        subtitle.pack(pady=(0, 15))

        # ---- 教务系统 ----
        self.make_section("教务系统账号")

        f1 = tk.Frame(self.root, bg=self.bg)
        f1.pack(fill="x", padx=40)

        tk.Label(f1, text="学号", bg=self.bg, font=("Microsoft YaHei", 10)).grid(
            row=0, column=0, sticky="w", pady=3
        )
        self.student_id = tk.Entry(f1, font=("Microsoft YaHei", 10), width=40)
        self.student_id.grid(row=0, column=1, pady=3, padx=(10, 0))

        tk.Label(f1, text="密码", bg=self.bg, font=("Microsoft YaHei", 10)).grid(
            row=1, column=0, sticky="w", pady=3
        )
        self.password = tk.Entry(f1, font=("Microsoft YaHei", 10), width=40, show="*")
        self.password.grid(row=1, column=1, pady=3, padx=(10, 0))

        # ---- WxPusher ----
        self.make_section("WxPusher 推送设置")
        f2 = tk.Frame(self.root, bg=self.bg)
        f2.pack(fill="x", padx=40)

        tk.Label(
            f2,
            text="1. 手机应用商店搜索 WxPusher 下载并登录\n2. 打开 wxpusher.zjiecode.com 扫码登录\n3. 新建应用 -> 复制 AppToken\n4. 应用详情点\"关注\"用App扫码订阅\n5. App内查看\"我的UID\"",
            bg="#fff",
            font=("Microsoft YaHei", 9),
            fg="#666",
            justify="left",
            relief="solid",
            bd=1,
            padx=10,
            pady=8,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        tk.Label(f2, text="AppToken", bg=self.bg, font=("Microsoft YaHei", 10)).grid(
            row=1, column=0, sticky="w", pady=3
        )
        self.wx_token = tk.Entry(f2, font=("Microsoft YaHei", 10), width=40)
        self.wx_token.grid(row=1, column=1, pady=3, padx=(10, 0))

        tk.Label(f2, text="UID", bg=self.bg, font=("Microsoft YaHei", 10)).grid(
            row=2, column=0, sticky="w", pady=3
        )
        self.wx_uid = tk.Entry(f2, font=("Microsoft YaHei", 10), width=40)
        self.wx_uid.grid(row=2, column=1, pady=3, padx=(10, 0))

        # ---- GitHub ----
        self.make_section("GitHub 访问令牌")
        f3 = tk.Frame(self.root, bg=self.bg)
        f3.pack(fill="x", padx=40)

        gh_btn = tk.Button(
            f3,
            text="点击获取 GitHub Token",
            command=lambda: webbrowser.open("https://github.com/settings/tokens/new?scopes=repo,workflow&description=grade-monitor"),
            bg="#24292e",
            fg="white",
            font=("Microsoft YaHei", 9),
            cursor="hand2",
            padx=10,
        )
        gh_btn.pack(anchor="w", pady=(0, 5))

        tk.Label(
            f3,
            text="1. 点上面按钮打开GitHub  2. Expiration选 No expiration\n3. 点 Generate token  4. 复制生成的 token (ghp_开头)",
            bg="#fff",
            font=("Microsoft YaHei", 9),
            fg="#666",
            relief="solid",
            bd=1,
            padx=10,
            pady=8,
        ).pack(fill="x", pady=(0, 8))

        self.gh_token = tk.Entry(f3, font=("Microsoft YaHei", 10), width=40)
        self.gh_token.pack(fill="x")

        # ---- 启动按钮 ----
        self.btn = tk.Button(
            self.root,
            text="一键配置并启动",
            command=self.start_setup,
            bg=self.accent,
            fg="white",
            font=("Microsoft YaHei", 13, "bold"),
            cursor="hand2",
            padx=30,
            pady=8,
            relief="flat",
        )
        self.btn.pack(pady=(20, 5))

        self.status = tk.Label(
            self.root,
            text="",
            font=("Microsoft YaHei", 10),
            bg=self.bg,
            fg="#666",
        )
        self.status.pack()

        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate", length=300
        )

    def make_section(self, text):
        """创建章节标题"""
        f = tk.Frame(self.root, bg=self.bg)
        f.pack(fill="x", padx=20, pady=(15, 5))
        tk.Label(
            f, text=text, font=("Microsoft YaHei", 12, "bold"), bg=self.bg, fg="#333"
        ).pack(anchor="w")

    def set_status(self, text, color="#666"):
        self.status.config(text=text, fg=color)
        self.root.update()

    def start_setup(self):
        # 验证输入
        sid = self.student_id.get().strip()
        pwd = self.password.get().strip()
        wt = self.wx_token.get().strip()
        wu = self.wx_uid.get().strip()
        gt = self.gh_token.get().strip()

        if not all([sid, pwd, wt, wu, gt]):
            messagebox.showerror("错误", "请填写所有字段")
            return

        if not wt.startswith("AT_"):
            messagebox.showerror("错误", "WxPusher AppToken 应以 AT_ 开头")
            return
        if not wu.startswith("UID_"):
            messagebox.showerror("错误", "WxPusher UID 应以 UID_ 开头")
            return
        if not gt.startswith("ghp_"):
            messagebox.showerror("错误", "GitHub Token 应以 ghp_ 开头")
            return

        self.btn.config(state="disabled", text="配置中...")
        self.progress.pack(pady=(5, 0))
        self.progress.start()

        threading.Thread(
            target=self.do_setup,
            args=(sid, pwd, wt, wu, gt),
            daemon=True,
        ).start()

    def do_setup(self, sid, pwd, wt, wu, gt):
        API = "https://api.github.com"
        HEADERS = {
            "Authorization": f"token {gt}",
            "Accept": "application/vnd.github+json",
        }

        try:
            # 1. 获取 GitHub 用户名
            self.set_status("获取 GitHub 账号信息...")
            r = requests.get(f"{API}/user", headers=HEADERS, timeout=15)
            if r.status_code != 200:
                self.show_error("GitHub Token 无效，请重新获取")
                return
            gh_user = r.json()["login"]
            repo_name = "grade-monitor"

            # 2. 创建私有仓库
            self.set_status("创建私有仓库...")
            r = requests.post(
                f"{API}/user/repos",
                headers=HEADERS,
                json={
                    "name": repo_name,
                    "private": True,
                    "description": "正方教务系统成绩自动监控",
                },
                timeout=15,
            )
            if r.status_code == 422:
                self.set_status("仓库已存在，使用已有仓库")
            elif r.status_code != 201:
                self.show_error(f"创建仓库失败: {r.json().get('message','')}")
                return

            repo = f"{gh_user}/{repo_name}"

            # 3. 上传必要文件
            self.set_status("上传配置文件...")
            files_to_upload = {
                "monitor.py": self.read_resource("monitor.py"),
                "requirements.txt": self.read_resource("requirements.txt"),
                ".github/workflows/monitor.yml": self.read_resource("workflow.yml"),
            }

            for fname, content in files_to_upload.items():
                if not content:
                    continue
                r = requests.put(
                    f"{API}/repos/{repo}/contents/{fname}",
                    headers=HEADERS,
                    json={
                        "message": f"Add {fname}",
                        "content": base64.b64encode(content.encode()).decode(),
                    },
                    timeout=15,
                )
                if r.status_code not in (201, 200):
                    # 文件可能已存在，尝试更新
                    r2 = requests.get(
                        f"{API}/repos/{repo}/contents/{fname}", headers=HEADERS
                    )
                    sha = r2.json().get("sha") if r2.status_code == 200 else None
                    if sha:
                        r = requests.put(
                            f"{API}/repos/{repo}/contents/{fname}",
                            headers=HEADERS,
                            json={
                                "message": f"Update {fname}",
                                "content": base64.b64encode(content.encode()).decode(),
                                "sha": sha,
                            },
                            timeout=15,
                        )

            # 4. 设置 Secrets
            self.set_status("加密存储凭证...")
            r = requests.get(
                f"{API}/repos/{repo}/actions/secrets/public-key", headers=HEADERS
            )
            if r.status_code != 200:
                self.show_error("无法访问仓库 Actions，请检查Token权限")
                return

            pk = r.json()
            key_id = pk["key_id"]
            pk_obj = public.PublicKey(
                pk["key"].encode("utf-8"), encoding.Base64Encoder()
            )

            def encrypt(val):
                box = public.SealedBox(pk_obj)
                return base64.b64encode(box.encrypt(val.encode("utf-8"))).decode(
                    "utf-8"
                )

            secrets = {
                "ZF_USERNAME": sid,
                "ZF_PASSWORD": pwd,
                "WXPUSHER_TOKEN": wt,
                "WXPUSHER_UID": wu,
            }

            for name, val in secrets.items():
                self.set_status(f"配置 {name}...")
                requests.put(
                    f"{API}/repos/{repo}/actions/secrets/{name}",
                    headers=HEADERS,
                    json={"encrypted_value": encrypt(val), "key_id": key_id},
                    timeout=15,
                )

            # 5. 触发首次运行
            self.set_status("触发首次成绩检查...")
            r = requests.post(
                f"{API}/repos/{repo}/actions/workflows/monitor.yml/dispatches",
                headers=HEADERS,
                json={"ref": "master"},
                timeout=15,
            )

            # 完成
            self.root.after(0, self.show_success, gh_user, repo_name)

        except requests.exceptions.ConnectionError:
            self.show_error("网络连接失败，请检查网络")
        except Exception as e:
            self.show_error(f"配置失败: {str(e)}")

    def read_resource(self, name):
        """读取资源文件内容"""
        try:
            # 打包后从临时目录读取
            import sys, os

            base = (
                sys._MEIPASS
                if hasattr(sys, "_MEIPASS")
                else os.path.dirname(__file__)
            )
            path = os.path.join(base, name)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass

        # 如果是 workflow.yml，返回硬编码内容
        if name == "workflow.yml":
            return """name: 成绩监控

on:
  schedule:
    - cron: "7,37 * * * *"
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: 安装Chrome
        run: sudo apt-get update -qq && sudo apt-get install -y -qq google-chrome-stable 2>/dev/null || true
      - name: 安装依赖
        run: pip install -r requirements.txt
      - name: 查询成绩
        env:
          ZF_USERNAME: ${{ secrets.ZF_USERNAME }}
          ZF_PASSWORD: ${{ secrets.ZF_PASSWORD }}
          WXPUSHER_TOKEN: ${{ secrets.WXPUSHER_TOKEN }}
          WXPUSHER_UID: ${{ secrets.WXPUSHER_UID }}
        run: python monitor.py
      - name: 保存记录
        run: |
          git config user.name "bot"
          git config user.email "bot@github.com"
          git add grades_history.json last_check.txt
          git diff --staged --quiet || git commit -m "update grades"
          git push
"""
        return ""

    def show_error(self, msg):
        self.root.after(0, lambda: self._show_error(msg))

    def _show_error(self, msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.config(state="normal", text="一键配置并启动")
        self.status.config(text="")
        messagebox.showerror("错误", msg)

    def show_success(self, user, repo):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn.config(state="normal", text="一键配置并启动")
        self.set_status("配置完成！", "#52c41a")
        messagebox.showinfo(
            "配置成功",
            f"成绩监控已启动！\n\n"
            f"查看状态: https://github.com/{user}/{repo}/actions\n\n"
            f"首次检查约2分钟后完成，\n"
            f"请检查 WxPusher App 是否收到推送。\n\n"
            f"之后每2小时自动检查，\n"
            f"无需再做任何操作。",
        )


def main():
    root = tk.Tk()
    app = GradeMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
