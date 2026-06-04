# 连接服务器说明

## 你现在的连接状态

从截图看，你已经通过阿里云 Workbench 连上服务器了：

- 用户：`root`
- 服务器：阿里云 ECS
- 内网 IP：`172.30.0.138`
- 当前终端提示符：`[root@... ~]#`

这说明你已经可以直接在 Workbench 里执行部署命令。

## Workbench 连接

这是最简单的方式：

1. 打开阿里云 ECS 控制台。
2. 进入实例。
3. 点击“远程连接”。
4. 选择 Workbench。
5. 登录后看到 `root@...#` 就说明已连接。

Workbench 不一定需要你本地电脑能直接 SSH 到服务器，它走的是阿里云控制台通道。

## 本地 SSH 连接

如果你想从本地电脑连接，需要公网 IP、SSH 端口和登录方式。

常见命令：

```bash
ssh root@服务器公网IP
```

如果用密钥：

```bash
ssh -i /path/to/key.pem root@服务器公网IP
```

注意：

- 截图里的 `172.30.0.138` 是内网 IP，通常不能从你本地电脑直接连。
- 需要看 ECS 实例是否有公网 IP。
- 安全组需要放行 TCP 22 端口。
- 如果只用 Workbench 部署，可以暂时不用配置本地 SSH。

## 部署前先检查服务器

在服务器 Workbench 终端里运行：

```bash
curl -fsSL https://raw.githubusercontent.com/你的用户名/你的仓库名/main/deploy/server_check.sh -o /tmp/server_check.sh
bash /tmp/server_check.sh
```

如果代码还没发布到 GitHub，可以先把 `deploy/server_check.sh` 文件内容复制到服务器，再运行：

```bash
bash server_check.sh
```

把输出贴回来，我就能判断：

- Python 是否够用
- pip 是否能安装依赖
- git 是否可用
- systemd 或 cron 是否可用
- 服务器能不能访问数据源
- 是否适合直接部署

