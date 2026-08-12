---
name: make-journal-material-skill
description: 将室内、旅行、静物或生活照片提炼成复古水粉剪纸风的手帐独立素材合集，并固定输出为 1920×1080（16:9）透明背景 PNG。用于用户要求“做手帐素材合集”“从照片提取独立物件/贴纸”“生成 16:9 透明 PNG 素材页”或希望延续佛罗伦萨室内插画的手绘风格时。
---

# 手帐素材合集

把照片中的代表性物件转成可单独剪贴的手绘素材，默认生成 9 组，最终交付 1920×1080 透明 PNG。

## 固定标准

- 画布：横向 16:9，最终精确为 1920×1080。
- 格式：PNG，必须包含有效透明通道。
- 排版：默认把 9 组素材按三行三列集中排列；保持宽松间距，左右保留透明余量。
- 背景：最终完全透明；没有房间、墙面、地面、阴影、描边贴纸底或装饰填充。
- 风格：以 `assets/style-reference.png` 为权威参考，只迁移画法，不复制其中的物件。

## 工作流

1. 查看输入照片，确认它是内容来源；查看 `assets/style-reference.png`，确认它是风格来源。
2. 从照片中选择默认 9 组代表性物件：
   - 优先轮廓清楚、具有旅行记忆或装饰价值的家具、花器、植物、陶瓷、画框、灯具和小摆件。
   - 把零碎但相关的小物合成一组，例如茶壶与茶杯、同一层架上的陶瓷壶、成排玩偶。
   - 保证造型、尺度和颜色有变化；不要重复同类物件。
   - 忽略文字、商标、可识别人脸、杂乱线缆和没有独立轮廓的背景。
3. 使用内置图片生成工具。把输入照片与 `assets/style-reference.png` 都作为参考图，并明确标注：
   - 输入照片：内容与物件身份来源。
   - 风格参考：笔触、色彩、质感、简化程度和完成度来源。
4. 生成一张 16:9 素材页，使用完全平坦、均匀的 `#ff00ff` 色键背景。绿色常用于物件，所以不要默认使用绿色色键。
5. 将生成的色键源图复制到工作区，运行本 Skill 自带的透明 PNG 脚本。相对路径从本 `SKILL.md` 所在目录解析：

   ```bash
   python <skill-dir>/scripts/finalize_transparent_png.py \
     --input <chroma-source.png> \
     --output <final.png>
   ```

   该脚本会一次完成色键移除、边缘去色、1920×1080 规范化和透明度验证。

6. 先用 `python -c "from PIL import Image"` 检查 Pillow。若缺少，优先使用宿主提供的带 Pillow 的 Python；得到用户许可后也可运行 `python -m pip install -r <skill-dir>/requirements.txt`。不得静默安装依赖。

7. 目视检查：九组素材完整、无重叠、无裁切、无洋红边、无背景残留；风格统一且手绘感明显。
8. 脚本默认从画布边缘估算实际色键。如果存在洋红边，只重跑一次并追加 `--edge-contract 1`；如果自动识别失准，使用 `--key-color '#ff00ff'` 明确指定色键。
9. 把最终文件保存到用户指定目录；未指定时保存到当前工作区的 `output/journal-materials/`。只展示最终透明 PNG，并提供可点击的绝对路径。

## 用户交付规则

- 把色键源图、失败变体、临时透明图和其他处理文件视为内部中间产物。
- 不在进度消息或最终答复中主动展示、嵌入、链接或提供中间产物下载；不要把洋红色键图作为生成结果交给用户。
- 图片生成工具若自动显示色键源图，把它视为宿主界面的临时预览，不要再次展示或引导用户下载，并继续完成透明化处理。
- 只有最终透明 PNG 通过尺寸、透明通道和目视检查后，才向用户展示并提供下载链接。
- 如果最终处理失败，只说明失败原因和下一步，不展示中间图；仅当用户明确要求排查或查看中间文件时例外。

## 生成提示词要求

提示词要明确包含以下内容，可按照片调整物件清单：

```text
Use case: style-transfer
Asset type: 16:9 transparent PNG journaling material collection
Primary request: Extract exactly nine distinctive object groups from the content photo and redraw them as separate cuttable journaling motifs. Match the supplied style-reference image for rendering only.
Input images: Image 1 = content and object source; Image 2 = authoritative style reference.
Scene/backdrop: perfectly flat uniform #ff00ff chroma-key background for later removal; no wall, floor, room, scenery, shadows, or texture in the background. Do not use #ff00ff in any object.
Style/medium: visibly hand-painted retro folk art; opaque gouache on warm paper, light dry screen-print grain, hand-cut-paper edges, slightly wonky geometry, uneven pigment, warm-brown restrained internal lines, rich but flattened decorative detail.
Composition/framing: exact horizontal 16:9; nine independent groups in a centered loose three-column by three-row layout; broad empty side margins; generous separation and cutting space; no touching or overlap.
Constraints: preserve recognizable object identities; keep handmade irregularity visible; every motif fully visible; no text, logo, watermark, people, or identifiable faces.
Avoid: full room scene, realistic light and perspective, gradients, glossy surfaces, cast shadows, near-black areas, perfect vector curves, minimalist icons, photographic textures, missing or duplicated motifs.
```

## 风格判断

目标不是极简矢量，也不是写实水彩：

- 物件细节丰富，但被处理成装饰图案。
- 边缘、直线和圆形略有手画的不规整感。
- 色块内部能看到干笔、颜料浓淡和纸张颗粒。
- 花朵、叶片、木纹和陶瓷图案使用朴拙、概括的符号。
- 透视与光影被压平；深色使用胡桃棕、橄榄绿或灰蓝，避免大块纯黑。

## 透明输出规则

- 不把米白背景误当作最终透明背景；米白只存在于物件本身和风格参考中。
- 色键源图的四周必须是纯 `#ff00ff`，没有渐变、纸纹、阴影或地面线。
- 透明成品必须具有 RGBA 通道、透明四角和非空主体。
- 如果物件包含写实毛发、玻璃、烟雾或半透明材质，先把它们改画成不透明的水粉剪纸形态；不要为此自动切换模型。

## 运行条件与失败处理

- 必须由宿主环境提供图片生成或图片编辑能力；本 Skill 提供工作流、风格参考和后处理，不包含生成模型或 API 密钥。
- 后处理只依赖 Python 3 与 `requirements.txt` 中声明的 Pillow，不依赖其他本地 Skill、用户目录或 Codex 系统脚本。
- 如果宿主没有图片生成能力，清楚说明该限制并停止，不要假装已经生成图片。
- 如果无法运行 Python 或 Pillow，在交付前说明缺少的依赖；不得把带洋红背景的中间图当作透明 PNG 成品。
