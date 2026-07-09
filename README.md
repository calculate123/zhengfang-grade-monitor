# 正方教务系统成绩监控（河南工业大学）

[![GitHub](https://img.shields.io/badge/GitHub%20Template-Use%20this%20template-blue)](https://github.com/calculate123/zhengfang-grade-monitor/generate)
[![License](https://img.shields.io/github/license/calculate123/zhengfang-grade-monitor)](LICENSE)

下载桌面软件 → 输入学号密码 → 微信扫码订阅 → 点击开始。每2小时自动查成绩，变化推送到手机。无需服务器，关机不受影响。

---

## 方式A：桌面软件（最简单）

1. 下载 `成绩监控.exe`
2. 双击打开，填写：
   - 学号、教务密码
   - WxPusher AppToken + UID（App 内获取）
   - GitHub Token（点软件内按钮获取）
3. 点击 **一键配置并启动** → 完成

**源码构建：**
```
pip install pyinstaller pynacl requests
build.bat
```

---

## 方式B：GitHub 一键配置

1. 点击上方 **Use this template** → Create new repository → **务必选 Private**
2. 克隆仓库，运行：
```
pip install -r requirements-wizard.txt
python wizard.py
```
3. 按提示输入信息 → 自动配置完成

---

## 方式C：手动配置

1. 点击 **Use this template** → Create new repository → **Private**
2. Settings → Secrets → 添加 4 个 Secret：

| Name | Value |
|------|-------|
| `ZF_USERNAME` | 学号 |
| `ZF_PASSWORD` | 教务密码 |
| `WXPUSHER_TOKEN` | WxPusher AppToken |
| `WXPUSHER_UID` | WxPusher UID |

3. Actions → 启用 → Run workflow

---

## 效果

- 首次：推送当前所有成绩
- 之后每2小时：无变化 → "1" / 有变化 → 详细推送
- 电脑关机、没网都不影响（运行在 GitHub 云端）

## WxPusher 设置

手机应用商店下载 **WxPusher** App → 微信登录 → wxpusher.zjiecode.com 扫码 → 新建应用 → 复制 AppToken → 点关注扫码 → 查看 UID

## 常见问题

**Q: 安全吗？** 密码存在你自己的 GitHub Secrets 中，加密存储。

**Q: 免费吗？** 完全免费，GitHub Actions 每月2000分钟免费额度足够。

**Q: 换了密码怎么办？** 重新运行软件或手动更新 Secret。

**Q: 其他学校？** 也是正方系统（URL 含 jwglxt）的话，修改 `monitor.py` 中的 `ZF_BASE_URL`。
