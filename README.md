# 正方教务系统成绩监控（河南工业大学）

[![GitHub](https://img.shields.io/badge/GitHub%20Template-Use%20this%20template-blue)](https://github.com/calculate123/zhengfang-grade-monitor/generate)
[![License](https://img.shields.io/github/license/calculate123/zhengfang-grade-monitor)](LICENSE)

每2小时自动查询教务系统成绩，有变化通过 WxPusher App 推送通知到手机。无需服务器，无需电脑开机，完全免费。

---

## 方式A：一键配置（推荐）

1. 点击上方 **Use this template** 按钮 → Create a new repository → **务必选 Private**
2. 克隆你的仓库到本地，打开终端运行：
```
pip install -r requirements-wizard.txt
python wizard.py
```
3. 按提示输入学号、密码、WxPusher AppToken/UID
4. 脚本自动配置 Secrets 并触发首次检查 —— **之后无需任何操作**

---

## 方式B：手动配置

### 第一步：创建仓库

点击右上角 **Use this template** → **Create a new repository** → 务必选 **Private**

### 第二步：注册 WxPusher 获取推送

> 注意：必须下载 WxPusher App 才能收到推送，仅关注公众号无效！

1. 在手机应用商店搜索 **WxPusher** 并下载安装
2. 打开 WxPusher App → 微信登录
3. 打开 https://wxpusher.zjiecode.com/ → 微信扫码登录
4. 点击 **应用管理** → **新建应用**（名称随意，如"成绩通知"）
5. 复制你的 **AppToken**（格式：`AT_xxxxxxxx`）
6. 在应用详情页点击 **关注** → 弹出二维码 → **用 WxPusher App 扫码订阅**
7. 在 App 中查看 **我的UID**（格式：`UID_xxxxxxxx`）

### 第三步：设置 GitHub Secrets

1. 打开你 Fork 的仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**，依次添加以下4个：

| Name | Value |
|------|-------|
| `ZF_USERNAME` | 你的学号 |
| `ZF_PASSWORD` | 教务系统密码 |
| `WXPUSHER_TOKEN` | 第二步的 AppToken |
| `WXPUSHER_UID` | 第二步的 UID |

### 第四步：启动

1. 打开仓库的 **Actions** 标签页
2. 点击 **I understand my workflows, go ahead and enable them**
3. 点击左侧 **成绩监控** → **Run workflow** → **Run workflow**
4. 等2分钟，检查 WxPusher App 是否收到成绩推送

---

## 效果

- 首次运行：推送当前所有成绩
- 之后每2小时：
  - 无变化 → 推送 "1"
  - 有新成绩 / 成绩更新 → 推送详情

## 工作原理

- 脚本跑在 GitHub 云端服务器，你电脑关机完全不受影响
- 每30分钟触发一次，内置2小时间隔过滤，保证不重复不遗漏
- 密码存在你自己的 GitHub Secrets 里，加密存储，任何人也看不到
- 完全免费，每月仅消耗约60分钟 Actions 额度（免费额度2000分钟）

## 常见问题

**Q: 安全吗？**
A: 学号和密码存在你自己的私有仓库 Secrets 中，GitHub 加密存储。

**Q: 没收到推送通知？**
A: 检查：(1) 是否下载了 WxPusher App（仅关注公众号无效）；(2) 是否在应用详情页扫码订阅了该应用。

**Q: 换了教务密码怎么办？**
A: 到仓库 Settings → Secrets → 更新 `ZF_PASSWORD`。

**Q: 能改查询频率吗？**
A: 编辑 `.github/workflows/monitor.yml` 修改 cron，编辑 `monitor.py` 修改 `CHECK_INTERVAL`。

**Q: 其他学校能用吗？**
A: 如果也是正方系统（URL 含 `jwglxt`），Fork 后修改 `monitor.py` 中的 `ZF_BASE_URL` 即可。
