---
name: cave-panorama-builder
description: "制作洞窟、古建和展厅的沉浸式全景漫游：拆解参考画面与交互，准备等距柱状全景素材，用 Pannellum 实现探灯揭幕、拖动视角、多场景热点和解读面板。适用于点亮洞窟、敦煌意象全景、360 度数字展馆；自由行走或单件 GLB 展示需另选三维方案。"
---

# 洞窟全景漫游

把“暗处发现 → 点亮空间 → 环视探索 → 热点换景 → 按需解读”做成可运行的网页体验。默认中文，沿用用户的主题、素材和技术栈。

## 先确定空间能力

本 Skill 的基础是固定机位的球面全景：视角可以旋转、缩放，点击热点切换到另一个机位。它没有几何深度、碰撞和连续位移。用户要自由行走、绕物观察或真实光照时，先说明所需资产不同，再按 [实现路径](references/implementation.md) 的三维分支执行。

原参考是小海少年的小红书视频，作者明确提到 Gemini、Pannellum 和虚构生成图片。阅读 [来源拆解](references/source-analysis.md) 可区分作者说明、视频可见现象与本 Skill 的实现设计。Gemini 是原作者的辅助制作工具，不是运行时依赖，不需要为此索要 API key。

## 从参考到可实施设计

1. 有新参考时先读正文与关键画面，记录来源和证据边界；无法看到的交互标为建议，不推断原源码。
2. 阅读 [画面与互动艺术规范](references/art-direction.md)，把材质、色彩、构图、控件、动效和时间参数映射到具体实现。默认敦煌意象只在用户未指定主题时采用。
3. 资产分为真实授权素材、生成的虚构场景和程序示意；逐场景记录来源及许可。历史资料和虚构叙述分开，缺少来源的史实不补造。
4. 先打通一个机位的素材与光照揭幕，再添加场景图和解读热点。全景素材要求见 [素材工作流与提示词](references/panorama-assets.md)。**2:1 是尺寸条件，不保证投影正确或无缝。** 不把普通宽图拉伸后称为合格全景。

## 生成可运行模板

`SKILL_DIR` 是本文件所在目录；脚本需要 Python 3.9+，运行网页需要支持 WebGL 的现代浏览器。模板自带固定版本 Pannellum，无 npm、在线 CDN 或模型服务依赖。它附带三个原创程序示意空间，用于测试交互，画面不是照片级洞窟。

```bash
python3 "$SKILL_DIR/scripts/create_tour.py" --output /absolute/path/cave-tour --title "点亮洞窟"
python3 "$SKILL_DIR/scripts/validate_tour.py" /absolute/path/cave-tour
python3 -m http.server 8772 --bind 127.0.0.1 --directory /absolute/path/cave-tour
```

访问 `http://127.0.0.1:8772`。需要 HTTP 服务，不承诺双击 `index.html` 可运行。生成器拒绝覆盖非空目录。

有合格的本地 PNG / JPEG 时，可以在生成时替换首场景：

```bash
python3 "$SKILL_DIR/scripts/create_tour.py" --output /absolute/path/my-tour --panorama /absolute/path/cave.jpg
```

随后编辑 `tour.json`，更换其余 `panorama / poster`、`provenance`、初始 `yaw / pitch / hfov` 和热点 `yaw / pitch`。替换图片后重新校准热点；模板坐标不是通用坐标。记录每个场景的内容与返回路径，不让用户进入无法退出的支路。

## 实现中的关键约束

- 灯光是同一全景之上的屏幕遮罩与揭幕，不是实时三维光源。暗场禁用全景热点；加载成功后才允许点亮。触屏不依赖 hover。
- 场景热点必须使用球面角度，由全景引擎投影。不能用固定屏幕百分比冒充贴在壁画上的标记。
- 切景等待真实 `load / error`；不要用假百分比或延时代表资源已加载。模板保留已点亮状态，用户明确“熄灯”才返回暗场。
- 解读使用可关闭的面板；键盘可以进入、退出并恢复焦点。减少动态效果模式缩短揭幕、切换与镜头动画，自动环视需用户主动开启。
- 资源失败时显示静态图与重试入口，保留场景目录和文字解读。静态降级不能被描述成可操作的全景。
- 如需陀螺仪或声音，再增加用户主动启用入口，并核对目标端的权限和自动播放限制。不要把这些新增功能说成已在原应用中实测。

数据结构、事件、离线部署与升级路径见 [实现路径](references/implementation.md)。

## 验收和交付

先运行静态预检，再在浏览器检查：加载后点亮、重复点亮/熄灯、拖动与缩放、场景往返、解读关闭、焦点恢复、窄屏、减少动态效果、缺图和无 WebGL。视频演示不等于实测原应用；静态预检也不等于浏览器测试。

```bash
python3 "$SKILL_DIR/scripts/validate_tour.py" /absolute/path/cave-tour --zip /absolute/path/cave-tour.zip
```

交付代码、素材来源、预览命令、已测项和未测项。只在用户要求发布时发布；普通 H5、小程序和小红书小工具分别核对当前平台能力。

本 Skill 可用 `python3 "$SKILL_DIR/scripts/install_local.py"` 安装到本机 Codex。安装器拒绝覆盖同名目录，不修改其他 Skill 或全局配置。新安装在下一轮对话可用。
