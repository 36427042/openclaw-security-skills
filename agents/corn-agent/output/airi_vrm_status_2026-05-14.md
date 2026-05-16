# AIRI-Male VRM 3D 渲染状态报告

**日期**: 2026-05-14 21:45 (Asia/Shanghai)
**项目路径**: `~/Desktop/AIRI-Male/`

---

## ✅ 当前状态：正常运行

### Vite Dev Server
- **端口**: `:5173`（已重启并正常运行）
- **路由**: `/characters/male` → MaleCharacterGrid 页面 ✅（200 OK）
- **根路径**: `/` → AIRI 主页 ✅（200 OK）

### 问题与修复
**问题**: 旧进程（PID 34229）的 Vite dev server 在终端断开后处于"僵尸"状态，返回 404
**修复**: 已清除旧进程，重新启动 `pnpm dev:web`，服务正常可用

### VRM 模型文件
| 模型 | 路径 | 状态 |
|------|------|------|
| AvatarSample_A.vrm | `packages/stage-ui/src/assets/vrm/models/AvatarSample-A/` | ✅ 存在 |
| AvatarSample_B.vrm | `packages/stage-ui/src/assets/vrm/models/AvatarSample-B/` | ✅ 存在 |
| 已构建的 VRM | `apps/stage-web/dist/assets/AvatarSample_A-BNRNjuVT.vrm` | ✅ 存在 |
| 已构建的 VRM | `apps/stage-web/dist/assets/AvatarSample_B-Cgr_Y5fe.vrm` | ✅ 存在 |
| idle_loop.vrma | `packages/stage-ui-three/src/assets/vrm/animations/idle_loop.vrma` | ✅ 存在 |

### 组件架构
- **`MaleCharacterVRMScene.vue`** → 核心 3D VRM 渲染组件
  - 位置: `apps/stage-web/src/components/MaleCharacterVRMScene.vue`
  - 使用 `@pixiv/three-vrm` + Three.js 加载和渲染 VRM
  - 支持镜头自动追踪、OrbitControls 交互、角色动画
  - 支持加载 `.vrma` idle 动画（当前因 workspace exports map 限制暂未启用）
  
- **`MaleCharacterGrid.vue`** → 角色网格容器
  - 位置: `apps/stage-web/src/components/MaleCharacterGrid.vue`
  - 显示 5 个男性角色（alexander, haruto, jihoon, moran, kai）
  - 每个角色卡片支持点击查看 3D VRM 预览
  - 支持注册角色到 character store

- **`pages/characters/male.vue`** → 路由页面
  - 位置: `apps/stage-web/src/pages/characters/male.vue`
  - 集成 MaleCharacterGrid 组件

### 依赖情况
- `@pixiv/three-vrm` ^3.5.2 ✅
- `@pixiv/three-vrm-animation` ^3.5.2 ✅
- `@proj-airi/stage-ui-three` workspace package ✅
- `@proj-airi/core-character` workspace package ✅
- VRM loader composable: `packages/stage-ui-three/src/composables/vrm/loader.ts` ✅

### 页面路由
- `/characters/male` → AIRI-Male 角色网格 + VRM 3D 预览
- `[...all].vue` → Catch-all 404 页面（显示 "Where are we?"）

### VRM 加载逻辑（MaleCharacterVRMScene.vue）
1. 组件挂载时初始化 Three.js 场景（透明背景）
2. 设置灯光（环境光 + 半球光 + 方向光 + 补光）
3. 设置 PerspectiveCamera + OrbitControls
4. 调用 `useVRMLoader()` 异步加载 VRM 模型
5. 优化 VRM（移除多余顶点，合并骨骼）
6. 计算 bounding box 自动定位相机
7. 若提供 `.vrma` 则加载 idle animation
8. 动画循环持续渲染

### 注意事项
- idle 动画 `.vrma` 文件当前未启用（`idleLoopVrmaUrl` 设置为 `undefined`）
  - 文件存在于 `packages/stage-ui-three/src/assets/vrm/animations/idle_loop.vrma`
  - 要启用需要将其加入 `@proj-airi/stage-ui-three` 的 package.json exports 或添加 vite alias
- 所有 5 个角色当前使用 2 个 VRM 模型（AvatarSample_A 和 B）作为占位演示
- 服务已通过 `open http://localhost:5173/characters/male` 在浏览器打开

---

## 下一步建议
1. 将 idle_loop.vrma 暴露在 package.json exports 中以启用角色 idle 动画
2. 为每个男性角色准备独立的 VRM 模型替换 AvatarSample 占位符
3. 移除 `VRM_MODEL_URLS` 中的重复映射（目前 5 个角色只用了 2 个模型）
