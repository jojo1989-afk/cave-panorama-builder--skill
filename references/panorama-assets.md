# 全景素材工作流与可复用提示词

适用：没有全景图、要替换示意素材，或素材出现接缝/变形。先决定是虚构概念空间还是有史料和授权的真实场所。

## 一张能用的全景图

完整等距柱状全景常用 2:1，覆盖水平 360°、垂直 180°。普通 2:1 广角照片并不自动满足这种投影。生成模型也可能忽略投影词，须实际放进查看器环视验收。

素材流程：创作/取得授权 → 检查投影 → 修接缝与两极 → 导出适当分辨率 → 接入机位 → 校准热点 → 手机验收。不要先标热点再随意裁图或水平翻转。

检查：左右边缘在环绕时是否连贯；天顶是否有拉长的人像/雕像；地面是否形成错误漩涡；相机是否像站在合理高度；门框与墙角是否连续；初始主体是否落在最佳视向；高光有无大片过曝。

如需生成或编辑图像，使用当前环境可用的图像生成工具；遵循该工具的 Skill 与图像编辑要求。不要要求用户为不需要的运行时 AI 服务配置密钥。没有出图能力时，先交付提示词与示意全景，明确其品质边界。

## 原创通用提示词

下面是本 Skill 新编的提示词，不是原作者完整提示词。工具支持时用原生 2:1 输出；不支持时，扩图/重投影后重新验证，不把拉伸当成修复。

> Create an original fictional rock-cut sanctuary interior as a full spherical equirectangular panorama, 360 degrees horizontally and 180 degrees vertically, exact 2:1 aspect ratio. A single stationary camera at human eye height, level horizon, seamless left and right edges, continuous architecture across the seam. Weathered ochre sandstone, faded mineral pigments in muted sage, dusty cinnabar and warm sand, restrained matte gold details. Subtle carved niches and original mural motifs, warm grazing light with readable shadow detail, quiet monumental atmosphere. Keep the focal shrine close to the center longitude. Do not reproduce an identifiable real cave, named heritage site, copyrighted mural or existing artwork. No visitors, no writing, no interface, no watermark. Design the zenith and nadir for spherical viewing, not a flat cinematic wide-angle composition.

“single stationary camera”和“level horizon”是验收目标，不能保证模型准确执行。主题中的宗教题材可按用户需要换成其他展陈内容。

## 三机位变体

- **主窟**：主像/主展品形成视觉锚点，两侧入口留给换景热点；不要在出图时烘焙箭头和文字。
- **卧佛/侧殿**：横向主体与侧向观看距离，保持同一矿物色系；不能用第一张图的简单水平镜像冒充不同空间。
- **中心塔柱/环廊**：相机在塔柱的一侧，能看见门洞和绕行路径的视觉提示；全景交互仍是固定机位，绕行需更多机位或真实几何。

如果两机位代表同一建筑，应先建立一致的门洞、壁画、材质和光源设计，再生成变体。无法保证跨图空间连续时，将它们写成独立的虚构展室，而不是同一真实洞窟的测绘。

## 对应的编码请求

> 用本地固定版本 Pannellum 和提供的合格全景图制作中文洞窟漫游。全景占满视口；暗场有局部探灯和显式点亮按钮，加载成功后才可揭幕。用 tour.json 管理场景与球面热点，含可返回的场景切换、解读对话框、复位和熄灯。视觉以暖褐、沙金、褪色青绿和细线圆环为主。实现触屏、键盘、减少动态效果、缺图与 WebGL 静态降级。不要添加未经要求的账号、收费或云服务。图片标明真实授权、生成虚构或程序示意。
