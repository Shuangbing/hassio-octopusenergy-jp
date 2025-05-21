# Octopus Energy Japan for Home Assistant

这个Home Assistant集成可以从Octopus Energy Japan获取您的电力使用数据（千瓦时和费用）。

## 功能

- 显示前一天的电力使用量（千瓦时）
- 显示前一天的电力费用（日元）
- 允许配置更新频率

## 安装

### 手动安装

1. 将 `custom_components/octopusenergy_jp` 文件夹复制到您的 Home Assistant 配置目录下的 `custom_components` 文件夹中。
   如果 `custom_components` 文件夹不存在，请先创建它。

2. 重启 Home Assistant。

### HACS安装（推荐）

1. 确保您已经安装了 [HACS](https://hacs.xyz/).
2. 在HACS中，点击"集成"。
3. 点击右上角的"+"图标。
4. 搜索 "Octopus Energy Japan"。
5. 点击搜索结果，并选择"安装"。
6. 重启 Home Assistant。

## 配置

1. 在 Home Assistant 的 "配置 > 设备与服务" 中，点击"添加集成"。
2. 搜索 "Octopus Energy Japan"。
3. 填写以下信息：
   - 电子邮件：您的 Octopus Energy Japan 账户电子邮件
   - 密码：您的 Octopus Energy Japan 账户密码
   - 账号：您的 Octopus Energy Japan 账号（格式为 A-XXXXXXXX）
   - 数据更新频率：数据更新的时间间隔（小时），默认为3小时

## 注意事项

- 此集成仅获取前一天的电力使用数据，因为 API 仅提供这些数据。
- 数据每次更新时会查询前一天的全天数据。
- API 返回的时间是 UTC 时间，集成会适当处理时区问题。

## 故障排除

如果您遇到问题：

1. 确保您的登录凭据正确。
2. 确保您输入的账号格式正确。
3. 检查 Home Assistant 日志中是否有错误信息。

## 贡献与支持

如果您想贡献代码或报告问题，请访问 [GitHub 仓库](https://github.com/shuangbing/hassio-octopusenergy-jp)。

## 免责声明

此集成不是由 Octopus Energy Japan 官方开发的。它使用 Octopus Energy Japan 提供的公开 API 访问您的账户数据。 