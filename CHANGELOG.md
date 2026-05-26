# 更新日志

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 待发布的新功能

---

## [1.2.0] - 2026-05-27

### 修复
- 修复供应商列表显示问题（API返回 `data.data` 而非 `data.providers`）
- 修复供应商选中状态更新逻辑（改为基于 `data-id` 属性）
- 修复模型映射字段与 API 结构不匹配问题

### 优化
- 替换 `prompt()` 弹窗为预设供应商选择模态框
- 模型映射以表格形式展示（Primary/Light/Balanced/Strongest）
- 简化按钮文案，去除冗余 emoji
- 代码审查和测试流程完善

### 技术债务
- 统一代码风格，减少 AI 生成痕迹

---

## [1.1.0] - 2026-05-25

### 新增
- AI 供应商管理（参考 CC Switch 设计）
- 4 层模型映射（primary/light/balanced/strongest）
- 看板趋势折线图和占比饼图

### 修复
- 修复 Windows 终端中文输出乱码

### 优化
- 添加 python-dotenv 自动加载 .env
- 前端搜索输入防抖（300ms）

---

## [1.0.0] - 2026-05-21

### 新增
- 智能翻译模块
- 合规审核模块
- 视觉识别模块
- 知识库模块
- 推荐引擎
- 数据看板
- 用户权限管理

---

[Unreleased]: https://github.com/2187262974-cmd/ccae-engine/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/2187262974-cmd/ccae-engine/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/2187262974-cmd/ccae-engine/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/2187262974-cmd/ccae-engine/releases/tag/v1.0.0
