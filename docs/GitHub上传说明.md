# GitHub 上传说明

本项目本地 Git 已初始化，主分支为 `main`。

当前本地仓库路径：

```bash
/Users/ywj/Desktop/鼎伟crm业务人员端
```

## 1. 当前状态

已经完成：

- 安装/确认 Git：`git version 2.50.1`
- 初始化本地仓库：`git init -b main`
- 本地提交：`8278888 chore: package sales CRM prototype handoff`
- 项目文件、前后端代码、原型、文档均已纳入 Git

尚未完成：

- GitHub CLI 未登录。
- 当前命令行访问 `github.com` 超时，无法自动创建远程仓库。

## 2. 登录 GitHub CLI

网络正常时执行：

```bash
cd /Users/ywj/Desktop/鼎伟crm业务人员端
gh auth login
```

推荐选择：

- GitHub.com
- HTTPS
- Login with a web browser

如果浏览器登录不方便，也可以使用 GitHub Personal Access Token：

```bash
export GH_TOKEN=你的token
```

Token 至少需要 `repo` 权限。

## 3. 创建 GitHub 空仓库并推送

登录完成后执行：

```bash
cd /Users/ywj/Desktop/鼎伟crm业务人员端
gh repo create dingwei-crm-sales-app --private --source . --remote origin --push
```

如果你希望仓库公开，把 `--private` 改成 `--public`。

## 4. 如果已经手动创建了 GitHub 仓库

把远程地址替换成你的仓库地址：

```bash
cd /Users/ywj/Desktop/鼎伟crm业务人员端
git remote add origin https://github.com/<你的用户名>/dingwei-crm-sales-app.git
git push -u origin main
```

## 5. 验证

```bash
git remote -v
git status
git log --oneline --decorate -3
```

期望：

- `origin` 指向 GitHub 仓库。
- `git status` 显示工作区干净。
- GitHub 页面能看到 `README.md`、`frontend/`、`backend/`、`docs/`。
