# bd-card — BD 名片落地页

公众号「阅读原文」的统一落地页。读者从公众号文章点进来，扫码加微信。

## 线上地址（开启 Pages 后）

https://zlj123455.github.io/storage-compass/

## 你需要做的一件事

**开 GitHub Pages（一次性）**：浏览器打开
https://github.com/zlj123455/storage-compass/settings/pages
→ Source 选 `gh-pages` 分支、目录 `/ (root)` → Save。
约 1 分钟后上面那个地址就能访问。

（二维码已就绪：从已发文章的联系方式卡中裁出的个人码，文件为 `qr-wechat.png`。若以后要换码，直接覆盖同名文件再跑 deploy.sh。）

## 页面结构（index.html 单文件，无依赖）

- 头部：姓名 / 中科曙光 FlashNexus BD / 存储罗盘作者
- 三张卡：我能帮到你什么、适合加我的人、加我微信（二维码）
- 内容入口：公众号「存储罗盘」+ GitHub 仓库

## 更新流程

改完 index.html 或换二维码后：

```
./deploy.sh "改了什么"
```

或手动：

```
git add -A && git commit -m "..." && git push origin gh-pages
```
