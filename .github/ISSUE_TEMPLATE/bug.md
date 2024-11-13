name: Bug Report 错误报告
description: Report a bug to help us improve 报告错误以帮助我们改进
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        感谢您花时间填写这份错误报告！
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: what-happened
    attributes:
      label: 发生了什么？ What happened?
      description: 请详细描述您遇到的问题 Please describe the bug in detail
      placeholder: |
        例如：当我...时，出现了...错误
        Example: When I... the error... occurred
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤 Steps to reproduce
      description: 请告诉我们如何复现这个问题 Please tell us how to reproduce this issue
      placeholder: |
        1. 打开软件...
        2. 点击...
        3. 出现错误...
    validations:
      required: true

  - type: dropdown
    id: version
    attributes:
      label: 版本 Version
      description: 您正在使用的软件版本是？ What version are you running?
      options:
        - v1.0.0
        - v0.9.0
        - v0.8.0
        - Other (请在下方说明 Please specify below)
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统 Operating System
      options:
        - Windows
        - macOS
        - Linux
    validations:
      required: true

  - type: textarea
    id: additional
    attributes:
      label: 补充信息 Additional information
      description: |
        添加任何其他有关问题的信息（截图、日志等）
        Add any other context about the problem here (screenshots, logs, etc.)
