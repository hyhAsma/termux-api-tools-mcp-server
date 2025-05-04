# Termux-API-Tools-MCP-Server 项目说明

## 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [工作逻辑](#工作逻辑)
- [如何使用](#如何使用)
- [测试截图](#测试截图)
- [已知问题](#已知问题)
- [免责声明](#免责声明)
- [未来计划](#未来计划)

## 项目概述

本项目是一个基于 Termux-API 的新人练手项目，主要用于通过 MCP 客户端操控 Android 设备。它提供了部分敏感操作功能，包括获取手机信息和执行电话/短信相关操作。

> **注意**：本项目涉及敏感功能，使用时请谨慎，建议敏感信息处理尽量使用本地 LLM。

## 功能特性

- 获取手机相关信息（部分功能可能涉及敏感数据）
- 获取通话记录、获取短信记录等功能（敏感操作）
- 拨打电话、发送短信等功能（敏感操作）
- 通过 MCP 客户端进行远程控制

## 工作逻辑

项目采用以下工作逻辑：

1. Android 设备（Termux 环境）与 MCP 客户端处于同一局域网；
2. Termux开启SSHD，并配置远程登陆；
3. termux-api-tools-mcp-server.py可以链接的到Termux；
4. 通过MCP客户端 JSON 配置建立连接：

```json 
{
    "termux-api-mcp-tools": {
      "name": "termux-api-mcp-tools",
      "type": "stdio",
      "isActive": true,
      "tags": [
        "termux",
        "android",
        "mobile"
      ],
      "command": "python.exe",
      "args": [
        "D:\\test\\termux-api-mcp\\termux-api-tools-mcp-server.py"
      ],
      "env": {
        "TERMUX_SSH_HOST": "192.168.x.xx",
        "TERMUX_SSH_PORT": "xxxx",
        "TERMUX_SSH_USER": "username",
        "TERMUX_SSH_PASSWORD": "password"
      }
    }
}
```

## 如何使用

1. 将上述JSON导入cherry studio或claude等MCP客户端；
2. 修改其termux-api-tools-mcp-server.py位置为自己本地文件位置
3. pip install 相关包
4. 填写env相关信息（前提是termux开启sshd，termux-api-tools-mcp-server.py可以通过网络请求的到termux）

## 测试截图
<img src="https://github.com/hyhAsma/termux-api-tools-mcp-server/blob/main/showImgs/img1.png" width="510px">

<img src="https://github.com/hyhAsma/termux-api-tools-mcp-server/blob/main/showImgs/img2.png" width="510px">

<img src="https://github.com/hyhAsma/termux-api-tools-mcp-server/blob/main/showImgs/img3.jpg" width="510px">

## 已知问题

- 获取设备上所有无线电模块 (`termux-telephony-cellinfo`) 有点问题
- cherry stduio调用电话`cell`功能存在异常
- 其他偶发的调用失败情况（可能是手机兼容性问题）
- 还有几个不常用的API未通过本地测试故没有添加进项目

## 免责声明

本项目为学习练习用途，开发者对使用本项目可能造成的任何后果不承担责任。涉及敏感操作的功能请谨慎使用，并遵守当地法律法规。

## 未来计划

- 完善代码异常处理
- ~~增加更多设备控制功能~~如需更多Android信息可以参考ADB-MCP-Server
- 提高代码质量和安全性

新人练手项目，请多包涵！联系作者：B站[@忘月沁](https://space.bilibili.com/46507166)
