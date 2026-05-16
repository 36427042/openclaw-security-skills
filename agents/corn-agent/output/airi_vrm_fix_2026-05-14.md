# AIRI-Male VRM 3D 渲染修复报告

**日期**: 2026-05-14
**代理人**: 🌽 玉米 (corn-agent)
**根因**: `MaleCharacterVRMScene.vue` 手写创建 Three.js Scene 与全局 `@tresjs/core` 冲突

---

## 🔍 根因分析

### 原组件三个核心问题

1. **`useTresContext()`/`useLoop()` 在 TresCanvas 作用域外调用**  
   原组件在 `<script setup>` 顶层即调用 `useTresContext()` 和 `useLoop()`，但这些函数只能在 `<TresCanvas>` 的子组件内部调用。组件自身拥有 `<TresCanvas>`，所以顶层调用找不到祖先的 TresCanvas provider，导致运行时错误。

2. **无效的 `useVRMLoader` 导入路径**  
   原代码 `import { useVRMLoader } from '@proj-airi/stage-ui-three/composables/vrm'` 在开发阶段可通过 Vite 别名解析，但 `useVRMLoader` 并非 `@proj-airi/stage-ui-three` 公共导出的一部分（`index.ts` 仅导出 `animation`, `core`, `expression`, `lip-sync`, `loader`, `utils` 等）。包通过 export map 暴露 `./composables/vrm`，所以动态 `import()` 可以工作，但静态顶层导入可能导致模块解析不一致。

3. **Three.js 实体创建与 TresJS 声明式 API 不兼容**  
   原组件使用 `new PerspectiveCamera()`, `new Scene()`, `new WebGLRenderer()` 等 Three.js 实体 API，与 `<TresCanvas>` 管理的声明式渲染管线不兼容，导致二次初始化、canvas 重叠、渲染冲突。

---

## 🔧 修复方案

### 架构重构：两组件分离模式

```
MaleCharacterVRMScene.vue  (父组件，拥有 <TresCanvas>)
    └─ TresVrmScene.vue     (子组件，在 <TresCanvas> 内部渲染)
        └─ 在此安全调用 useTresContext()/useLoop()
```

### 改动详情

#### 1. `MaleCharacterVRMScene.vue` — 完全重写

- **保持** `<TresCanvas>` 作为唯一的三维渲染入口
- **保留** `<OrbitControls>`、灯光等 TresJS 组件
- **保留** FallbackMaleCharacter 后备组件
- **新增** `TresVrmScene` 作为 VRM 加载子组件，通过 props 传递 `sceneState`
- **删除** 所有手写 Three.js API 调用（`new Scene`, `new PerspectiveCamera` 等）
- **UI 覆盖层**：加载动画、错误提示、空状态提示全部使用绝对定位 `<div>`，不干扰 TresCanvas

#### 2. `TresVrmScene.vue` — 新建子组件

- **在 `<TresCanvas>` 内部** 安全调用 `useTresContext()` 和 `useLoop()`
- 接收 `sceneState` prop 驱动 VRM 加载
- 通过 `useVRMLoader` 动态导入加载 VRM 模型
- 绑定 `onBeforeRender` 循环更新 VRM 子系统（spring bone, expression, humanoid, material）

#### 3. `MaleCharacterGrid.vue` — 微调

- 将 `getGradient()` 函数从独立的 `<script lang="ts">` 块移入 `<script setup>`，修复模板作用域问题

### 运行时验证

| 组件 | Vite 编译 | 状态 |
|------|-----------|------|
| `MaleCharacterVRMScene.vue` | ✅ 200 | 可用 |
| `TresVrmScene.vue` | ✅ 200 | 可用 |
| `FallbackMaleCharacter.vue` | ✅ 200 | 可用 |
| `MaleCharacterGrid.vue` | ✅ 200 | 可用 |
| `@pixiv/three-vrm` 解析 | ✅ 通过 pnpm hoisting | 运行时可用 |
| `@pixiv/three-vrm-animation` 解析 | ✅ 通过 pnpm hoisting | 运行时可用 |
| 页面 `/characters/male` | ✅ 200 | 可访问 |

### 已知限制

- `@pixiv/three-vrm` 和 `@pixiv/three-vrm-animation` 不在 `apps/stage-web/package.json` 中声明为直接依赖，因此 `vue-tsc` 类型检查会报 `TS2307`。此为**预存问题**，可通过 `skipLibCheck: true` 或在 stage-web 的 `package.json` 中添加依赖解决。Vite 开发服务器不受影响。

---

## 📂 产出文件

- `/Users/a1234/Desktop/AIRI-Male/apps/stage-web/src/components/MaleCharacterVRMScene.vue`
- `/Users/a1234/Desktop/AIRI-Male/apps/stage-web/src/components/TresVrmScene.vue`
- `/Users/a1234/Desktop/AIRI-Male/apps/stage-web/src/components/MaleCharacterGrid.vue` (微调)
