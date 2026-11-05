# 队友协作说明

## 有仓库写入权限

先接受 GitHub 协作者邀请。每次修改创建一个分支：

```powershell
git switch main
git pull --ff-only
git switch -c feature/your-change
```

修改并完成 README 中的检查后提交：

```powershell
git add <你修改的文件>
git commit -m "Describe your change"
git push -u origin feature/your-change
```

在 GitHub 上从该分支创建 Pull Request，写清改了什么、如何验证，再由队友审核合并。

## 暂时没有写入权限

在 GitHub 点击 Fork，克隆自己的 Fork，创建分支并提交修改，然后向原仓库创建 Pull Request；无需等待协作者邀请。

## 修改位置与生成文件

游戏规则在 `software/tank.s`，网页样式和交互在 `web/dist/`。`web/dist/rom.js`、`build/tank.hex`、`build/tank.lst` 由汇编生成，不要只改机器码。

修改汇编后运行 README 的规则测试、网页导出和网页测试；重新生成 `浏览器试玩.html`。修改显示外设或 Logisim 电路生成器时还应重建并实际打开 `tank.circ` 检查。无需为单纯网页样式修改重跑整局硬件仿真。

请勿提交访问令牌、账号凭据、个人配置、虚拟环境或 `tools/_vendor/`。原 CPU 备份位于 `original/`，修改前请保留备份。
