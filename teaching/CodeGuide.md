通过git进行代码上传

git status 检查修改状态
git add .  提交所有修改
git commit -m"描述本次修改的内容"
git branch 查看当前分支
git push origin master  把本地提交推送到远程仓库(master)

### 开发流程：
## 步骤 1：先同步最新的 main
每次开始新功能前，先确保本地 main 是最新的：
在仓库目录下:

git checkout main
git pull origin main

## 步骤 2：从 main 拉一个个人功能分支
建议统一分支命名规范：
功能：feature/功能名-简短描述
修复：bugfix/问题描述
例如：
git checkout -b feature/login-page
现在你在 feature/login-page 分支上，可以放心乱改，不会影响别人。

## 步骤 3：正常写代码、调试
一路改，改到你觉得可以提交一小步，就：
git status  # 看看改了哪些文件
git add .   # 或者逐个 add 某些文件
git commit -m "feat: 实现基础登录页面 UI"
提交建议用统一格式，比如：
•	新功能：feat: xxxx
•	修 bug：fix: xxxx
•	文档：docs: xxxx
•	重构：refactor: xxxx

## 步骤 4：把分支推到 GitHub
第一次推这个分支时：
git push -u origin feature/login-page
之后再推就直接：
git push

## 步骤 5：在 GitHub 上发起 Pull Request（PR）
1.	打开 GitHub 仓库页面，会看到提示「Compare & pull request」
2.	点击后检查：
base：main
compare：feature/login-page
3.	写清楚 PR 标题和说明，例如：
标题：feat: 增加登录页面
描述：简要说明改了什么、需要怎么测试
然后提交 PR。

## 步骤 6：代码评审（Review）和合并
•	其他人打开这个 PR，查看改动内容
•	如果没问题，在 GitHub 上点 Approve
•	Leader 或有权限的人点击 Merge（建议使用 Squash and merge 或 Merge）
•	合并完成后，可以在 GitHub 上删除这个功能分支

本地也可以删掉：
git checkout main
git pull origin main    # 同步一下最新 main
git branch -d feature/login-page   # 删除本地分支

### 多人同时开发时如何避免冲突
重点：
1.	每个人只在自己的分支上改，不动别人的分支
2.	任何人要改公共文件（比如 requirements.txt、router.js 或数据库模型等），要在 PR 说明里特别写清楚
如果合并时 GitHub 提示冲突，一般可以这样解决：
1.	在本地切到你的分支：
2.	git checkout feature/login-page
3.	把最新 main 合并进来：
4.	git fetch origin
5.	git merge origin/main
6.	Git 会提示冲突文件，手动打开这些文件，找到类似：
7.	<<<<<<< HEAD
8.	你的版本
9.	=======
10.	main 分支上的版本
11.	>>>>>>> origin/main
12.	手动选择保留哪部分，或者两边内容合并，然后删掉这些标记。
13.	解决完所有冲突后：
14.	git add 冲突文件1 冲突文件2 ...
15.	git commit     # 提交合并后的结果
16.	git push
17.	回到 GitHub，再次检查 PR，冲突就消失了，可以继续合并。

### 修 Bug 的流程（和开发功能类似）
比如上线后发现一个 bug，或者在测试时发现问题，可以这样：
1.	确认本地 main 最新：
2.	git checkout main
3.	git pull origin main
4.	拉修复分支：
5.	git checkout -b bugfix/fix-login-error
6.	修改代码、提交：
7.	git add .
8.	git commit -m "fix: 修复登录失败时提示信息错误"
9.	git push -u origin bugfix/fix-login-error
10.	发起 PR，说明 bug 的现象、修复方法
11.	其他人 Review → 合并 → 删除分支

### 推荐的一些协作习惯
1. 使用 Issues 管理任务
在 GitHub 仓库的 Issues 中：
•	开一个 Issue：[功能] 登录页面 或 [Bug] 登录失败提示错误
•	在 Issue 里说明需要做什么
•	发 PR 时在描述写上：Closes #1（1 是 Issue 编号）
合并后这个 Issue 会自动关闭，任务链路清晰。
2. 约定统一分支命名
例如：
•	功能：feature/登录功能 → 英文更好：feature/login
•	修复：bugfix/登录提示错误
•	实验：experiment/new-layout
这样在 GitHub 分支列表里，一眼能看出哪个是干嘛的。
3. 经常同步 main，避免大冲突
•	每个人每天开始写代码前，习惯性做：
•	git checkout main
•	git pull origin main
•	新建功能分支时，一定基于最新的 main 来拉分支。

### 协作例子
假设你们要做一个平台，三个任务：
•	A：负责 用户认证模块
•	B：负责 前端仪表盘页面
•	C：负责 日志采集 API
操作大概是：
1.	A：
拉分支：feature/auth-backend
完成登录、注册 API
发 PR：feat: 完成后端用户认证接口 → B 或 C 帮你 Review → 合并
2.	B：
拉分支：feature/dashboard-ui
完成前端首页仪表盘
发 PR：feat: 仪表盘前端页面 → A(leader)审 → 合并
3.	C：
拉分支：feature/log-collector-api
实现日志上传接口
发 PR：feat: 日志采集接口 → A(leader)审 → 合并
最后，main 分支就始终是「当前最稳定、可运行版本」，可以用来部署测试环境或生产环境。



### 问题：上传失败（fatal: unable to access 'https://github.com/beinlov/botnet.git/': Recv failure: Connection was reset）
尝试改用 SSH 方式连接 GitHub（避开 https 问题）
如果你所在环境（学校/单位）对 https 有限制，改用 SSH 通常更稳定：
## 1 生成 SSH key（如果你以前没生成过）
在命令行执行：
ssh-keygen -t ed25519 -C "你的GitHub邮箱"
一路按回车即可（默认保存在 C:\Users\你的用户名\.ssh\id_ed25519）。
然后查看公钥：
type C:\Users\你的用户名\.ssh\id_ed25519.pub
复制输出的一整行内容。
## 2 在 GitHub 绑定 SSH key
登录 GitHub
右上角头像 -> Settings
左侧菜单选择 “SSH and GPG keys”
New SSH key -> 把刚才复制的内容粘贴进去 -> 保存
## 3 修改当前仓库的远程地址为 SSH
在 D:\workspace\botnet 中执行：
git remote set-url origin git@github.com:beinlov/botnet.git
测试一下：
ssh -T git@github.com
第一次会提示是否信任，输入 yes 回车，如果显示类似：
Hi beinlov! You've successfully authenticated, but GitHub does not provide shell access.
说明 SSH 通了。
然后再 push：
git push origin master
