# 正方教务系统成绩监控（河南工业大学）

每2小时自动查询教务系统成绩，有变化通过微信推送通知。**无需服务器，无需电脑开机。**

## 一键部署（5分钟）

### 第一步：Fork 本仓库

点击右上角 **Fork** → **Create fork**

### 第二步：注册WxPusher（微信推送）

1. 微信搜索公众号 **"WxPusher"** → 关注
2. 打开 https://wxpusher.zjiecode.com/ → 微信扫码登录
3. 点击 **"应用管理"** → **"新建应用"**（名称随意）
4. 复制 **AppToken**（AT_开头）
5. 点击 **"关注"** → 用微信扫码关注此应用
6. 在公众号对话框回复 **"我的UID"** → 复制 UID

### 第三步：设置GitHub Secrets

1. 打开你 Fork 的仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**，依次添加4个：

| Name | Value |
|------|-------|
| `ZF_USERNAME` | 你的学号 |
| `ZF_PASSWORD` | 教务系统密码 |
| `WXPUSHER_TOKEN` | 第二步获得的 AppToken |
| `WXPUSHER_UID` | 第二步获得的 UID |

### 第四步：启动

打开仓库的 **Actions** 标签页 → 点击 **I understand my workflows, go ahead and enable them**

然后进入 **成绩监控** workflow → **Run workflow** → 手动触发一次测试。

---

## 效果

- **首次**：推送当前所有成绩
- **之后每2小时**：
  - 无变化 → 推送 "1"
  - 有新成绩/成绩变化 → 推送详情

## 常见问题

**Q: 安全吗？密码存在哪？**
A: 密码存在你自己的 GitHub 仓库 Secrets 里（不是我们的服务器），GitHub 会加密存储。

**Q: 免费吗？**
A: 完全免费。GitHub Actions 免费额度足够。

**Q: 能改查询频率吗？**
A: 编辑 `.github/workflows/monitor.yml`，修改 `cron: "0 */2 * * *"` 中的数字（小时）。

## 适配其他学校

如果你的学校也用正方系统，修改 `monitor.py` 中的 `ZF_BASE_URL` 即可。
