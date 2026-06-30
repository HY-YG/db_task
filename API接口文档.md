# API 接口文档

本文档依据当前项目后端 `backend/routers` 的真实路由整理。

## 1. 基本说明

### 1.1 基础地址

```text
http://localhost:8000
```

统一前缀：`/api`

### 1.2 统一返回结构

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 1.3 鉴权说明

- 认证接口中，`/api/auth/me`、`/api/auth/logout`、`/api/auth/password` 需要在请求头中携带：

```http
Authorization: Bearer <token>
```

- 其他接口当前主要通过业务参数传递 `user_id`，并未统一接入 Bearer Token 校验。

## 2. 基础接口

### 2.1 服务根路径

- 方法：`GET`
- 路径：`/`
- 功能描述：返回后端服务欢迎信息。

## 3. 认证接口

### 3.1 注册

- 方法：`POST`
- 路径：`/api/auth/register`
- 功能描述：注册学生或教师账号，并返回登录令牌与用户信息。
- 请求体关键字段：
  - `username`：3-50 位用户名
  - `password`：6-50 位密码
  - `name`：姓名
  - `gender`：可选
  - `age`：可选，0-150
  - `role_name`：仅支持 `学生` 或 `教师`

### 3.2 登录

- 方法：`POST`
- 路径：`/api/auth/login`
- 功能描述：用户名密码登录，返回令牌与用户信息。
- 请求体关键字段：
  - `username`
  - `password`

### 3.3 获取当前用户

- 方法：`GET`
- 路径：`/api/auth/me`
- 功能描述：根据 Bearer Token 返回当前登录用户信息。

### 3.4 登出

- 方法：`POST`
- 路径：`/api/auth/logout`
- 功能描述：删除当前用户的令牌记录。

### 3.5 修改密码

- 方法：`PUT`
- 路径：`/api/auth/password`
- 功能描述：校验旧密码后修改当前用户密码。
- 请求体关键字段：
  - `old_password`
  - `new_password`

## 4. 用户与角色接口

### 4.1 用户接口

- 方法：`POST`
- 路径：`/api/user/add`
- 功能描述：新增用户基础资料。

- 方法：`GET`
- 路径：`/api/user/list`
- 功能描述：获取用户列表。

- 方法：`GET`
- 路径：`/api/user/detail/{user_id}`
- 功能描述：按用户 ID 获取用户详情。

- 方法：`PUT`
- 路径：`/api/user/update/{user_id}`
- 功能描述：按用户 ID 更新用户信息。

- 方法：`DELETE`
- 路径：`/api/user/delete/{user_id}`
- 功能描述：按用户 ID 删除用户。

### 4.2 角色接口

- 方法：`POST`
- 路径：`/api/role/add`
- 功能描述：新增角色。

- 方法：`GET`
- 路径：`/api/role/list`
- 功能描述：获取角色列表。

- 方法：`GET`
- 路径：`/api/role/detail/{role_id}`
- 功能描述：按角色 ID 获取角色详情。

- 方法：`PUT`
- 路径：`/api/role/update/{role_id}`
- 功能描述：按角色 ID 更新角色信息。

- 方法：`DELETE`
- 路径：`/api/role/delete/{role_id}`
- 功能描述：按角色 ID 删除角色。

## 5. 课程与资源接口

### 5.1 课程接口

- 方法：`POST`
- 路径：`/api/course/add`
- 功能描述：创建课程；当请求体包含 `teacher_user_id` 且该用户为教师时，会自动补齐授课关系。
- 请求体关键字段：
  - `course_name`
  - `class_time`
  - `course_intro`
  - `teacher_user_id`

- 方法：`GET`
- 路径：`/api/course/list`
- 功能描述：获取课程列表。

- 方法：`GET`
- 路径：`/api/course/detail/{course_id}`
- 功能描述：按课程 ID 获取课程详情。

- 方法：`GET`
- 路径：`/api/course/overview/{user_id}`
- 功能描述：获取某个用户的课程概览聚合数据，包含章节数、资源数、作业数、选课状态和进度百分比。

- 方法：`GET`
- 路径：`/api/course/detail-bundle/{course_id}?user_id={user_id}`
- 功能描述：获取课程详情页聚合数据，包含课程、选课关系、章节、资源、作业、最近笔记和学习进度。

- 方法：`GET`
- 路径：`/api/course/management-bundle`
- 功能描述：获取课程管理页聚合数据。
- 查询参数：
  - `user_id`：可选；传入教师 ID 时，仅返回该教师负责的课程、章节与资源

- 方法：`PUT`
- 路径：`/api/course/update/{course_id}`
- 功能描述：按课程 ID 更新课程信息。

- 方法：`DELETE`
- 路径：`/api/course/delete/{course_id}`
- 功能描述：按课程 ID 删除课程。

### 5.2 章节接口

- 方法：`POST`
- 路径：`/api/course/chapter/add`
- 功能描述：创建课程章节。

- 方法：`GET`
- 路径：`/api/course/chapter/list`
- 功能描述：获取章节列表。
- 查询参数：
  - `course_id`：可选

- 方法：`GET`
- 路径：`/api/course/chapter/detail/{chapter_id}`
- 功能描述：按章节 ID 获取章节详情。

- 方法：`PUT`
- 路径：`/api/course/chapter/update/{chapter_id}`
- 功能描述：按章节 ID 更新章节信息。

- 方法：`DELETE`
- 路径：`/api/course/chapter/delete/{chapter_id}`
- 功能描述：按章节 ID 删除章节。

### 5.3 资源接口

- 方法：`POST`
- 路径：`/api/course/resource/add`
- 功能描述：创建课程资源。

- 方法：`GET`
- 路径：`/api/course/resource/list`
- 功能描述：获取资源列表。
- 查询参数：
  - `chapter_id`：可选

- 方法：`GET`
- 路径：`/api/course/resource/detail/{resource_id}`
- 功能描述：按资源 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/course/resource/update/{resource_id}`
- 功能描述：按资源 ID 更新资源信息。

- 方法：`DELETE`
- 路径：`/api/course/resource/delete/{resource_id}`
- 功能描述：按资源 ID 删除资源。

### 5.4 资源版本接口

- 方法：`POST`
- 路径：`/api/course/resource/version/add`
- 功能描述：创建资源版本记录。

- 方法：`GET`
- 路径：`/api/course/resource/version/list`
- 功能描述：获取资源版本列表。
- 查询参数：
  - `resource_id`：可选

- 方法：`GET`
- 路径：`/api/course/resource/version/detail/{version_id}`
- 功能描述：按版本 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/course/resource/version/update/{version_id}`
- 功能描述：按版本 ID 更新资源版本信息。

- 方法：`DELETE`
- 路径：`/api/course/resource/version/delete/{version_id}`
- 功能描述：按版本 ID 删除资源版本记录。

### 5.5 标签接口

- 方法：`POST`
- 路径：`/api/course/tag/add`
- 功能描述：创建标签。

- 方法：`GET`
- 路径：`/api/course/tag/list`
- 功能描述：获取标签列表。

- 方法：`GET`
- 路径：`/api/course/tag/detail/{tag_id}`
- 功能描述：按标签 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/course/tag/update/{tag_id}`
- 功能描述：按标签 ID 更新标签。

- 方法：`DELETE`
- 路径：`/api/course/tag/delete/{tag_id}`
- 功能描述：按标签 ID 删除标签。

### 5.6 资源标签关联接口

- 方法：`POST`
- 路径：`/api/course/resource/tag/add`
- 功能描述：新增资源与标签的关联关系。

- 方法：`GET`
- 路径：`/api/course/resource/tag/list`
- 功能描述：查询资源标签关系列表。
- 查询参数：
  - `resource_id`：可选
  - `tag_id`：可选

- 方法：`DELETE`
- 路径：`/api/course/resource/tag/delete`
- 功能描述：删除指定资源与标签的关联关系。
- 查询参数：
  - `resource_id`
  - `tag_id`

### 5.7 授课关系接口

- 方法：`POST`
- 路径：`/api/course/teaching/add`
- 功能描述：新增授课关系。

- 方法：`GET`
- 路径：`/api/course/teaching/list`
- 功能描述：获取授课关系列表。
- 查询参数：
  - `user_id`：可选

### 5.8 选课关系接口

- 方法：`POST`
- 路径：`/api/course/enrollment/add`
- 功能描述：新增选课关系。

- 方法：`GET`
- 路径：`/api/course/enrollment/list`
- 功能描述：获取选课关系列表。
- 查询参数：
  - `user_id`：可选
  - `course_id`：可选

## 6. 学习模块接口

### 6.1 笔记接口

- 方法：`POST`
- 路径：`/api/learning/note/add`
- 功能描述：创建学习笔记。

- 方法：`GET`
- 路径：`/api/learning/note/list`
- 功能描述：获取学习笔记列表。
- 查询参数：
  - `user_id`：可选
  - `course_id`：可选

- 方法：`GET`
- 路径：`/api/learning/note/detail/{note_id}`
- 功能描述：按笔记 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/learning/note/update/{note_id}`
- 功能描述：按笔记 ID 更新内容。

- 方法：`DELETE`
- 路径：`/api/learning/note/delete/{note_id}`
- 功能描述：按笔记 ID 删除笔记。

### 6.2 学习计划接口

- 方法：`POST`
- 路径：`/api/learning/plan/add`
- 功能描述：创建学习计划。

- 方法：`GET`
- 路径：`/api/learning/plan/list`
- 功能描述：获取学习计划列表。
- 查询参数：
  - `user_id`：可选

- 方法：`GET`
- 路径：`/api/learning/plan/detail/{plan_id}`
- 功能描述：按计划 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/learning/plan/update/{plan_id}`
- 功能描述：按计划 ID 更新学习计划。

- 方法：`DELETE`
- 路径：`/api/learning/plan/delete/{plan_id}`
- 功能描述：按计划 ID 删除学习计划。

### 6.3 通知接口

- 方法：`POST`
- 路径：`/api/learning/notification/add`
- 功能描述：创建单条用户通知。

- 方法：`POST`
- 路径：`/api/learning/notification/publish-course`
- 功能描述：向某门课程的所有选课学生批量发布课程通知。
- 请求体关键字段：
  - `sender_user_id`
  - `course_id`
  - `notification_content`

- 方法：`GET`
- 路径：`/api/learning/notification/sent-course`
- 功能描述：按教师和课程查看已发送课程通知的聚合记录。
- 查询参数：
  - `sender_user_id`
  - `course_id`

- 方法：`GET`
- 路径：`/api/learning/notification/list`
- 功能描述：获取通知列表。
- 查询参数：
  - `user_id`：可选

- 方法：`GET`
- 路径：`/api/learning/notification/detail/{notification_id}`
- 功能描述：按通知 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/learning/notification/update/{notification_id}`
- 功能描述：更新通知内容或已读状态。

- 方法：`DELETE`
- 路径：`/api/learning/notification/delete/{notification_id}`
- 功能描述：删除单条通知。

- 方法：`POST`
- 路径：`/api/learning/notification/delete-course-batch`
- 功能描述：按课程通知内容批量删除课程通知记录。
- 请求体关键字段：
  - `sender_user_id`
  - `course_id`
  - `notification_content`

### 6.4 学习进度接口

- 方法：`POST`
- 路径：`/api/learning/progress/upsert`
- 功能描述：新增或更新学习进度。
- 请求体关键字段：
  - `user_id`
  - `course_id`
  - `progress_type`：仅支持 `chapter`、`resource`、`assignment`
  - `target_id`
  - `progress_status`
  - `completed_at`
- 说明：当 `progress_type=resource` 时，接口会自动检查同章节下资源是否全部完成，并同步更新章节进度。

- 方法：`GET`
- 路径：`/api/learning/progress/list`
- 功能描述：获取学习进度列表。
- 查询参数：
  - `user_id`：可选
  - `course_id`：可选
  - `progress_type`：可选

- 方法：`PUT`
- 路径：`/api/learning/progress/update/{progress_id}`
- 功能描述：按进度 ID 更新学习进度状态。

## 7. 作业模块接口

### 7.1 作业接口

- 方法：`POST`
- 路径：`/api/assignment/add`
- 功能描述：创建作业。

- 方法：`GET`
- 路径：`/api/assignment/list`
- 功能描述：获取作业列表。
- 查询参数：
  - `course_id`：可选

- 方法：`GET`
- 路径：`/api/assignment/dashboard/{user_id}`
- 功能描述：获取作业看板聚合数据，包含课程信息、提交记录、进度状态和是否已选课。
- 查询参数：
  - `course_id`：可选

- 方法：`GET`
- 路径：`/api/assignment/detail/{assignment_id}`
- 功能描述：按作业 ID 获取详情。

- 方法：`PUT`
- 路径：`/api/assignment/update/{assignment_id}`
- 功能描述：按作业 ID 更新作业信息。

- 方法：`DELETE`
- 路径：`/api/assignment/delete/{assignment_id}`
- 功能描述：按作业 ID 删除作业。

### 7.2 作业提交接口

- 方法：`POST`
- 路径：`/api/assignment/submission/add/{assignment_id}`
- 功能描述：为指定作业新增提交记录。
- 请求体关键字段：
  - `user_id`
  - `submission_status`
  - `submitted_at`
  - `submission_content`
  - `teacher_feedback`
  - `score`
  - `reviewed_at`

- 方法：`GET`
- 路径：`/api/assignment/submission/list/{assignment_id}`
- 功能描述：获取指定作业的提交列表。
- 查询参数：
  - `user_id`：可选

- 方法：`PUT`
- 路径：`/api/assignment/submission/update/{submission_id}`
- 功能描述：更新作业提交记录或教师批改信息。

- 方法：`DELETE`
- 路径：`/api/assignment/submission/delete/{submission_id}`
- 功能描述：删除作业提交记录。

## 8. AI 模块接口

### 8.1 AI 会话接口

- 方法：`POST`
- 路径：`/api/ai/session/add`
- 功能描述：创建 AI 会话。

- 方法：`GET`
- 路径：`/api/ai/session/list`
- 功能描述：获取 AI 会话列表。
- 查询参数：
  - `user_id`：可选

- 方法：`PUT`
- 路径：`/api/ai/session/update/{session_id}`
- 功能描述：更新会话状态。

- 方法：`DELETE`
- 路径：`/api/ai/session/delete/{session_id}`
- 功能描述：删除 AI 会话。

### 8.2 AI 消息接口

- 方法：`POST`
- 路径：`/api/ai/message/add`
- 功能描述：创建 AI 消息记录。
- 请求体关键字段：
  - `session_id`
  - `sender`
  - `message_content`：结构化 JSON

- 方法：`GET`
- 路径：`/api/ai/message/list`
- 功能描述：获取 AI 消息列表。
- 查询参数：
  - `session_id`：可选

### 8.3 学习教练接口

- 方法：`POST`
- 路径：`/api/ai/coach/start`
- 功能描述：启动学习教练流程。
- 请求体关键字段：
  - `session_id`
  - `user_id`
  - `course_id`

- 方法：`POST`
- 路径：`/api/ai/coach/next`
- 功能描述：推进学习教练流程到下一阶段。
- 请求体关键字段：
  - `session_id`
  - `user_id`
  - `message`

### 8.4 资源上传与向量化接口

- 方法：`POST`
- 路径：`/api/ai/upload`
- 功能描述：上传课程资源文件并自动创建资源及版本信息。
- 请求类型：`multipart/form-data`
- 表单字段：
  - `chapter_id`
  - `file`
  - `resource_title`
  - `version_description`

- 方法：`POST`
- 路径：`/api/ai/vectorize`
- 功能描述：对指定资源执行向量化。
- 请求体关键字段：
  - `resource_id`

### 8.5 课程问答与聊天接口

- 方法：`POST`
- 路径：`/api/ai/qa`
- 功能描述：基于课程资料进行问答，可选回写会话消息。
- 请求体关键字段：
  - `question`
  - `user_id`
  - `course_id`
  - `session_id`
  - `top_k`

- 方法：`POST`
- 路径：`/api/ai/chat`
- 功能描述：普通会话聊天接口，自动写入用户和 AI 消息，并返回工具调用结果及上下文。
- 请求体关键字段：
  - `session_id`
  - `user_id`
  - `message`
  - `course_id`
  - `top_k`

- 方法：`POST`
- 路径：`/api/ai/assistant/chat`
- 功能描述：统一 AI 助手接口，可返回回答模式、是否需要个人信息授权、工具调用结果和上下文。
- 请求体关键字段：
  - `session_id`
  - `user_id`
  - `message`
  - `course_id`
  - `top_k`
  - `confirm_personal_context`

## 9. 管理接口

### 9.1 健康检查

- 方法：`GET`
- 路径：`/api/admin/health`
- 功能描述：返回服务健康状态。
