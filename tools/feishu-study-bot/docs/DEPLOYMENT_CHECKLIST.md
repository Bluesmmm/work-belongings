# 飞书学习机器人 - 部署检查清单

## 本地测试阶段

- [ ] 服务已启动：`curl http://localhost:8000/health`
- [ ] 数据已导入：`curl http://localhost:8000/api/stats`
- [ ] 飞书应用已创建（open.feishu.cn/app）
- [ ] 已获取 APP_ID 和 APP_SECRET
- [ ] 已安装 ngrok 或其他内网穿透工具
- [ ] 本地回调地址已配置到飞书后台
- [ ] 飞书群聊已创建，机器人已加入
- [ ] 已获取群聊 ID（通过日志或 API）

## 远程部署阶段

### 服务器准备
- [ ] 服务器 SSH 连接正常
- [ ] Python 3.10+ 已安装
- [ ] 已创建 www-data 用户（或其他运行用户）
- [ ] 防火墙已开放 8000 端口（或使用反向代理）

### 代码部署
- [ ] 代码已上传到服务器 `/opt/feishu-study-bot`
- [ ] systemd 服务文件已安装到 `/etc/systemd/system/`
- [ ] .env 文件已配置（包含真实的飞书凭证）
- [ ] 数据库路径正确（生产环境建议用 PostgreSQL）

### 飞书配置
- [ ] 飞书事件订阅已更新为服务器地址
- [ ] 卡片回调地址已更新
- [ ] DEFAULT_CHAT_ID 已设置为正确的群聊 ID
- [ ] 飞书应用已发布版本

### 服务启动
- [ ] `systemctl start feishu-bot` 执行成功
- [ ] `systemctl enable feishu-bot` 已设置开机自启
- [ ] `systemctl status feishu-bot` 显示 running
- [ ] 服务日志无错误：`journalctl -u feishu-bot -f`

### 功能测试
- [ ] 健康检查正常：`curl http://server-ip:8000/health`
- [ ] 统计接口正常：`curl http://server-ip:8000/api/stats`
- [ ] 飞书群内发送 `/今日` 有响应
- [ ] 发送 `/打卡` 能显示表单
- [ ] 打卡提交成功
- [ ] 定时提醒正常发送（等待到设定时间测试）

### 生产优化（可选）
- [ ] 配置 Nginx 反向代理
- [ ] 配置 SSL 证书（Let's Encrypt）
- [ ] 切换到 PostgreSQL 数据库
- [ ] 配置日志轮转
- [ ] 设置监控告警

## 常见问题排查

| 问题 | 排查方法 |
|------|----------|
| 服务启动失败 | `journalctl -u feishu-bot -n 50` |
| 飞书无响应 | 检查事件订阅 URL 是否正确 |
| 定时任务不触发 | 检查 DEFAULT_CHAT_ID 是否配置 |
| 数据库错误 | 检查 DATABASE_URL 路径权限 |
| 端口被占用 | `netstat -tlnp \| grep 8000` |

## 回滚步骤

如果部署出现问题需要回滚：

```bash
# 停止服务
sudo systemctl stop feishu-bot

# 恢复之前的版本
cd /opt/feishu-study-bot
git pull origin main  # 或恢复备份
git checkout <previous-commit>

# 重启服务
sudo systemctl start feishu-bot
```
