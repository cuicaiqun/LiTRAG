# Interview Kit

这是一套围绕当前 `rag-skill` 项目制作的静态多页面试作战包。

## 页面

- `index.html`：项目总览
- `resume.html`：简历写法
- `architecture.html`：架构拆解
- `modules.html`：模块细节
- `evidence.html`：亮点与证据
- `graph.html`：知识图谱
- `qa.html`：面试问答
- `drills.html`：速记与模拟

## 用法

直接双击 `index.html` 即可离线打开。

如果你更习惯本地服务，也可以在本目录下用任意静态文件服务启动，比如：

```powershell
python -m http.server 8899
```

然后访问 `http://127.0.0.1:8899/index.html`。

## 内容边界

- 页面中的“已实现”内容都基于当前仓库代码或已有输出。
- “下一步”内容单独标记为 roadmap。
- QA 最新报告的 fallback 边界已在页面里明确写出，不应在面试中包装成最新在线跑分成功。
