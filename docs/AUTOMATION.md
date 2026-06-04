# 自动运行说明

## 当前是否可以自动运行

可以。

当前项目已经支持命令行自动采集。你只需要给交易日期，脚本会自动完成取数、保存文件、生成复盘草稿。

目前默认状态是“手动触发脚本”。要变成真正定时，需要配置本机定时任务或 GitHub Actions。

示例：

```bash
scripts/run_daily.sh 2026-06-02
```

## 脚本入口

```text
scripts/run_daily.sh
```

它内部会调用：

```text
tools/collect_daily_data.py
```

## 手动运行

在项目根目录执行：

```bash
scripts/run_daily.sh 2026-06-02
```

不传日期时，脚本默认使用当天日期：

```bash
scripts/run_daily.sh
```

## macOS 定时运行

可以用 `cron`。例如每个交易日下午 15:20 执行：

```cron
20 15 * * 1-5 cd /path/to/A股复盘 && /bin/zsh scripts/run_daily.sh >> logs/cron.log 2>&1
```

第一次使用前先创建日志目录：

```bash
mkdir -p logs
```

配置步骤：

1. 打开定时任务编辑器：

```bash
crontab -e
```

2. 写入类似下面这一行，把路径换成你的真实项目路径：

```cron
20 15 * * 1-5 cd /Users/admin/Desktop/obsidian/valut1/A股复盘 && /bin/zsh scripts/run_daily.sh >> logs/cron.log 2>&1
```

3. 保存后，工作日下午 15:20 会自动运行。

说明：

- `1-5` 表示周一到周五。
- 节假日不会自动识别，后续可以结合交易日历再优化。
- 日志在 `logs/cron.log`。

## Linux 服务器定时运行

服务器更推荐使用 `systemd timer`。模板和说明见：

```text
docs/DEPLOYMENT.md
deploy/systemd/
```

## GitHub Actions

如果发布到 GitHub，也可以用 GitHub Actions 定时跑。

项目已内置：

```text
.github/workflows/daily-collect.yml
```

它会在工作日定时运行，也支持在 GitHub 页面手动触发。采集结果会作为 artifact 上传，不会自动提交到仓库。

不过要注意：

- 公共数据接口可能限制请求频率。
- GitHub Actions 的网络环境和你本机不同，东方财富或新浪源不一定都稳定。
- 如果你不想把采集结果提交到仓库，就不要在 Actions 里自动 commit 数据文件。

## 失败处理

脚本默认会继续运行，把失败接口写入：

```text
data/raw/日期/errors.json
```

如果你希望失败时直接中断，可以加 `--strict`：

```bash
PYTHONPATH=tools python3 tools/collect_daily_data.py 2026-06-02 --out-dir . --allow-insecure --strict
```
