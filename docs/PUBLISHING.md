# 发布到 GitHub

## 发布前检查

建议确认：

- `README.md` 已经写清楚项目用途。
- `requirements.txt` 已经列出依赖。
- `.gitignore` 已经忽略生成数据和本地环境。
- 测试可以通过。
- 没有提交 token、cookie、账号、私密配置。
- `.github/workflows/ci.yml` 可以正常运行测试。
- 如果要开源，建议补一个 `LICENSE`，例如 MIT、Apache-2.0 或保留所有权利。

## 初始化仓库

如果这个目录还不是 Git 仓库：

```bash
cd A股复盘
git init
git add .
git commit -m "Initial A-share review data collector"
```

## 连接 GitHub

在 GitHub 创建空仓库后：

```bash
git remote add origin git@github.com:你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

## 建议不要提交的数据

默认 `.gitignore` 已经忽略：

```text
data/raw/
data/processed/
data/reports/
```

这些文件是每天生成的结果，不建议放进公共仓库。以后如果要展示样例，可以单独放一个小的 `examples/` 目录。

## 合规提示

README 里已经写了项目边界：

- 只整理公开数据。
- 不构成投资建议。
- 不做自动交易。
- 生成草稿需要人工复核。

发布前建议保留这些说明。
