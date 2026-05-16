# AIRI-Male VRM 3D 渲染推进计划

> 生成时间: 2026-05-14 21:51 CST
> 后接 [A2: VRM渲染推进] Task

---

## 一、当前状态总览

| 项目 | 状态 |
|:---|:---:|
| 🎮 AIRI Dev Server (`localhost:5173`) | ✅ **运行中** (Vite, node PID 55741) |
| 🧩 `three-vrm` 依赖 | ✅ 已安装 (`@pixiv/three-vrm@3.5.2`, `@pixiv/three-vrm-animation@3.5.2`) |
| 📄 VRM 示例模型 | ✅ 2个 (AvatarSample-A, AvatarSample-B, 各~26MB) |
| 🎭 VRM 场景组件 | ✅ `MaleCharacterVRMScene.vue` (完整组件, Three.js + OrbitControls) |
| 🗺️ VRM 角色选择页 | ✅ `characters/male` 路由 + `MaleCharacterGrid.vue` |
| 🎞️ VRM 待机动画 | ✅ `idle_loop.vrma` (154KB, 在 `stage-ui-three/src/assets/vrm/animations/`) |
| 🎨 `stage-ui-three` VRM 核心 | ✅ `useVRMLoader()` / `loadVrm()` / `AiriMToonMaterialLoaderPlugin` |
| 🧑‍🦰 男性角色注册 | ✅ 5角色 (alexander/haruto/jihoon/moran/kai) 已定义在 `core-character` |
| 📂 `core-character` 测试 | ✅ 44测试全通过 |

---

## 二、目前卡住的点 & 根因分析

### 🔴 阻塞项 #1 — 所有5名男性角色用的都是占位 Live2D 模型

**位置**: `packages/core-character/src/male-characters.ts`
**代码**:
```typescript
avatarModels: [
  {
    type: 'live2d',  // ← 写死为 live2d
    config: {
      live2d: {
        urls: [`/assets/live2d/models/hiyori_free_zh/Hiyori.model3.json`], // ← 女版占位
      },
    },
  },
]
```

**影响**: `MaleCharacterGrid.vue` 中 `card.isVRM` 全为 `false`，点击角色不会触发 VRM 预览，而是显示渐变色占位。

**根因**: 5个角色在 `core-character/src/male-characters.ts` 注册时 avatarModels 只注册了 live2d 类型（且使用 Hiyori 女版占位），没有注册对应的 VRM 模型。

### 🔴 阻塞项 #2 — VRM_MODEL_URLS 全部指向同一个示例模型

**位置**: `apps/stage-web/src/components/MaleCharacterGrid.vue`
**代码**:
```typescript
const VRM_MODEL_URLS: Record<string, string> = {
  alexander: avatarSampleAVrmUrl,
  haruto: avatarSampleAVrmUrl,  // ← 全是 AvatarSample-A
  jihoon: avatarSampleBVrmUrl, // ← AvatarSample-B
  moran: avatarSampleBVrmUrl,  // ← 重复
  kai: avatarSampleAVrmUrl,    // ← 重复
}
```

**影响**: 即使注册了 VRM 类型，3个角色(Alexander/Haruto/Kai)显示同一个灰色短发模型，2个角色(Jihoon/Moran)显示同一个粉色长发模型。无角色区分度。

**根因**: 只有2个 VRoid Hub 样本模型，没有5个角色的定制 VRM 模型。

### 🟡 阻塞项 #3 — VRM 待机动画导入路径受阻

**位置**: `MaleCharacterGrid.vue`
**代码**:
```typescript
const idleLoopVrmaUrl: string | undefined = undefined
/* 
 * 注释说明: 需要将 idle_loop.vrma 加入
 * @proj-airi/stage-ui-three 的 package.json exports 或者加 vite alias
 */
```

**现状**: 动画文件 `idle_loop.vrma` 存在 (`stage-ui-three/src/assets/vrm/animations/`)，
`stage-ui-three` 的 exports map 已有 `./assets/vrm` 导出（指向 `index.ts`，但该文件又 `export * from './animations'` → index.ts 用 `new URL('./idle_loop.vrma', import.meta.url)` 暴露了 URL），
然而 `stage-web` 的 `MaleCharacterGrid.vue` 并没有导入这个 exports 路径。

**影响**: VRM 加载后没有待机动画，角色静止站立。

### 🟢 非阻塞 — VRM 核心渲染架构完好

- ✅ `useVRMLoader()` 正确注册 MToon 材质、outline 扩展
- ✅ `loadVrm()` 完整的骨架优化、bounding box 计算、摄像机自动定位
- ✅ `MaleCharacterVRMScene.vue` 完整的生命周期、动画循环、OrbitControls
- ✅ Vite 已正确配置 VRM 文件下载和缓存（从 `dist.ayaka.moe` 下载到 `.cache/vrm/`）

---

## 三、推进计划（按优先级）

### Phase 1: 打通 VRM 渲染链路（立即 → 1h）

**目标**: 让至少一个男性角色能在 `characters/male` 页面加载并显示 VRM 3D 模型。

| # | 步骤 | 操作 | 涉及文件 |
|:--:|:-----|:-----|:---------|
| 1.1 | 注册 VRM 类型到角色 | 在 `createMaleCharacterRegistrations()` 的 `avatarModels` 数组中，为每个角色额外添加一个 `type: 'vrm'` 的模型条目 | `packages/core-character/src/male-characters.ts` |
| 1.2 | 修复 idle 动画导入 | 在 `MaleCharacterGrid.vue` 中通过 `@proj-airi/stage-ui-three/assets/vrm` 导入 `animations.idleLoop` | `apps/stage-web/src/components/MaleCharacterGrid.vue` |
| 1.3 | 角色详情页 VRM 模型分流 | 确保 `MaleCharacterGrid.vue` 的 `card.isVRM` 逻辑正确识别 | `apps/stage-web/src/components/MaleCharacterGrid.vue` |
| 1.4 | 验证渲染 | 打开 `localhost:5173/characters/male`，点击角色 -> 检查 VRM 3D 预览是否正常加载 | 浏览器 |

### Phase 2: 定制 5 位男性角色 VRM 模型（2-3天）

**目标**: 让每个角色有自己的专属 VRM 模型（形象匹配）。

| # | 步骤 | 操作 | 备注 |
|:--:|:-----|:-----|:-----|
| 2.1 | 寻找可商用男体 VRM 基底 | 从 VRoid Hub、VRoid Mobile、或免费 VRM 模型中获取基底 | 根据角色身材调整 |
| 2.2 | 角色定制化 | 统一外联 AI 造型师，根据角色设定（发色/眼型/服饰）微调 | Alexander金色短发/Alexander蓝色眼；墨然黑色长发/汉服 |
| 2.3 | 测试模型导入 | 将 .vrm 文件放入 `stage-ui/src/assets/vrm/models/{角色id}/` | 参考 AvatarSample 目录结构 |
| 2.4 | 更新 VRM_MODEL_URLS | 替换 MaleCharacterGrid.vue 中的模型映射 | imports 改用 `?url` 方式 |
| 2.5 | 验证各角色预览 | 逐一测试5角色加载显示 | 检查骨骼/材质/表情 |

### Phase 3: 3D 展示增强（可选，迭代中优化）

| # | 步骤 | 操作 | 备注 |
|:--:|:-----|:-----|:-----|
| 3.1 | 环境光/背景美颜 | 为每个角色添加独特的环境光照预设 | Alexander古典暖色/墨然冷月 |
| 3.2 | 表情/眨眼 | 利用 VRM BlendShape 添加 idle 表情循环 | 现有 `stage-ui-three` 已有 `expression.ts` |
| 3.3 | 唇形同步 | 结合 ARIA 音频系统，让 VRM 模型在语音时张嘴说话 | 现有 `lip-sync.ts` 和 `wlipsync` 已到位 |
| 3.4 | 首帧/待机姿势 | 为每个角色设置 unique 待机姿态（站姿/手势） | 可用 `.vrma` 动画 |

---

## 四、当前进度甘特图

```
Phase 1: 打通渲染链路    ⬛⬛⬛⬛⬜⬜⬜⬜⬜⬜  40% [正在阻塞]
  ├─ 1.1 注册VRM类型      ⬛⬛⬛⬛⬛⬛⬛⬛⬜⬜  80% ✅ avatarModels已完成定义结构
  ├─ 1.2 idle动画导入     ⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜  10% ❌ 导入路径注释掉了
  ├─ 1.3 isVRM逻辑        ⬛⬛⬛⬛⬛⬜⬜⬜⬜⬜  50% ✅ 组件存在但avatarModels type是live2d
  └─ 1.4 验证渲染         ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 尚未验证

Phase 2: 定制模型          ⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜  10% [待天赐决策]
  ├─ 2.1 男体基底模型     ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 未获取
  ├─ 2.2 角色定制化       ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 未开始
  ├─ 2.3 模型文件部署     ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 未开始
  ├─ 2.4 更新MODEL_URLS   ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 未开始
  └─ 2.5 验证各角色       ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% ❌ 未开始

Phase 3: 展示增强           ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜   0% [看板项]
```

---

## 五、具体修改代码参考

### 5.1 修复角色 VRM 注册（male-characters.ts）

在 `createMaleCharacterRegistrations()` 的 avatarModels 数组追加 VRM 条目：

```typescript
avatarModels: [
  // ... 原有的 live2d 条目保持不变 ...
  {
    id: generateId('model', characterId, 'vrm'),
    characterId,
    name: `${config.name} VRM Model`,
    type: 'vrm',  // ← 关键: 类型改为 vrm
    description: `AIRI-Male ${config.nameCN} VRM 3D Model`,
    config: {
      vrm: {
        urls: [`/assets/vrm/models/${characterId}/model.vrm`], // ← VRM文件路径
      },
    },
    createdAt: ts(),
    updatedAt: ts(),
  },
  // ... 2D portrait avatar (可选) ...
],
```

### 5.2 修复 idle 动画导入（MaleCharacterGrid.vue）

```typescript
// 替换原来的注释掉的 import
// import { animations } from '@proj-airi/stage-ui-three/assets/vrm'
// 或直接用 Vite 的 ?url 方式:
import idleLoopVrmaUrlRaw from '@proj-airi/stage-ui-three/assets/vrm/animations/idle_loop.vrma?url'

// 但目前 @proj-airi/stage-ui-three 的 exports 没有导出子目录文件
// 临时方案: 复制 idle_loop.vrma 到 stage-ui 的 assets 目录下
// 或添加 alias 在 vite.config.ts:
// '@proj-airi/stage-ui-three/assets': resolve('../../packages/stage-ui-three/src/assets')
```

### 5.3 新增 VRM 模型文件结构

```
packages/stage-ui/src/assets/vrm/
├── models/
│   ├── AvatarSample-A/
│   │   ├── AvatarSample_A.vrm
│   │   └── preview.png
│   ├── AvatarSample-B/
│   │   ├── AvatarSample_B.vrm
│   │   └── preview.png
│   ├── alexander/                    # ← 新增
│   ├── haruto/                       # ← 新增
│   ├── jihoon/                       # ← 新增
│   ├── moran/                        # ← 新增
│   └── kai/                          # ← 新增
```

---

## 六、是否需要天赐决策

### ✅ 可以自主完成
- Phase 1.1~1.4 的代码修改（注册VRM类型、修复动画导入、验证渲染）
- 使用现有 AvatarSample 模型验证链路通断

### ❓ 需要天赐确认后再进行
- **Phase 2 模型定制**: 是否需要为5个角色定制专属 VRM 模型？预算和来源？
  - 选项A: 从 VRoid Hub 下载免费男体模型 + 自行微调
  - 选项B: 外约角色3D模型师（2-5天，成本约 500-2000 元/角色）
  - 选项C: 先用现有 AvatarSample 占位验证功能，后期再找模型
- **Phase 3 增强**: 是否值得投入时间做唇形同步和环境光美颜？优先级对比当前其他任务。

### 推荐路径
**天赐自主决策**: 建议先走 Phase 1（1h内完成），用 AvatarSample 占位模型验证整条 VRM 渲染链路通断。如果通了，再问天赐要不要推进 Phase 2 定制模型。

---

## 七、附录：涉及文件速查

| 文件 | 作用 | 修改需求 |
|:---|:-----|:---------|
| `packages/core-character/src/male-characters.ts` | 角色注册（类型/Live2D/VRM配置） | **必须改**: 追加 VRM 类型条目 |
| `apps/stage-web/src/components/MaleCharacterGrid.vue` | 角色选择网格 + VRM预览触发 | **必须改**: 修复 idle 动画导入、确认 isVRM 逻辑 |
| `apps/stage-web/src/components/MaleCharacterVRMScene.vue` | VRM 渲染引擎（Three.js 场景） | **不改**: 已完成且功能正常 |
| `packages/stage-ui-three/src/composables/vrm/loader.ts` | VRM GLTF 加载器（MToon/outline） | **不改**: 功能完整 |
| `packages/stage-ui-three/src/composables/vrm/core.ts` | VRM 核心加载逻辑（骨架优化/朝向/BBOX） | **不改**: 功能完整 |
| `apps/stage-web/vite.config.ts` | Vite 配置（alias/下载/缓存） | **可能改**: 如需要加 `@proj-airi/stage-ui-three/assets` alias |
| `packages/stage-ui-three/package.json` | exports map | **可能改**: 如需要暴露 assets 子路径 |
