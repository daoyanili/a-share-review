# 服务器部署说明

## 适合的部署方式

这个项目当前是命令行采集器，不需要常驻 Web 服务。

推荐部署方式：

1. 服务器安装 Python 环境。
2. 克隆仓库。
3. 安装依赖。
4. 用 `systemd timer` 或 `cron` 定时执行 `scripts/run_daily.sh`。

## 服务器准备

先安装基础环境：

```bash
dnf install -y git python3 python3-pip gcc python3-devel
```

如果安装依赖时报 `No matching distribution found for akshare`，通常是服务器默认 Python 太老。先看版本：

```bash
python3 --version
```

如果低于 Python 3.9，优先安装新版 Python：

```bash
dnf install -y python3.11 python3.11-pip python3.11-devel
```

然后用新版 Python 安装项目：

```bash
PYTHON_BIN=python3.11 bash deploy/install_server.sh
```

如果你的系统仓库里没有 `python3.11`，把终端报错发出来，再换下一种安装方式。

部署前建议先跑一次环境检查：

```bash
bash deploy/server_check.sh
```

如果你想判断服务器资源够不够，跑：

```bash
bash deploy/server_audit.sh
```

这个脚本会列出内存、磁盘、进程、服务、Docker 容器和主要数据源网络连通性。

```bash
git clone https://github.com/daoyanili/a-share-review.git a-share-review
cd a-share-review
bash deploy/install_server.sh
```

手动试跑：

```bash
./scripts/run_daily.sh 2026-06-02
```

也可以直接运行安装脚本：

```bash
bash deploy/install_server.sh
```

生成文件会在：

```text
data/raw/
data/processed/
data/reports/
```

## systemd 定时运行

项目提供模板：

```text
deploy/systemd/a-share-review.service
deploy/systemd/a-share-review.timer
```

推荐直接用安装脚本生成 systemd 配置，脚本会自动写入当前项目目录和运行用户：

```bash
sudo bash deploy/setup_systemd.sh "$(pwd)" root
```

如果后续不想用 `root` 跑采集，可以新建一个普通用户，再把上面命令最后的 `root` 换成那个用户名。

项目也保留了模板文件：

```text
deploy/systemd/a-share-review.service
deploy/systemd/a-share-review.timer
```

如果不用 `deploy/setup_systemd.sh`，才需要手动把 service 文件里的路径和用户改成服务器实际值。

还要确认服务器时区。如果服务器不是北京时间，可以执行：

```bash
timedatectl
```

如果你希望定时器按北京时间触发，可以把服务器时区设为上海：

```bash
sudo timedatectl set-timezone Asia/Shanghai
```

手动复制到 systemd：

```bash
sudo cp deploy/systemd/a-share-review.service /etc/systemd/system/
sudo cp deploy/systemd/a-share-review.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now a-share-review.timer
```

查看定时器：

```bash
systemctl list-timers a-share-review.timer
```

查看日志：

```bash
journalctl -u a-share-review.service -n 100 --no-pager
```

## cron 定时运行

也可以使用 cron：

```cron
20 15 * * 1-5 cd /path/to/a-share-review && /bin/bash scripts/run_daily.sh >> logs/cron.log 2>&1
```

## 部署注意事项

- 服务器时区不一定是北京时间，脚本默认使用 `Asia/Shanghai` 生成日期。
- 这个项目不是常驻服务，资源主要消耗发生在定时采集运行时。
- 建议至少保留 1GB 可用内存和 3GB 可用磁盘空间。
- 公共数据接口可能偶尔失败，失败项会写入 `data/raw/{trade_date}/errors.json`。
- 生成数据默认不建议提交到 GitHub。
- 如果服务器网络访问东方财富不稳定，行业和概念板块可能失败，但主流程不会中断。
- 如果希望任一接口失败时直接返回失败状态，可以在命令后加 `--strict`。
