# 实现框架与路径

核对日期：2026-11-04。以下是独立实现，不是原作者源码。

## 分层

```text
主题 / 参考 / 内容来源
          ↓
全景资产（2:1 等距柱状图 + 小预览 + 来源声明）
          ↓
tour.json（场景图、初始镜头、热点角度、解读内容）
          ↓
Pannellum（球面投影、拖动、缩放、热点投影、切景）
          +
体验层（探灯遮罩、亮灯状态、题签、目录、解读对话框）
          ↓
静态 HTTP 服务 → 桌面 / 手机 H5 → 目标端验收
```

Pannellum 用 WebGL 展示全景，单图、多机位和多分辨率都能组织为静态资源。参考：[官方概览](https://pannellum.org/documentation/overview/)。本模板固定 2.5.7，来源为官方[下载页](https://pannellum.org/download/)指定的包，并保留 MIT 许可。升级时重新做客户端验收，不在运行时引用 `latest`。

## 随附模板

```text
index.html           空间容器、光照遮罩、外围 UI 和原生 dialog
styles.css           色彩、排版、窄屏、安全区、减少动态效果
app.js               状态、加载、热点、操作、错误和静态降级
tour.json            唯一的内容配置入口
panoramas/*.png      原创程序示意空间，换成授权/生成的合格全景
vendor/              固定版本引擎、样式、许可与来源校验记录
```

开发与运行不需要 Gemini API。使用任何可用的编码助手都可以生成/修改这一工程；作者所述 Gemini 属于制作方式。

## 状态与时序

灯光状态与资源状态要分开。`load` 才代表图片已就绪；`scenechange` 只表示切换开始。

| 状态 | 可用操作 | 离开条件 |
|---|---|---|
| booting | 查看加载提示 | load → dark；error → fallback |
| dark | 探灯、点亮、阅读来源 | 点亮 → revealing |
| revealing | 有限操作，避免重复触发 | 遮罩揭幕完成 → exploring |
| exploring | 拖动、缩放、热点、解读、复位、熄灯 | 切景 / 熄灯 / 错误 |
| switching | 显示真实等待状态，暂时禁用跳转 | load → exploring；error → fallback |
| fallback | 静态图、场景目录、文字解读、重试 | 用户重试页面 |

原视频可见过渡进度条，但无法确认其内部计量。本模板用不表示百分比的等待动画。光照只是叠加遮罩的透明度变化，不改变全景内各对象的几何光照。

## 数据与球面热点

`tour.json` 顶层含 `title / firstScene / scenes`。场景以稳定 ID 为键，至少有 `title / panorama / poster / pitch / yaw / hfov / provenance / hotSpots`。热点含 `id / kind / label / pitch / yaw`；`kind=scene` 需要 `target`，`kind=info` 需要 `title / body`。

完整样例在 `assets/starter/tour.json`，不要另维护重复的数据源。`panorama` 和 `poster` 是工程内相对路径。文本按纯文本放入 DOM；不要将外部内容直接拼进 HTML。

球面角度单位为度。对应同一张等距柱状图的初始定位近似为：`yaw = 360 × u/W − 180`，`pitch = 90 − 180 × v/H`。最终用引擎的 `hotSpotDebug` 或 `mouseEventToCoords` 现场校准；素材朝向与地平线修正会影响结果。发布时关闭调试。

热点的 HTML 可以自定义，但位置交给引擎投影。当前模板的自定义按钮会调用 `loadScene` 或打开原生对话框。保留热点之外的场景目录，便于手机和键盘访问。

参数及事件参考：[配置](https://pannellum.org/documentation/reference/)、[API](https://pannellum.org/documentation/api/)。常用 `loadScene / lookAt / getScene / stopMovement / destroy`；错误监听必须早于正常操作。

## 三条实现路径

| 场景 | 路径 | 资产要求 / 边界 |
|---|---|---|
| 小型作品集、科普展馆 | 随附 Pannellum + HTML/CSS/JS，静态部署 | 几张合格全景即可；固定机位，最快建立体验 |
| 高分辨率、多机位正式展陈 | 保留 Pannellum，离线生成多分辨率切片，配置按需加载 | 先处理接缝和出处，再优化体积；需要服务器正确 MIME 与缓存 |
| 自由走动、穿过塔柱、实时手电、可绕物观察 | Three.js / 同类三维引擎 + GLB 场景、相机、碰撞与真实灯光 | 需要几何和材质；全景原图不能自动变成完整空间模型 |

多机位参考：[官方虚拟漫游示例](https://pannellum.org/documentation/examples/tour/)；几何资产分支可查 [Three.js GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html)。不要为了“看起来高级”给固定机位全景引入完整游戏引擎。

## 部署与验收要点

- 本地也用 HTTP；`file://` 下 JSON 和图片可能因安全限制加载失败。同源图片最省事，远程资源必须处理 CORS、许可和失效问题。
- 先用 2048×1024 / 4096×2048 控制移动端显存；更大素材评估设备纹理上限或切片方案。不存在所有手机都能加载的任意大单图。
- 检查 yaw 接缝、天顶、地面和门洞直线。视觉检查不能由尺寸验证代替。
- 测试重复亮灯/熄灯、切景返回、资源缺失、降级、焦点和窄屏。真实手机、iOS 和目标应用 WebView 需要独立记录，本机浏览器通过不代表它们通过。
- 如发布到特定平台，先阅读当期官方限制；“链接来自小红书”只表示参考来源，不表示这个作品是小红书小工具，也不表示模板能直接上传。
