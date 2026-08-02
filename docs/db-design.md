# 数据库设计（初稿）

对应 PRD V1.1（10 大功能模块）。设计原则：第三范式（3NF）、敏感数据加密存储、全表软删除（`is_deleted`）、审计溯源（`created_at/updated_at` + 操作日志）。

## 一、表清单

| 表名 | 对应模块 | 说明 |
| --- | --- | --- |
| users | M1 | 统一账号，角色唯一绑定 |
| doctor_profiles / student_profiles / patient_profiles | M1 | 分角色差异化注册信息 |
| conversations | M5 | 问诊会话（状态机：进行中→已结束） |
| messages | M5 | 多类型消息（含互转文本/合成语音） |
| medical_histories | M6 | 病史（家族/过敏/既往），带版本号溯源 |
| consultation_summaries | M3/M7 | 问诊总结（状态机：草稿→待审核→已通过/已驳回） |
| consultation_records | M6 | 诊疗记录归档（总结审核通过后自动生成） |
| training_plans | M3/M7 | 实训计划（独立审核流） |
| plan_todos | M3 | 计划待办 |
| review_records | M7 | 审核记录（留痕，不可修改） |
| score_records | M2/M7 | 实训评分（百分制四维 + 等级） |
| health_reminders | M8 | 健康提醒（类型/周期/cron 调度） |
| reminder_logs | M8 | 提醒发送与患者反馈记录 |
| health_data | M4/M6 | 血压/血糖/体重健康数据 |
| medication_logs | M4 | 用药记录（时间轴） |
| voice_translations | M9 | 语音互转记录（双语文本、术语命中、置信度） |
| audit_logs | 全模块 | 操作日志（登录/审核/评分/导出/越权尝试等） |

## 二、关键表结构

### users（用户表）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 用户ID |
| phone | varchar(20) | 唯一，可空 | 手机号 |
| email | varchar(100) | 唯一，可空 | 邮箱 |
| password_hash | varchar(255) | 非空 | bcrypt 哈希 |
| role | varchar(20) | 非空 | doctor/student/patient/admin（唯一绑定） |
| status | varchar(20) | 非空 | pending/active/rejected/disabled |
| name | varchar(50) | 非空 | 姓名 |
| reject_reason | varchar(500) | 可空 | 审核驳回原因 |
| last_login_at | datetime | 可空 | 最近登录时间 |
| is_deleted | tinyint(1) | 默认0 | 软删除 |
| created_at / updated_at | datetime | 非空 | 时间戳 |

### conversations（问诊会话）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 会话ID |
| patient_id | int | 索引 | 患者 |
| student_id | int | 可空，索引 | 医学生 |
| doctor_id | int | 可空，索引 | 介入/直接问诊医生 |
| status | varchar(20) | 非空 | active/ended |
| ended_at | datetime | 可空 | 结束时间 |
| end_requester_id / end_confirm_id | int | 可空 | 结束请求/确认方（双方确认规则） |
| summary_triggered | tinyint(1) | 默认0 | 已触发总结填报 |

### messages（消息）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 消息ID |
| conversation_id | int | 索引（+created_at 复合） | 会话 |
| sender_id / sender_role | int/varchar | 索引 | 发送者 |
| msg_type | varchar(20) | 非空 | text/image/voice/file/system |
| content | text | 可空 | 文本/URL |
| translated_text | text | 可空 | 互转目标语言文本 |
| target_audio_url | varchar(500) | 可空 | 合成语音 URL |
| status | varchar(20) | 默认 sent | sent/failed |
| read_at | datetime | 可空 | 已读时间 |

### consultation_summaries（问诊总结）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 总结ID |
| conversation_id | int | 唯一 | 一会话一总结 |
| student_id | int | 索引 | 医学生 |
| chief_complaint | varchar(200) | 非空 | 主诉（≤100字，标准化校验） |
| present_illness / past_illness / consultation_process / treatment_advice | text | — | 结构化内容 |
| initial_diagnosis | varchar(300) | 非空 | 初步判断 |
| status | varchar(20) | 非空 | draft/pending/passed/rejected |
| review_comment / reviewed_by / reviewed_at | — | 可空 | 审核信息 |

### score_records（实训评分）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 评分ID |
| student_id | int | 索引 | 医学生 |
| q_consultation / q_history / q_communication / q_summary | int | 非空 | 四维得分 |
| total | int | 非空 | 百分制总分 |
| grade | varchar(10) | 非空 | 优秀≥90/良好80-89/合格60-79/不合格<60 |
| comment | text | 非空 | 评语 |

### health_reminders（健康提醒）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 提醒ID |
| patient_id | int | 索引 | 患者 |
| creator_id / creator_role | — | 非空 | 创建者（医生/医学生） |
| reminder_type | varchar(20) | 非空 | medication/measurement/follow_up/lifestyle |
| content / detail | text | — | 内容与扩展信息 |
| cycle | varchar(20) | 非空 | once/daily/weekly/monthly |
| schedule_cron | varchar(100) | 非空 | 调度表达式 |
| start_date / end_date | datetime | 可空 | 生效区间 |
| status | varchar(20) | 非空 | active/ended/paused |
| push_enabled | tinyint(1) | 默认1 | 推送开关 |

### voice_translations（语音互转）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | bigint | PK | 记录ID |
| message_id | int | 可空 | 关联消息 |
| source_lang / target_lang | varchar(10) | 非空 | zh/yi |
| source_text / target_text | text | 可空 | 双语文本 |
| source_audio_url / target_audio_url | varchar(500) | 可空 | 语音文件 |
| confidence | float | 可空 | 识别置信度 |
| term_hit_count | int | 默认0 | 医疗术语命中数 |
| status | varchar(20) | 非空 | success/failed/degraded |

## 三、索引与性能设计

1. `messages(conversation_id, created_at)` 复合索引支撑历史消息分页拉取；文本检索走 Elasticsearch 全文索引（消息 content、档案内容），不依赖 MySQL LIKE。
2. 统计类查询基于 `created_at` 范围聚合，数据量增长后切换为聚合表/宽表（Celery 预聚合），不破坏 3NF。
3. `users(phone)`、`users(email)` 唯一索引保证注册唯一性。

## 四、数据安全与溯源

1. 密码 bcrypt 哈希存储；患者敏感字段（身份证号、手机号、病历内容）应用层加密，展示脱敏。
2. 全部业务表支持软删除；`audit_logs` 记录登录、注册、审核、评分、档案修改、数据导出、越权尝试等操作，留存 ≥ 3 年。
3. 健康数据越界校验阈值（血压/血糖/体重合理范围）在应用层校验（PRD 6.4.6 规则 3）。

## 五、迁移与初始化

- 使用 Alembic 管理 schema 迁移（`backend/alembic`），首版迁移由 `alembic revision --autogenerate` 生成。
- 种子数据：管理员账号、术语词典（语音模块）、审核要点配置（后续接入配置表）。
