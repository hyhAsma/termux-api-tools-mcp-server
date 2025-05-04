# Termux-API-Tools-MCP-Server 项目说明

## 项目概述

本项目是一个基于 Termux-API 的新人练手项目，主要用于通过 MCP 客户端操控 Android 设备。它提供了部分敏感操作功能，包括获取手机信息和执行电话/短信相关操作。

> **注意**：本项目涉及敏感功能，使用时请谨慎，建议敏感信息处理尽量使用本地 LLM。

## 功能特性

- 获取手机相关信息（部分功能可能涉及敏感数据）
- 拨打电话、发送短信等功能（敏感操作）
- 通过 MCP 客户端进行远程控制

## 技术架构

项目采用以下工作逻辑：

1. Android 设备（Termux 环境）与 MCP 客户端处于同一局域网
2. 通过MCP客户端 JSON 配置建立连接：

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


## 已知问题

- 电话功能模块 (`termux-telephony-x`) 目前仅 `cell` 电话功能测试通过
- 其他电话相关功能可能存在异常（可能是手机兼容性问题）

## 免责声明

本项目为学习练习用途，开发者对使用本项目可能造成的任何后果不承担责任。涉及敏感操作的功能请谨慎使用，并遵守当地法律法规。

## 未来计划

- 完善代码异常处理
- ~~增加更多设备控制功能~~如需更多Android信息可以参考ADB-MCP-Server
- 提高代码质量和安全性

欢迎各位前辈指正代码中的问题，新人练手项目，请多包涵！
